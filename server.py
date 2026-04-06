"""WeChat MCP Server - wxauto4ベースのWeChat 4.x対応MCPサーバー"""

import ctypes
import ctypes.wintypes
import sys


def _detect_wechat_window_name():
    """WeChatメインウィンドウの実際のタイトルを検出する。

    WeChat 4.0.5以前は「微信」、最新版は「WeChat」にウィンドウ名が変更されている。
    ウィンドウクラス名で検索し、実際のタイトルを返す。
    """
    FindWindowEx = ctypes.windll.user32.FindWindowExW
    FindWindowEx.argtypes = [
        ctypes.wintypes.HWND, ctypes.wintypes.HWND,
        ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR,
    ]
    FindWindowEx.restype = ctypes.wintypes.HWND

    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowText.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]

    known_titles = ("微信", "WeChat", "wechat")
    known_classes = ("Qt51514QWindowIcon",)

    for cls in known_classes:
        prev = None
        while True:
            prev = FindWindowEx(None, prev, cls, None)
            if not prev:
                break
            buf = ctypes.create_unicode_buffer(256)
            GetWindowText(prev, buf, 256)
            if buf.value in known_titles:
                return buf.value

    return None


def _patch_wxauto4_for_wechat_name(detected_name):
    """wxauto4のUIコントロール検索をパッチし、最新版WeChatに対応する。

    最新版WeChatでは以下の変更がある:
    1. UIラベルが中国語→英語に変更（「微信」→「WeChat」、「搜索」→「Search」）
    2. SearchContentPopover がトップレベルウィンドウからメインウィンドウの子要素に変更
    """
    from wxauto4 import uia
    from wxauto4.ui.main import WeChatMainWnd

    WeChatMainWnd._ui_name = detected_name

    # 最新版WeChatでは中国語UIラベルが英語に変更されている
    name_replacements = {
        "微信": detected_name,
        "搜索": "Search",
    }

    # UIAutomation コントロールの検索で中国語名を英語名に置換
    for ctrl_type in (uia.ButtonControl, uia.EditControl):
        _orig_init = ctrl_type.__init__

        def _make_patched(orig, replacements=name_replacements):
            def _patched(self, *args, **kwargs):
                name = kwargs.get("Name")
                if name in replacements:
                    kwargs["Name"] = replacements[name]
                return orig(self, *args, **kwargs)
            return _patched

        ctrl_type.__init__ = _make_patched(_orig_init)

    # WindowControl: 名前置換 + SearchContentPopover の検索スコープ修正
    _orig_window_init = uia.WindowControl.__init__

    def _patched_window_init(self, *args, **kwargs):
        name = kwargs.get("Name")
        if name in name_replacements:
            kwargs["Name"] = name_replacements[name]
        # SearchContentPopover は最新版では メインウィンドウの子要素になっている
        # デフォルト（デスクトップから検索）だと見つからないので、メインウィンドウから検索する
        cls = kwargs.get("ClassName", "")
        if cls == "mmui::SearchContentPopover" and kwargs.get("searchFromControl") is None:
            main_wnd = uia.WindowControl(
                ClassName="mmui::MainWindow", Name=detected_name
            )
            if main_wnd.Exists(2):
                kwargs["searchFromControl"] = main_wnd
        return _orig_window_init(self, *args, **kwargs)

    uia.WindowControl.__init__ = _patched_window_init


# ウィンドウ名を自動検出し、「微信」以外なら wxauto4 をパッチ
_detected = _detect_wechat_window_name()
if _detected and _detected != "微信":
    _patch_wxauto4_for_wechat_name(_detected)
    print(f"[wechat-mcp] Patched wxauto4 for window name: {_detected}", file=sys.stderr)


import re

from fastmcp import FastMCP
from wxauto4 import WeChat

mcp = FastMCP("wechat")
wx = WeChat(ads=False)

# WeChat セッション一覧の control.Name 末尾に付く時刻表示を除去するパターン
_TIME_RE = re.compile(
    r"\s+"
    r"(?:"
    r"(?:昨天|前天|星期[一二三四五六日天])\s+\d{1,2}:\d{2}"
    r"|\d{1,2}:\d{2}"
    r"|\d{1,2}月\d{1,2}日"
    r"|\d{4}年\d{1,2}月\d{1,2}日"
    r")"
    r"\s*$"
)


def _get_sessions_with_display():
    """セッション一覧を (表示テキスト, SessionElement) のペアで返す。"""
    sessions = wx.GetSession()
    result = []
    for s in sessions:
        full = (s.control.Name or "").rstrip()
        stripped = _TIME_RE.sub("", full).rstrip()
        if stripped:
            result.append((stripped, s))
    return result


def _open_chat(contact: str) -> str:
    """あいまいな名前でチャットを開く。

    まずサイドバーのセッション一覧を部分一致で検索し、
    見つかればそのセッションを直接クリックして開く。
    見つからなければ ChatWith（WeChat検索）にフォールバック。
    返り値はマッチした表示テキスト（またはクエリそのもの）。
    """
    pairs = _get_sessions_with_display()
    query_lower = contact.lower()

    # 完全一致（表示テキスト先頭部分）
    for display, session in pairs:
        if display.lower() == query_lower:
            session.control.Click()
            return display

    # 部分一致（クエリが表示テキストに含まれる）
    for display, session in pairs:
        if query_lower in display.lower():
            session.control.Click()
            return display

    # セッション一覧に見つからない場合は WeChat 検索にフォールバック
    wx.ChatWith(contact)
    return contact


@mcp.tool()
def list_chats() -> str:
    """現在のチャット一覧（サイドバーに表示中のチャット）を取得する。

    連絡先名と最新メッセージのプレビューが表示されます。
    get_messages や send_message の contact には、ここに表示される名前の一部を指定すればOKです。
    """
    pairs = _get_sessions_with_display()
    if not pairs:
        return "チャット一覧を取得できませんでした"
    return "\n".join(display for display, _ in pairs)


@mcp.tool()
def get_messages(contact: str) -> str:
    """指定した連絡先のチャットを開き、表示されているメッセージを全て取得する。

    Args:
        contact: 連絡先の名前（部分一致・あいまい入力OK）
    """
    resolved = _open_chat(contact)
    messages = wx.GetAllMessage()
    if not messages:
        return f"{resolved} のメッセージはありません"
    result = []
    for msg in messages:
        sender = getattr(msg, "sender", "")
        content = getattr(msg, "content", str(msg))
        result.append(f"[{sender}] {content}")
    return "\n".join(result)


@mcp.tool()
def send_message(contact: str, message: str) -> str:
    """指定した連絡先にテキストメッセージを送信する。

    Args:
        contact: 送信先の連絡先名（部分一致・あいまい入力OK）
        message: 送信するメッセージ内容
    """
    resolved = _open_chat(contact)
    wx.SendMsg(message)
    return f"{resolved} にメッセージを送信しました: {message}"


@mcp.tool()
def send_file(contact: str, filepath: str) -> str:
    """指定した連絡先にファイルを送信する。

    Args:
        contact: 送信先の連絡先名（部分一致・あいまい入力OK）
        filepath: 送信するファイルのパス
    """
    resolved = _open_chat(contact)
    wx.SendFiles(filepath)
    return f"{resolved} にファイルを送信しました: {filepath}"


if __name__ == "__main__":
    mcp.run()

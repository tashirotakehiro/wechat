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

    wxauto4はUIAutomationのコントロール名として「微信」をハードコードしている。
    最新版WeChatでは「WeChat」に変更されているため、コントロール検索時に名前を置換する。
    """
    from wxauto4 import uia
    from wxauto4.ui.main import WeChatMainWnd

    WeChatMainWnd._ui_name = detected_name

    # UIAutomation コントロールの検索で Name='微信' を検出名に置換
    for ctrl_type in (uia.ButtonControl, uia.WindowControl, uia.EditControl):
        _orig_init = ctrl_type.__init__

        def _make_patched(orig, name=detected_name):
            def _patched(self, *args, **kwargs):
                if kwargs.get("Name") == "微信":
                    kwargs["Name"] = name
                return orig(self, *args, **kwargs)
            return _patched

        ctrl_type.__init__ = _make_patched(_orig_init)


# ウィンドウ名を自動検出し、「微信」以外なら wxauto4 をパッチ
_detected = _detect_wechat_window_name()
if _detected and _detected != "微信":
    _patch_wxauto4_for_wechat_name(_detected)
    print(f"[wechat-mcp] Patched wxauto4 for window name: {_detected}", file=sys.stderr)


from fastmcp import FastMCP
from wxauto4 import WeChat

mcp = FastMCP("wechat")
wx = WeChat(ads=False)


@mcp.tool()
def get_messages(contact: str) -> str:
    """指定した連絡先のチャットを開き、表示されているメッセージを全て取得する。

    Args:
        contact: 連絡先の名前（WeChat表示名）
    """
    wx.ChatWith(contact)
    messages = wx.GetAllMessage()
    if not messages:
        return f"{contact} のメッセージはありません"
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
        contact: 送信先の連絡先名（WeChat表示名）
        message: 送信するメッセージ内容
    """
    wx.SendMsg(message, contact)
    return f"{contact} にメッセージを送信しました: {message}"


@mcp.tool()
def send_file(contact: str, filepath: str) -> str:
    """指定した連絡先にファイルを送信する。

    Args:
        contact: 送信先の連絡先名（WeChat表示名）
        filepath: 送信するファイルのパス
    """
    wx.SendFiles(filepath, contact)
    return f"{contact} にファイルを送信しました: {filepath}"


if __name__ == "__main__":
    mcp.run()

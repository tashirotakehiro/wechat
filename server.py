"""WeChat MCP Server - wxauto4ベースのWeChat 4.x対応MCPサーバー"""

import ctypes
import ctypes.wintypes

from wxauto4.ui.main import WeChatMainWnd


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

    GetClassName = ctypes.windll.user32.GetClassNameW
    GetClassName.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]

    # wxauto4 が使うウィンドウクラス名
    target_cls = WeChatMainWnd._win_cls_name

    hwnd = None
    prev = None
    while True:
        prev = FindWindowEx(None, prev, target_cls, None)
        if not prev:
            break
        buf = ctypes.create_unicode_buffer(256)
        GetWindowText(prev, buf, 256)
        title = buf.value
        if title in ("微信", "WeChat", "wechat"):
            return title

    return None


# ウィンドウ名を自動検出し、wxauto4 のハードコード値を上書き
detected_name = _detect_wechat_window_name()
if detected_name and detected_name != WeChatMainWnd._ui_name:
    WeChatMainWnd._ui_name = detected_name


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

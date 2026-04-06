"""WeChat MCP Server - wxauto4ベースのWeChat 4.x対応MCPサーバー"""

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

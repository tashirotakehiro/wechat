# WeChat ↔ Slack ブリッジ

WeChatに届くメッセージをClaude Codeが日本語に翻訳してSlackに転送し、Slackでの返信を中国語に翻訳してWeChatで送信するブリッジシステムです。

## 前提条件

- Windows PC（WeChatとClaude Codeが同一マシン上で動作）
- WeChat for Windows 4.x インストール済み・ログイン済み
- Python 3.12（wxauto4が3.13未対応のため）
- Claude Code インストール済み
- Slack MCP 接続済み

## セットアップ手順

### 1. 依存パッケージのインストール

```powershell
py -3.12 -m pip install wxauto4 fastmcp
```

### 2. WeChat にログイン

WeChat for Windows を起動し、ログイン状態であることを確認。

### 3. 動作確認

WeChat が起動した状態で：

```powershell
py -3.12 -c "from wxauto4 import WeChat; print('OK')"
```

`OK` と表示されれば準備完了。

### 4. MCP サーバーの起動確認

Claude Code を再起動すると `.mcp.json` が読み込まれ、自動的に `server.py` が起動されます。
`/mcp` コマンドで `wechat` サーバーが認識されているか確認してください。

### 5. テスト

Claude に以下を試してください：
- 「WeChatの〇〇さんのメッセージを取得して」
- 「WeChatで〇〇さんに你好と送って」

### 6. 自動ポーリング開始

```
/loop 5m WeChat新着メッセージをチェックし、日本語に翻訳してSlackの対応チャンネルに投稿。Slackの wechat-* チャンネルの新着返信を中国語に翻訳してWeChatで返信。
```

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `server.py` | wxauto4ベースのWeChat MCPサーバー |
| `requirements.txt` | Python依存パッケージ |
| `.mcp.json` | Claude Code MCP設定 |
| `CLAUDE.md` | Claudeへのブリッジ動作指示 |

## 利用可能なツール

| ツール | 説明 |
|-------|------|
| `get_messages` | 指定連絡先のチャットを開き、表示中のメッセージを取得 |
| `send_message` | 指定連絡先にテキストメッセージを送信 |
| `send_file` | 指定連絡先にファイルを送信 |

## トラブルシューティング

- **wxauto4 インストール失敗**: Python 3.12を使用しているか確認（`py -3.12 --version`）
- **WeChat認識エラー**: WeChatが起動・ログイン済みか確認
- **GUI干渉**: サーバー動作中はWeChatウィンドウを手動操作しない

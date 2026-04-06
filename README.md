# WeChat ↔ Slack ブリッジ

WeChatに届くメッセージをClaude Codeが日本語に翻訳してSlackに転送し、Slackでの返信を中国語に翻訳してWeChatで送信するブリッジシステムです。

## 前提条件

- Windows PC（WeChatとClaude Codeが同一マシン上で動作）
- WeChat for Windows インストール済み・ログイン済み
- Python >= 3.11
- Claude Code インストール済み
- Slack MCP が既に接続済みであること

## セットアップ手順

### 1. mcp_server_wechat のインストール

Windows のターミナル（PowerShell / CMD）で実行:

```powershell
pip install mcp_server_wechat
```

### 2. ファイル保存用フォルダの作成

```powershell
mkdir C:\wechat_files
```

### 3. WeChat にログイン

WeChat for Windows を起動し、ログイン状態であることを確認。

### 4. SSEサーバーの起動

```powershell
python -m mcp_server_wechat_sse --folder-path=C:\wechat_files
```

`http://localhost:3000/sse` で起動すれば成功。このターミナルは閉じないこと。

> **注意**: サーバー稼働中はWeChatウィンドウを手動で操作しないでください（GUI自動操作が干渉します）。

### 5. 動作確認

1. Claude Code を再起動（またはセッション再開）
2. `/mcp` コマンドで `wechat` サーバーが認識されているか確認
3. テスト: 「WeChatの〇〇さんの今日のチャット履歴を取得して」

### 6. 自動ポーリング開始

Claude Code で以下を実行:

```
/loop 5m WeChat新着メッセージをチェックし、日本語に翻訳してSlackの対応チャンネルに投稿。Slackの wechat-* チャンネルの新着返信を中国語に翻訳してWeChatで返信。
```

## 構成

- `.mcp.json` — WeChat MCPサーバー設定（SSE接続）
- `CLAUDE.md` — Claudeへのブリッジ動作指示（翻訳ルール、チャンネル命名規則等）
- Slack — 既存のSlack MCPサーバー経由で操作

## トラブルシューティング

- **WeChat MCP接続エラー**: `python -m mcp_server_wechat_sse` が起動しているか確認
- **翻訳精度**: Claudeに追加の翻訳指示を与えることで調整可能
- **WeChatウィンドウ干渉**: サーバー動作中はWeChatウィンドウを手動操作しない

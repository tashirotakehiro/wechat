# WeChat ↔ Slack ブリッジ

WeChatに届くメッセージをClaude Codeが日本語に翻訳してSlackに転送し、Slackでの返信を中国語に翻訳してWeChatで送信するブリッジシステムです。

## 前提条件

- Windows PC（WeChatとClaude Codeが同一マシン上で動作）
- WeChat for Windows インストール済み・ログイン済み
- Python >= 3.11
- Node.js >= 18（npx用）
- Claude Code インストール済み
- Slackワークスペースの管理者権限

## セットアップ手順

### 1. WeChat MCP サーバー（mcp_server_wechat）

Windows のターミナル（PowerShell / CMD）で実行:

```powershell
# インストール
pip install mcp_server_wechat

# ファイル保存用ディレクトリ作成
mkdir C:\wechat_files

# SSEサーバー起動
python -m mcp_server_wechat_sse --folder-path=C:\wechat_files
```

サーバーが `http://localhost:3000/sse` で起動します。

> **注意**: サーバー稼働中はWeChatウィンドウを手動で操作しないでください（GUI自動操作が干渉します）。

### 2. Slack Bot の作成

1. [Slack API](https://api.slack.com/apps) にアクセス
2. **Create New App** → **From scratch** を選択
3. アプリ名（例: `WeChat Bridge`）とワークスペースを設定
4. 左メニュー **OAuth & Permissions** に移動
5. **Bot Token Scopes** に以下を追加:
   - `channels:history` — チャンネルメッセージの読み取り
   - `channels:read` — チャンネル情報の取得
   - `channels:manage` — チャンネルの作成・管理
   - `chat:write` — メッセージの送信
   - `users:read` — ユーザー情報の取得
6. **Install to Workspace** をクリックして承認
7. 表示される **Bot User OAuth Token**（`xoxb-` で始まる）をコピー
8. **Team ID** の確認: Slackをブラウザで開き、URLの `https://app.slack.com/client/T01234567/...` の `T` で始まる部分

### 3. `.mcp.json` にトークンを設定

`.mcp.json` ファイルのプレースホルダーを実際の値に置換:

```json
{
  "mcpServers": {
    "wechat": {
      "type": "sse",
      "url": "http://localhost:3000/sse"
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-actual-token",
        "SLACK_TEAM_ID": "T01234567"
      }
    }
  }
}
```

> **セキュリティ注意**: 実際のトークンを入れた `.mcp.json` はGitにコミットしないでください。

### 4. 動作確認

1. WeChat SSEサーバーが起動していることを確認
2. Claude Code を再起動（またはセッション再開）
3. `/mcp` コマンドで `wechat` と `slack` の両サーバーが認識されているか確認
4. テスト:
   - 「WeChatの〇〇さんの今日のチャット履歴を取得して」
   - 「Slackの #wechat-test チャンネルにテストメッセージを投稿して」

### 5. 自動ポーリング開始

Claude Code で以下を実行:

```
/loop 5m WeChat新着メッセージをチェックし、日本語に翻訳してSlackの対応チャンネルに投稿。Slackの wechat-* チャンネルの新着返信を中国語に翻訳してWeChatで返信。
```

## 利用可能なツール

### WeChat（mcp_server_wechat）
| ツール | 説明 |
|-------|------|
| チャット履歴取得 | 指定連絡先の指定日のメッセージを取得（日付形式: `YY/M/D`） |
| メッセージ送信 | 指定連絡先にメッセージを送信 |
| バッチ送信 | 1つの連絡先に複数メッセージを送信 |
| 一斉送信 | 複数の連絡先にメッセージを送信 |

### Slack（@modelcontextprotocol/server-slack）
| ツール | 説明 |
|-------|------|
| チャンネル一覧 | ワークスペースのチャンネルを一覧表示 |
| メッセージ投稿 | チャンネルにメッセージを投稿 |
| スレッド返信 | スレッドに返信 |
| リアクション追加 | メッセージにリアクションを追加 |
| 履歴取得 | チャンネルの直近メッセージを取得 |
| ユーザー一覧 | ワークスペースのユーザーを一覧表示 |

## トラブルシューティング

- **WeChat MCP接続エラー**: `python -m mcp_server_wechat_sse` が起動しているか確認
- **Slack認証エラー**: Bot Token / Team ID が正しいか確認。Botがチャンネルに招待されているか確認
- **翻訳精度**: Claudeに追加の翻訳指示を与えることで調整可能

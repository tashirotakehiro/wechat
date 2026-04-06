# WeChat MCP サーバー 動作ルール

## 概要
このプロジェクトはClaude CodeからWeChatを操作するためのMCPサーバーです。
Claude CodeがMCPサーバー経由でWeChatのメッセージ取得・送信を行います。

## 構成
- **WeChat側**: wxauto4ベースのカスタムMCPサーバー（server.py）をWindows上で起動

## MCP ツール

### WeChat（server.py）
| ツール | 説明 |
|-------|------|
| `get_messages` | 指定連絡先のチャットを開き、表示中のメッセージを取得 |
| `send_message` | 指定連絡先にテキストメッセージを送信 |
| `send_file` | 指定連絡先にファイルを送信 |

## 注意事項

- WeChat操作中はWeChatウィンドウに手動で触れないこと（GUI自動操作のため）
- Python 3.12 + wxauto4 を使用（3.13では wxauto4 が未対応）
- WeChat 4.x に対応（server.py がウィンドウ名「微信」/「WeChat」を自動検出）

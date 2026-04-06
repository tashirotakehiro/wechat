"""MCP stdio wrapper - server.pyのstdoutからJSON-RPCメッセージだけを通過させる。

wxauto4の.pydバイナリがCレベルでstdoutに直接書き込む初期化メッセージ
（例: "初始化成功，获取到已登录窗口：..."）をフィルタリングし、
MCPプロトコル（JSON-RPC）のみをクライアントに転送する。
"""

import subprocess
import sys
import threading
import os

SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
PYTHON = sys.executable


def forward_stdin(proc):
    """クライアントのstdinをサーバープロセスに転送する"""
    try:
        while True:
            data = sys.stdin.buffer.read(4096)
            if not data:
                break
            proc.stdin.write(data)
            proc.stdin.flush()
    except (BrokenPipeError, OSError):
        pass


def filter_stdout(proc):
    """サーバーのstdoutからJSON-RPCメッセージだけを通過させる"""
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            # JSON-RPCメッセージは { で始まる行のみ
            # Content-Length ヘッダーもそのまま通す（MCPのHTTP-likeフレーミング）
            stripped = line.lstrip()
            if stripped.startswith(b"{") or stripped.startswith(b"Content-Length"):
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
            else:
                # 非JSONメッセージはstderrに転送（デバッグ用）
                sys.stderr.buffer.write(line)
                sys.stderr.buffer.flush()
    except (BrokenPipeError, OSError):
        pass


def forward_stderr(proc):
    """サーバーのstderrをそのまま転送する"""
    try:
        while True:
            data = proc.stderr.read(4096)
            if not data:
                break
            sys.stderr.buffer.write(data)
            sys.stderr.buffer.flush()
    except (BrokenPipeError, OSError):
        pass


def main():
    proc = subprocess.Popen(
        [PYTHON, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdin_thread = threading.Thread(target=forward_stdin, args=(proc,), daemon=True)
    stdout_thread = threading.Thread(target=filter_stdout, args=(proc,), daemon=True)
    stderr_thread = threading.Thread(target=forward_stderr, args=(proc,), daemon=True)

    stdin_thread.start()
    stdout_thread.start()
    stderr_thread.start()

    proc.wait()
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()

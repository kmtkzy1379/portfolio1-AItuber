import subprocess
import os
import sys
import time

def main():
    """
    AIアシスタント本体とLive2D連携スクリプトを同時に起動します。
    片方のプロセスが終了したら、もう片方も自動的に終了させます。
    """
    # プロジェクトのルートディレクトリを特定します
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   
    # AIアシスタント本体を起動します
    ai_process = subprocess.Popen([sys.executable, "app/main_app.py"], cwd=project_root)

    # Live2D連携スクリプトを起動します
    live2d_process = subprocess.Popen([sys.executable, "app/random_move.py"], cwd=project_root)

    processes = [ai_process, live2d_process]

    # プロセスが両方とも実行中である限りループします
    while all(p.poll() is None for p in processes):
        time.sleep(0.5)  # CPU負荷を下げるために少し待機します

    print("\nどちらかのプロセスが終了しました。残りのプロセスを終了します...")

    # ループを抜けた後、まだ実行中のプロセスがあれば正常終了を試みます
    if live2d_process.poll() is None:
        print("Live2D連携スクリプトを終了させています...")
        live2d_process.terminate()  # SIGTERMを送信

    if ai_process.poll() is None:
        print("AIアシスタントプロセスを終了させています...")
        ai_process.terminate()  # SIGTERMを送信

    # サブプロセスが終了するのを待ちます
    try:
        ai_process.wait(timeout=10)
        live2d_process.wait(timeout=5)
        print("全てのサブプロセスが終了しました。")
    except subprocess.TimeoutExpired:
        print("サブプロセスの終了待機がタイムアウトしました。強制終了します。")
        ai_process.kill()
        live2d_process.kill()

    print("アプリケーションを終了します。")

if __name__ == "__main__":
    main()

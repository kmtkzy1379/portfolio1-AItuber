import subprocess
import os
import sys

def main():
    """
    AIアシスタント本体とLive2D連携スクリプトを同時に起動します。
    どちらかのプロセスが終了するまで待機します。
    """
    # プロジェクトのルートディレクトリに移動します
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # AIアシスタント本体を起動します
    ai_process = subprocess.Popen([sys.executable, "app/main_app.py"], cwd=os.getcwd())

    # Live2D連携スクリプトを起動します
    live2d_process = subprocess.Popen([sys.executable, "app/random_move.py"], cwd=os.getcwd())

    # どちらかのプロセスが終了するまで待機します
    ai_process.wait()
    live2d_process.wait()

if __name__ == "__main__":
    main()
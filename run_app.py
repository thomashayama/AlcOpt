import os
import subprocess

def main():
    app_path = os.path.join(os.path.dirname(__file__), 'alcopt', 'app', 'Home.py')
    subprocess.run(["streamlit", "run", app_path])

if __name__ == "__main__":
    main()

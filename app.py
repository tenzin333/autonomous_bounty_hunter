from flask import Flask
import threading
import time
import subprocess
import os

app = Flask(__name__)

def run_bot():
    """Runs your bounty hunter logic in the background."""
    while True:
        print("Bot is hunting...")
        subprocess.run(["python", "main.py"])
        time.sleep(3600)  # Run once per hour

@app.route('/')
def health_check():
    return "Bounty Hunter is Active!", 200

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask
import threading
import time
import subprocess
import os

app = Flask(__name__)

def run_bot():
    """This function runs your actual bounty hunter logic in the background."""
    while True:
        print("Bot is hunting...")
        # Replace this with your actual script execution
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        subprocess.run(["python", "main.py"]) 
        time.sleep(3600) # Run once per hour

@app.route('/')
def health_check():
    return "Bounty Hunter is Active!", 200

if __name__ == "__main__":
    # Start the bot logic in a separate thread so the web server can stay live
    threading.Thread(target=run_bot, daemon=True).start()
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
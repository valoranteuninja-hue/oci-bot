from flask import Flask
import threading
import os
import subprocess

app = Flask(__name__)

def run_oci_bot():
    print("Starting Oracle Auto-Retry bot in the background...")
    subprocess.run(["python", "oracle-arm-retry.py"])

@app.route('/')
def home():
    return "Oracle ARM bot is running in the background! (Please set up a free cron-job.org ping to keep this page awake 24/7)"

if __name__ == '__main__':
    # Start the infinite retry script in a background thread
    bot_thread = threading.Thread(target=run_oci_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Render requires a web server binding to the $PORT env variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

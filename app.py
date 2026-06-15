from flask import Flask
import threading
import os
import subprocess
import time

app = Flask(__name__)
# Keep the last 50 lines of logs in memory
bot_logs = []

import sys

def run_oci_bot():
    global bot_logs
    bot_logs.append("Starting Oracle Auto-Retry bot in the background...")
    
    try:
        # Use sys.executable to ensure we use the exact same Python binary Render/Gunicorn is using
        process = subprocess.Popen(
            [sys.executable, "-u", "oracle-arm-retry.py"],  # -u for unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            stripped_line = line.strip()
            if stripped_line:
                print(f"[BOT] {stripped_line}")  # Prints to Render's Logs tab
                bot_logs.append(stripped_line)
                if len(bot_logs) > 50:
                    bot_logs.pop(0)
    except Exception as e:
        error_msg = f"CRITICAL ERROR: Failed to start the bot. Reason: {str(e)}"
        print(error_msg)
        bot_logs.append(error_msg)

@app.route('/')
def home():
    header = "<h2>Oracle ARM Auto-Provisioner Status</h2>"
    header += "<p>This page automatically refreshes every 10 seconds. (Required for Render to stay awake)</p><hr>"
    
    # Format logs with monospace font
    logs_html = "<pre style='background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; height: 400px; overflow-y: scroll;'>"
    logs_html += "<br>".join(bot_logs)
    logs_html += "</pre>"
    
    # Auto-refresh meta tag
    html = f"<html><head><meta http-equiv='refresh' content='10'></head><body style='font-family: Arial; padding: 20px;'>{header}{logs_html}</body></html>"
    return html

bot_started = False
bot_lock = threading.Lock()

@app.before_request
def start_bot_thread_on_first_request():
    global bot_started
    if not bot_started:
        with bot_lock:
            if not bot_started:
                bot_thread = threading.Thread(target=run_oci_bot)
                bot_thread.daemon = True
                bot_thread.start()
                bot_started = True

if __name__ == '__main__':
    # Render requires a web server binding to the $PORT env variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

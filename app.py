from flask import Flask
import threading
import os
import subprocess
import time

app = Flask(__name__)
# Keep the last 50 lines of logs in memory
bot_logs = []

def run_oci_bot():
    global bot_logs
    bot_logs.append("Starting Oracle Auto-Retry bot in the background...")
    
    # Use Popen to stream the output live
    process = subprocess.Popen(
        ["python", "-u", "oracle-arm-retry.py"],  # -u for unbuffered output
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

if __name__ == '__main__':
    # Start the infinite retry script in a background thread
    bot_thread = threading.Thread(target=run_oci_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Render requires a web server binding to the $PORT env variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

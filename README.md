# Oracle ARM Auto-Provisioner

This script automatically retries requesting a free ARM Ampere A1 instance from Oracle Cloud every 60 seconds until capacity is found.

## 🚨 IMPORTANT SECURITY WARNING 🚨
NEVER push your real `.env` file to GitHub! 
This folder includes a `.gitignore` that ignores `.env` by default to keep you safe.

## How to run this 24/7 without keeping your PC on:

You have 3 free options:

### Option 1: The "Always Free" VM Method (BEST & EASIEST) ⭐
You already have an "Always Free" Oracle server running your backend right now (`VM.Standard.E2.1.Micro`)! You can simply run this script on that server because it's already running 24/7 for free.
1. SSH into your current Oracle backend server.
2. Upload this folder to the server.
3. Install dependencies: `pip3 install oci python-dotenv`
4. Run it in the background using screen or nohup: 
   `nohup python3 oracle-arm-retry.py &`
5. You can now close your laptop and it will run forever until it secures the ARM server.

### Option 2: PythonAnywhere (Free Tier)
1. Go to [PythonAnywhere.com](https://www.pythonanywhere.com/) and create a free account.
2. Upload `oracle-arm-retry.py` and your `.env` file.
3. Open a Bash console from their dashboard.
4. Run `pip install oci python-dotenv`
5. Run `python oracle-arm-retry.py`
*(Note: PythonAnywhere free tier consoles occasionally restart naturally, but it's completely browser-based).*

### Option 3: Oracle Cloud Shell (Built-in)
Oracle has a built-in free Linux terminal directly in your web browser.
1. Go to the [Oracle Console](https://cloud.oracle.com).
2. Click the `>_` Cloud Shell icon at the very top right.
### Option 4: Render.com (Requires Cron-job ping)
You can deploy this repository directly to Render.com as a free **Web Service**.
Because Render's free tier requires your app to run as a web server, this repository includes an `app.py` wrapper that runs the Oracle bot in the background while serving a dummy webpage.
**Important:** Render puts free services to sleep after 15 minutes of inactivity. To prevent this, sign up for a free account at [cron-job.org](https://cron-job.org/) and configure it to visit your Render website URL every 14 minutes.
1. Push this `oci-bot` folder to a new GitHub repository.
2. Go to [Render.com](https://render.com) > New > Web Service.
3. Connect your GitHub repository.
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `python app.py`
6. In the Render Environment Variables tab, you must add **9** variables:
   - Your original 4 (`OCI_COMPARTMENT_ID`, `OCI_SUBNET_ID`, `OCI_IMAGE_ID`, `OCI_SSH_PUBLIC_KEY`)
   - The 5 authentication variables found inside your local `C:\\Users\\admin\\.oci\\config` file:
     - `OCI_USER_ID`: (Your user OCID)
     - `OCI_TENANT_ID`: (Your tenancy OCID)
     - `OCI_FINGERPRINT`: (Your fingerprint)
     - `OCI_REGION`: (e.g. `ap-mumbai-1`)
     - `OCI_KEY_CONTENT`: (Open your `.pem` key file in notepad, copy the ENTIRE text including `-----BEGIN RSA PRIVATE KEY-----` and paste it here)
7. Click Deploy, then grab your URL and put it into cron-job.org!

*(Note: Oracle Cloud Shell pauses if you close your browser tab for more than 20 minutes, so you'd have to leave the browser tab open).*

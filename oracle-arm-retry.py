"""
Oracle ARM Ampere A1 Instance Auto-Retry Script
================================================
This script automatically retries creating an Oracle Cloud ARM instance
until capacity becomes available. It runs every 60 seconds.

SETUP:
1. Install OCI CLI:  pip install oci-cli
2. Run:              oci setup config
   - Follow the prompts to enter your User OCID, Tenancy OCID, Region, and API Key
3. Fill in the CONFIG section below with your Oracle Cloud details
4. Run:              python oracle-arm-retry.py
"""

import oci
import sys
import random
import time
from datetime import datetime

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# ⚙️ CONFIG - THESE VALUES ARE LOADED FROM .env
# ============================================================

COMPARTMENT_ID = os.environ.get("OCI_COMPARTMENT_ID", "").strip().strip('"').strip("'")
SUBNET_ID = os.environ.get("OCI_SUBNET_ID", "").strip().strip('"').strip("'")
IMAGE_ID = os.environ.get("OCI_IMAGE_ID", "").strip().strip('"').strip("'")
SSH_PUBLIC_KEY = os.environ.get("OCI_SSH_PUBLIC_KEY", "").strip().strip('"').strip("'")

# Availability Domains (Fetched dynamically in main())
AVAILABILITY_DOMAINS = [] 

# Instance name
INSTANCE_NAME = "strex-server"

# Shape configuration
SHAPE = "VM.Standard.A1.Flex"
OCPUS = 1          # 1 core
MEMORY_GB = 6      # 6 GB RAM
BOOT_VOLUME_GB = 50  # 50 GB disk

# Retry settings
RETRY_INTERVAL_SECONDS = 30  # Increased to 30s to avoid rate limits
MAX_RETRIES = 10000          # Run for much longer

# ============================================================
# 🚀 SCRIPT - DO NOT EDIT BELOW THIS LINE
# ============================================================

def log(message):

    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_instance(compute_client, availability_domain):
    """Attempt to create the ARM instance in a specific AD."""
    
    instance_details = oci.core.models.LaunchInstanceDetails(
        compartment_id=COMPARTMENT_ID,
        availability_domain=availability_domain,
        display_name=INSTANCE_NAME,
        shape=SHAPE,
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=float(OCPUS),
            memory_in_gbs=float(MEMORY_GB)
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            source_type="image",
            image_id=IMAGE_ID,
            boot_volume_size_in_gbs=BOOT_VOLUME_GB
        ),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=SUBNET_ID,
            assign_public_ip=True
        ),
        metadata={
            "ssh_authorized_keys": SSH_PUBLIC_KEY
        },
        is_pv_encryption_in_transit_enabled=True
    )
    
    response = compute_client.launch_instance(instance_details)
    return response.data

def main():
    # Validate config
    placeholders = []
    if not COMPARTMENT_ID:
        placeholders.append("OCI_COMPARTMENT_ID")
    if not SUBNET_ID:
        placeholders.append("OCI_SUBNET_ID")
    if not IMAGE_ID:
        placeholders.append("OCI_IMAGE_ID")
    if not SSH_PUBLIC_KEY:
        placeholders.append("OCI_SSH_PUBLIC_KEY")
    
    if placeholders:
        log("❌ ERROR: You need to fill in these values in the CONFIG section:")
        for p in placeholders:
            log(f"   → {p}")
        log("")
        log("📖 HOW TO FIND THESE VALUES:")
        log("   COMPARTMENT_ID : Oracle Console → Identity → Compartments → Copy OCID")
        log("   SUBNET_ID      : Oracle Console → Networking → VCNs → Your VCN → Subnets → Copy OCID")
        log("   IMAGE_ID       : Oracle Console → Compute → Custom Images (or from instance creation page URL)")
        log("   SSH_PUBLIC_KEY  : Contents of the .pub file you downloaded")
        sys.exit(1)
    
    # Determine Authentication Method
    # 1. Try Environment Variables (For Render / Cloud)
    oci_user = os.environ.get("OCI_USER_ID", "")
    oci_fingerprint = os.environ.get("OCI_FINGERPRINT", "")
    oci_tenancy = os.environ.get("OCI_TENANT_ID", "")
    oci_region = os.environ.get("OCI_REGION", "")
    oci_key_content = os.environ.get("OCI_KEY_CONTENT", "")
    
    if oci_user and oci_fingerprint and oci_tenancy and oci_region and oci_key_content:
        log("☁️ Cloud Environment detected. Using OCI Environment Variables.")
        # Fix potential newline escaping issues from Render dashboard
        oci_key_content = oci_key_content.replace('\\n', '\n')
        
        config = {
            "user": oci_user,
            "fingerprint": oci_fingerprint,
            "tenancy": oci_tenancy,
            "region": oci_region,
            "key_content": oci_key_content
        }
        try:
            oci.config.validate_config(config)
            log("✅ OCI Cloud config validated successfully.")
        except Exception as e:
            log(f"❌ Failed to validate OCI Cloud config: {e}")
            sys.exit(1)
            
    # 2. Try Local File Fallback (For PC)
    else:
        try:
            config = oci.config.from_file()
            log("✅ Local OCI config loaded successfully (~/.oci/config)")
        except Exception as e:
            log(f"❌ Failed to load OCI config: {e}")
            log("   Render Users: You must add OCI_USER_ID, OCI_FINGERPRINT, OCI_TENANT_ID, OCI_REGION, and OCI_KEY_CONTENT to Render Env Vars!")
            log("   Local Users:  Run 'oci setup config' first to configure your credentials")
            sys.exit(1)
    
    compute_client = oci.core.ComputeClient(config)
    
    # 3. Dynamically fetch Availability Domains (Avoids prefix mismatches like VFRl:)
    try:
        identity_client = oci.identity.IdentityClient(config)
        ads = identity_client.list_availability_domains(oci_tenancy or config['tenancy']).data
        dynamic_ads = [ad.name for ad in ads]
        log(f"✅ Dynamically fetched ADs: {', '.join(dynamic_ads)}")
    except Exception as e:
        log(f"⚠️ Warning: Could not fetch ADs dynamically: {e}")
        dynamic_ads = AVAILABILITY_DOMAINS

    log("=" * 60)
    log("🚀 Oracle ARM Ampere A1 Auto-Retry Script")
    log("=" * 60)
    log(f"   Shape    : {SHAPE}")
    log(f"   OCPUs    : {OCPUS}")
    log(f"   Memory   : {MEMORY_GB} GB")
    log(f"   Disk     : {BOOT_VOLUME_GB} GB")
    log(f"   Region   : {config.get('region', 'unknown')}")
    log(f"   ADs      : {', '.join([ad.split(':')[-1] for ad in dynamic_ads])}")
    log(f"   Interval : Every {RETRY_INTERVAL_SECONDS} seconds")
    log(f"   Max tries: {MAX_RETRIES}")
    log("=" * 60)
    log("")

    # Debug check for ID formats
    log("🔍 Configuration Check:")
    log(f"   Compartment ID length: {len(COMPARTMENT_ID)}")
    log(f"   Subnet ID length     : {len(SUBNET_ID)}")
    log(f"   Image ID length      : {len(IMAGE_ID)}")
    log(f"   SSH Key length       : {len(SSH_PUBLIC_KEY)}")
    if SSH_PUBLIC_KEY.startswith('"') or SSH_PUBLIC_KEY.startswith("'"):
        log("   ⚠️ WARNING: SSH key starts with a quote character!")
    
    for attempt in range(1, MAX_RETRIES + 1):
        # Randomly choose an availability domain from the fetched list
        ad_to_try = random.choice(dynamic_ads)
        ad_name = ad_to_try.split(':')[-1]

        try:
            log(f"🔄 Attempt {attempt}/{MAX_RETRIES} - Using {ad_name} - Creating instance...")
            instance = create_instance(compute_client, ad_to_try)
            
            log("")
            log("=" * 60)
            log("🎉🎉🎉 SUCCESS! Instance created! 🎉🎉🎉")
            log("=" * 60)
            log(f"   Instance ID   : {instance.id}")
            log(f"   Display Name  : {instance.display_name}")
            log(f"   State         : {instance.lifecycle_state}")
            log(f"   Time Created  : {instance.time_created}")
            log("")
            log("⏳ Waiting for instance to get a Public IP...")
            log("   Check your Oracle Console → Compute → Instances → strex-server")
            log("")
            log("🏎️ Your new server has been created!")
            log(f"   Shape: {SHAPE} ({OCPUS} OCPU, {MEMORY_GB} GB RAM)")
            log("   Go tell your AI assistant the Public IP to set everything up!")
            
            # Try to send a Windows notification
            try:
                from plyer import notification
                notification.notify(
                    title="🎉 Oracle ARM Instance Created!",
                    message=f"Instance '{INSTANCE_NAME}' is now provisioning! Check your Oracle Console.",
                    timeout=30
                )
            except ImportError:
                pass  # plyer not installed, skip notification
            
            return  # SUCCESS - Exit the script
            
        except oci.exceptions.ServiceError as e:
            if e.status == 400 and e.code == "CannotParseRequest":
                log("   ❌ API Error (400): CannotParseRequest")
                log("      This often means a parameter is invalid. Let's check the details:")
                log(f"      Selected AD: {ad_to_try}")
                log(f"      OCPUs      : {OCPUS}")
                log(f"      Memory     : {MEMORY_GB} GB")
                log(f"      Full Error : {e.message}")
            elif e.status == 500 and "Out of capacity" in str(e.message):
                log(f"   ⚠️ Out of capacity. Retrying in {RETRY_INTERVAL_SECONDS}s...")
            elif e.status == 500 and "Out of host capacity" in str(e.message):
                log(f"   ⚠️ Out of host capacity. Retrying in {RETRY_INTERVAL_SECONDS}s...")
            elif e.status == 429:
                log(f"   ⏱️ Rate limited. Waiting 120s before retry...")
                time.sleep(120)
                continue
            else:
                log(f"   ❌ API Error ({e.status}): {e.message}")
                log(f"      Code     : {e.code}")
                # Detailed OCI Error Logging
                log(f"      Target   : {getattr(e, 'target_service', 'Unknown')}")
                log(f"      Operation: {getattr(e, 'operation_name', 'Unknown')}")
                log(f"      RequestID: {getattr(e, 'request_id', 'Unknown')}")
                log(f"      Hint     : {getattr(e, 'troubleshooting_tips', 'None provided')}")
                
                # Check for common configuration mistakes:
                log("")
                log("   🔍 TROUBLESHOOTING TIPS:")
                log("   ------------------------")
                if e.status == 404:
                    log("   1. You are seeing a 404 NotAuthorizedOrNotFound error.")
                    log("   2. In OCI, this almost ALWAYS means your API User is missing IAM Policies.")
                    log("   3. Check that your user is in the 'Administrators' group.")
                    log("   4. Verify the Compartment ID in your .env file is correct.")
                    
            time.sleep(RETRY_INTERVAL_SECONDS + random.randint(1, 5))
            
        except Exception as e:
            log(f"   ❌ Unexpected error: {str(e)}")
            time.sleep(RETRY_INTERVAL_SECONDS + random.randint(1, 5))
    
    log("")
    log(f"😞 Exhausted all {MAX_RETRIES} attempts. No capacity found.")
    log("   Try again later or try a different availability domain.")

if __name__ == "__main__":
    main()

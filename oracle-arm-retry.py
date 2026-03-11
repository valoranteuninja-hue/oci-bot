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
import time
import json
from datetime import datetime

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# ⚙️ CONFIG - THESE VALUES ARE LOADED FROM .env
# ============================================================

COMPARTMENT_ID = os.environ.get("OCI_COMPARTMENT_ID", "")
SUBNET_ID = os.environ.get("OCI_SUBNET_ID", "")
IMAGE_ID = os.environ.get("OCI_IMAGE_ID", "")
SSH_PUBLIC_KEY = os.environ.get("OCI_SSH_PUBLIC_KEY", "")

# Availability Domain (from your Oracle Console)
AVAILABILITY_DOMAIN = os.environ.get("OCI_AVAILABILITY_DOMAIN", "VFRl:AP-MUMBAI-1-AD-1")

# Instance name
INSTANCE_NAME = "strex-server"

# Shape configuration
SHAPE = "VM.Standard.A1.Flex"
OCPUS = 4          # 4 cores (max free)
MEMORY_GB = 24     # 24 GB RAM (max free)
BOOT_VOLUME_GB = 50  # 50 GB disk

# Retry settings
RETRY_INTERVAL_SECONDS = 60  # Try every 60 seconds
MAX_RETRIES = 1440           # Keep trying for 24 hours (1440 minutes)

# ============================================================
# 🚀 SCRIPT - DO NOT EDIT BELOW THIS LINE
# ============================================================

def log(message):

    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_instance(compute_client):
    """Attempt to create the ARM instance."""
    
    instance_details = oci.core.models.LaunchInstanceDetails(
        compartment_id=COMPARTMENT_ID,
        availability_domain=AVAILABILITY_DOMAIN,
        display_name=INSTANCE_NAME,
        shape=SHAPE,
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=OCPUS,
            memory_in_gbs=MEMORY_GB
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
    
    # Load OCI config from ~/.oci/config
    try:
        config = oci.config.from_file()
        log("✅ OCI config loaded successfully")
    except Exception as e:
        log(f"❌ Failed to load OCI config: {e}")
        log("   Run 'oci setup config' first to configure your credentials")
        sys.exit(1)
    
    compute_client = oci.core.ComputeClient(config)
    
    log("=" * 60)
    log("🚀 Oracle ARM Ampere A1 Auto-Retry Script")
    log("=" * 60)
    log(f"   Shape    : {SHAPE}")
    log(f"   OCPUs    : {OCPUS}")
    log(f"   Memory   : {MEMORY_GB} GB")
    log(f"   Disk     : {BOOT_VOLUME_GB} GB")
    log(f"   Region   : {config.get('region', 'unknown')}")
    log(f"   Interval : Every {RETRY_INTERVAL_SECONDS} seconds")
    log(f"   Max tries: {MAX_RETRIES}")
    log("=" * 60)
    log("")
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"🔄 Attempt {attempt}/{MAX_RETRIES} - Creating instance...")
            instance = create_instance(compute_client)
            
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
            log("🏎️ Your new server has 4 ARM cores + 24GB RAM!")
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
            if e.status == 500 and "Out of capacity" in str(e.message):
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
                    
            time.sleep(RETRY_INTERVAL_SECONDS)
            
        except Exception as e:
            log(f"   ❌ Unexpected error: {str(e)}")
            time.sleep(RETRY_INTERVAL_SECONDS)
    
    log("")
    log(f"😞 Exhausted all {MAX_RETRIES} attempts. No capacity found.")
    log("   Try again later or try a different availability domain.")

if __name__ == "__main__":
    main()

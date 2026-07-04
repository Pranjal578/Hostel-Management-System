import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure app module can be found
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.utils.email_sender import send_test_email
from app.utils.sms_sender import send_test_sms

app = create_app()
with app.app_context():
    print("==================================================")
    print("HOSTEL SAAS PLATFORM INTEGRATIONS TESTING UTILITY")
    print("==================================================")
    
    # 1. Test Email Configuration
    email = input("\nEnter email address to receive test email (leave empty to skip): ").strip()
    if email:
        print(f"Sending test email to {email}...")
        success, msg = send_test_email(email)
        if success:
            print("✔ Email sent successfully!")
        else:
            print(f"✘ Email delivery failed: {msg}")
    else:
        print("Skipped email test.")
            
    # 2. Test SMS Configuration
    phone = input("\nEnter mobile number with country code (e.g. +91XXXXXXXXXX) to receive test SMS (leave empty to skip): ").strip()
    if phone:
        print(f"Sending test SMS to {phone}...")
        success, msg = send_test_sms(phone)
        if success:
            print("✔ SMS sent successfully!")
        else:
            print(f"✘ SMS delivery failed: {msg}")
    else:
        print("Skipped SMS test.")
            
    print("\nIntegrations check complete.")

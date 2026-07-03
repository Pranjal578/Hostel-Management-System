"""
SMS Sender Module

Handles sending OTP via SMS using Twilio API
Uses current_app to fetch Twilio credentials dynamically.
"""

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask import current_app


def send_otp_sms(phone_number, otp_code, resident_name=None):
    """
    Send OTP via SMS to resident

    Args:
        phone_number (str): Recipient phone number (with country code, e.g., +1234567890)
        otp_code (str): The OTP code to send
        resident_name (str): Name of resident (optional)

    Returns:
        tuple: (success: bool, message: str)
            - (True, "SMS sent successfully") if successful
            - (False, error_message) if failed
    """
    try:
        # Check if Twilio is configured
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        from_phone = current_app.config.get('TWILIO_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_phone]):
            return False, "SMS service not configured. Please contact support."

        # Create Twilio client
        client = Client(account_sid, auth_token)

        # Create message
        message_text = f"Your OTP for Hostel Management System login is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nIf you didn't request this, please ignore this message."

        # Send SMS
        message = client.messages.create(
            body=message_text,
            from_=from_phone,
            to=phone_number
        )

        return True, f"OTP sent successfully to {mask_phone(phone_number)}"

    except TwilioRestException as e:
        error_msg = f"Twilio Error: {e.msg}"
        print(f"SMS Error: {error_msg}")
        return False, "Failed to send SMS. Please check your phone number and try again."

    except Exception as e:
        error_msg = f"Failed to send SMS: {str(e)}"
        print(f"SMS Error: {error_msg}")
        return False, "Failed to send SMS. Please try again later."


def send_test_sms(phone_number):
    """
    Send a test SMS to verify SMS configuration

    Args:
        phone_number (str): Recipient phone number

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        from_phone = current_app.config.get('TWILIO_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_phone]):
            return False, "SMS service not configured"

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body="Test SMS from Hostel Management System. If you received this, SMS configuration is working correctly.",
            from_=from_phone,
            to=phone_number
        )

        return True, "Test SMS sent successfully"

    except Exception as e:
        return False, f"Failed to send test SMS: {str(e)}"


def mask_phone(phone_number):
    """
    Mask phone number for display (show only last 4 digits)

    Args:
        phone_number (str): Phone number to mask

    Returns:
        str: Masked phone number (e.g., "+1***5678")
    """
    if not phone_number or len(phone_number) < 5:
        return "****"

    return phone_number[:-4] + "****"

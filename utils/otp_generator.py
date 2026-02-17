"""
OTP Generator and Validator Module

Handles generation, validation, and management of One-Time Passwords
"""

import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


def generate_otp(length=6):
    """
    Generate a random OTP code

    Args:
        length (int): Length of OTP to generate (default: 6 digits)

    Returns:
        str: Generated OTP code (numeric)
    """
    return ''.join(random.choices(string.digits, k=length))


def hash_otp(otp_code):
    """
    Hash OTP code for secure storage

    Args:
        otp_code (str): The OTP code to hash

    Returns:
        str: Hashed OTP code
    """
    return generate_password_hash(otp_code, method='pbkdf2:sha256')


def validate_otp(otp_code, stored_hash, expires_at):
    """
    Validate OTP code against stored hash and expiry time

    Args:
        otp_code (str): The OTP code entered by user
        stored_hash (str): The hashed OTP stored in database
        expires_at (datetime): The expiry time of OTP

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
            - (True, None) if OTP is valid
            - (False, error_message) if OTP is invalid or expired
    """
    # Check if OTP has expired
    if expires_at:
        if datetime.utcnow() > expires_at:
            return False, "OTP has expired. Please request a new one."
    else:
        return False, "OTP not found. Please request a new one."

    # Check if OTP code matches stored hash
    if check_password_hash(stored_hash, otp_code):
        return True, None
    else:
        return False, "Invalid OTP code. Please try again."


def is_otp_expired(expires_at):
    """
    Check if OTP has expired

    Args:
        expires_at (datetime): The expiry time of OTP

    Returns:
        bool: True if expired, False otherwise
    """
    if not expires_at:
        return True

    return datetime.utcnow() > expires_at


def get_otp_expiry_time(expiry_minutes=10):
    """
    Get OTP expiry time

    Args:
        expiry_minutes (int): Minutes until OTP expires (default: 10)

    Returns:
        datetime: The time when OTP will expire
    """
    return datetime.utcnow() + timedelta(minutes=expiry_minutes)


def get_remaining_time(expires_at):
    """
    Get remaining time for OTP validity

    Args:
        expires_at (datetime): The expiry time of OTP

    Returns:
        dict: Contains remaining seconds and formatted time string
            {
                'seconds': int,
                'minutes': int,
                'display': str (format: "M:SS")
            }
    """
    if not expires_at:
        return {'seconds': 0, 'minutes': 0, 'display': '0:00'}

    remaining = expires_at - datetime.utcnow()
    seconds = max(0, int(remaining.total_seconds()))
    minutes = seconds // 60
    secs = seconds % 60

    return {
        'seconds': seconds,
        'minutes': minutes,
        'display': f"{minutes}:{secs:02d}"
    }

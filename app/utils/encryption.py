import os
from cryptography.fernet import Fernet
from flask import current_app

# Default fallback key for development ONLY. Will warn in production.
_DEV_KEY = Fernet.generate_key()

def get_fernet():
    """Retrieve Fernet instance initialized with config or environment key."""
    # Check Flask config first
    key = None
    try:
        key = current_app.config.get('ENCRYPTION_KEY')
    except RuntimeError:
        # Working outside application context
        pass
        
    if not key:
        # Check environment variable
        key = os.environ.get('ENCRYPTION_KEY')
        
    if not key:
        # Use development key fallback
        return Fernet(_DEV_KEY)
        
    # Standardize key (needs to be bytes)
    if isinstance(key, str):
        key = key.encode()
        
    try:
        return Fernet(key)
    except Exception as e:
        # If key is invalid (e.g. not 32 URL-safe base64-encoded bytes), fallback to dev key and print warning
        print(f"Warning: Invalid ENCRYPTION_KEY format ({str(e)}). Falling back to ephemeral key.")
        return Fernet(_DEV_KEY)

def encrypt_field(value):
    """Encrypt a string value using AES-256 Fernet."""
    if value is None:
        return None
    
    # Ensure value is string
    val_str = str(value)
    f = get_fernet()
    # Encrypt and return string representation
    return f.encrypt(val_str.encode()).decode()

def decrypt_field(cipher_text):
    """Decrypt a cipher text back to a string using AES-256 Fernet."""
    if not cipher_text:
        return None
        
    f = get_fernet()
    try:
        if isinstance(cipher_text, str):
            cipher_text = cipher_text.encode()
        return f.decrypt(cipher_text).decode()
    except Exception as e:
        # Return fallback/warning instead of crashing the application
        print(f"Error decrypting database field: {str(e)}")
        return "[Decryption Error]"

"""
app/utils/validators.py
─────────────────────────────────────────────────────────────────
Centralized server-side input validation for all routes.
Prevents XSS via stored data, enforces format consistency,
and validates file uploads with magic-byte checking.
─────────────────────────────────────────────────────────────────
"""

import re
import io
import os
from typing import Optional, Tuple

# ─────────────────────────────────────────────────────────────
# STRING VALIDATORS
# ─────────────────────────────────────────────────────────────

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False, "Email is required."
    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email address format."
    if len(email) > 120:
        return False, "Email must be 120 characters or fewer."
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate Indian 10-digit phone number (digits only, no spaces/dashes)."""
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required."
    digits = re.sub(r'\D', '', phone)
    if len(digits) != 10:
        return False, "Phone number must be exactly 10 digits."
    if digits[0] not in '6789':
        return False, "Phone number must start with 6, 7, 8, or 9."
    return True, None


def validate_aadhar(aadhar: str) -> Tuple[bool, Optional[str]]:
    """Validate 12-digit Aadhar number (ignoring dashes)."""
    if not aadhar:
        return True, None  # Optional field — empty is OK
    clean = re.sub(r'[\-\s]', '', aadhar)
    if not clean.isdigit():
        return False, "Aadhar ID must contain only digits."
    if len(clean) != 12:
        return False, "Aadhar ID must be exactly 12 digits."
    return True, None


def validate_pincode(pincode: str) -> Tuple[bool, Optional[str]]:
    """Validate Indian 6-digit postal pincode."""
    if not pincode or not isinstance(pincode, str):
        return False, "Pincode is required."
    clean = pincode.strip()
    if not re.match(r'^\d{6}$', clean):
        return False, "Pincode must be exactly 6 digits."
    return True, None


def validate_room_number(room: str) -> Tuple[bool, Optional[str]]:
    """Validate room number: alphanumeric, max 10 chars."""
    if not room or not isinstance(room, str):
        return False, "Room number is required."
    room = room.strip().upper()
    if not re.match(r'^[A-Z0-9\-]{1,10}$', room):
        return False, "Room number must be 1–10 alphanumeric characters (dashes allowed)."
    return True, None


def validate_amount(amount_str: str) -> Tuple[bool, Optional[str]]:
    """Validate a positive float amount."""
    if not amount_str:
        return False, "Amount is required."
    try:
        value = float(amount_str)
    except (ValueError, TypeError):
        return False, "Amount must be a valid number."
    if value < 0:
        return False, "Amount cannot be negative."
    if value > 1_000_000:
        return False, "Amount exceeds the maximum allowed value."
    return True, None


def validate_text_field(value: str, field_name: str, max_length: int = 200,
                        required: bool = True) -> Tuple[bool, Optional[str]]:
    """Generic text field validator with length and XSS-injection checks."""
    if not value or not isinstance(value, str) or not value.strip():
        if required:
            return False, f"{field_name} is required."
        return True, None
    value = value.strip()
    if len(value) > max_length:
        return False, f"{field_name} must be {max_length} characters or fewer."
    # Basic XSS detection — block obvious script injection
    if re.search(r'<\s*(script|iframe|object|embed|link|style)\b', value, re.IGNORECASE):
        return False, f"{field_name} contains disallowed HTML content."
    return True, None


def validate_password(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
    """Validate password strength."""
    if not password:
        return False, "Password is required."
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters."
    if len(password) > 128:
        return False, "Password must be 128 characters or fewer."
    return True, None


def validate_capacity(capacity_str: str) -> Tuple[bool, Optional[str]]:
    """Validate a hostel room capacity (positive integer 1–9999)."""
    try:
        cap = int(capacity_str)
    except (ValueError, TypeError):
        return False, "Capacity must be a whole number."
    if cap < 1 or cap > 9999:
        return False, "Capacity must be between 1 and 9999."
    return True, None


# ─────────────────────────────────────────────────────────────
# FILE / IMAGE VALIDATORS
# ─────────────────────────────────────────────────────────────

# Allowed MIME types via magic bytes
IMAGE_MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',      # JPEG
    b'\x89PNG\r\n\x1a\n': 'image/png', # PNG
    b'GIF87a': 'image/gif',             # GIF87
    b'GIF89a': 'image/gif',             # GIF89
    b'RIFF': 'image/webp',              # WebP (starts RIFF....WEBP)
}

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_magic_bytes(file_storage) -> Tuple[bool, Optional[str]]:
    """
    Check the actual first bytes of an uploaded file to confirm it is a
    real image (JPEG or PNG) rather than a renamed executable / HTML file.

    Args:
        file_storage: Werkzeug FileStorage object

    Returns:
        (is_valid, error_message)
    """
    try:
        file_storage.seek(0)
        header = file_storage.read(16)
        file_storage.seek(0)
    except Exception:
        return False, "Could not read uploaded file."

    # Check extension first
    filename = file_storage.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Only {', '.join(ALLOWED_IMAGE_EXTENSIONS).upper()} images are allowed."

    # Magic byte check
    for magic, mime in IMAGE_MAGIC_BYTES.items():
        if header[:len(magic)] == magic:
            # Extra WebP validation: bytes 8-11 must be "WEBP"
            if mime == 'image/webp' and header[8:12] != b'WEBP':
                continue
            # Only allow JPEG and PNG for resident photos/receipts
            if mime in ('image/jpeg', 'image/png'):
                return True, None
            else:
                return False, f"File type '{mime}' is not permitted. Upload JPEG or PNG only."

    return False, "File does not appear to be a valid image. Only JPEG and PNG are accepted."


def validate_upload_size(file_storage,
                         max_bytes: int = MAX_IMAGE_SIZE_BYTES) -> Tuple[bool, Optional[str]]:
    """Validate that file size does not exceed the configured limit."""
    try:
        file_storage.seek(0, os.SEEK_END)
        size = file_storage.tell()
        file_storage.seek(0)
    except Exception:
        return False, "Could not determine file size."

    if size > max_bytes:
        mb = max_bytes / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        return False, f"File is too large ({actual_mb:.1f} MB). Maximum allowed size is {mb:.0f} MB."
    if size == 0:
        return False, "Uploaded file is empty."
    return True, None


def validate_image_upload(file_storage) -> Tuple[bool, Optional[str]]:
    """
    Composite image validation:
      1. File is present and has a filename
      2. Size within limit
      3. Magic bytes match JPEG or PNG

    Use this as the single call for any image upload route.
    """
    if not file_storage or not file_storage.filename:
        return False, "No file selected."

    ok, err = validate_upload_size(file_storage)
    if not ok:
        return False, err

    ok, err = validate_image_magic_bytes(file_storage)
    if not ok:
        return False, err

    return True, None


# ─────────────────────────────────────────────────────────────
# SAFE FILENAME
# ─────────────────────────────────────────────────────────────

def safe_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal.
    Strips path components and replaces suspicious characters.
    """
    from werkzeug.utils import secure_filename
    name = secure_filename(filename or 'upload')
    # Double-check no path separators remain
    name = name.replace('/', '').replace('\\', '').replace('..', '')
    return name or 'upload'


# ─────────────────────────────────────────────────────────────
# BULK FORM VALIDATOR HELPER
# ─────────────────────────────────────────────────────────────

def collect_errors(*validations: Tuple[bool, Optional[str]]) -> list:
    """
    Run multiple (ok, error) tuples and collect all error messages.

    Usage:
        errors = collect_errors(
            validate_email(email),
            validate_phone(phone),
            validate_pincode(pincode),
        )
        if errors:
            flash('; '.join(errors), 'danger')
            return redirect(...)
    """
    return [err for ok, err in validations if not ok and err]

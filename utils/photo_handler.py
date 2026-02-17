"""
Photo Upload Handler Module

Handles photo upload, validation, storage (both Base64 and file),
and retrieval for resident profiles.
"""

import os
import base64
from werkzeug.utils import secure_filename
from datetime import datetime

# Configuration
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB
PHOTO_FOLDER = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Get file extension"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return 'jpg'


def validate_photo(file):
    """
    Validate photo file

    Args:
        file: FileStorage object from request.files

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not file or file.filename == '':
        return False, "No file selected"

    if not allowed_file(file.filename):
        return False, "Invalid file format. Only JPG and PNG allowed."

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_PHOTO_SIZE:
        return False, f"File too large. Maximum size is 5MB (Current: {file_size / 1024 / 1024:.1f}MB)"

    return True, None


def file_to_base64(file):
    """
    Convert file to Base64 string

    Args:
        file: FileStorage object

    Returns:
        str: Base64 encoded string
    """
    file.seek(0)
    file_data = file.read()
    return base64.b64encode(file_data).decode('utf-8')


def base64_to_bytes(base64_string):
    """
    Convert Base64 string to bytes

    Args:
        base64_string: Base64 encoded string

    Returns:
        bytes: Decoded binary data
    """
    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        print(f"Error decoding Base64: {e}")
        return None


def save_photo_file(file, resident_id):
    """
    Save photo file to filesystem

    Args:
        file: FileStorage object
        resident_id: ID of resident

    Returns:
        tuple: (success: bool, filename: str, error: str)
    """
    try:
        # Create folder if needed
        if not os.path.exists(PHOTO_FOLDER):
            os.makedirs(PHOTO_FOLDER)

        # Get file extension
        ext = get_file_extension(file.filename)

        # Create filename
        filename = f"resident_{resident_id}.{ext}"
        filepath = os.path.join(PHOTO_FOLDER, filename)

        # Save file
        file.seek(0)
        file.save(filepath)

        return True, filename, None

    except Exception as e:
        error_msg = f"Error saving photo: {str(e)}"
        print(error_msg)
        return False, None, error_msg


def delete_photo_file(resident_id):
    """
    Delete photo file from filesystem

    Args:
        resident_id: ID of resident

    Returns:
        bool: Success status
    """
    try:
        # Try both jpg and png
        for ext in ['jpg', 'jpeg', 'png']:
            filepath = os.path.join(PHOTO_FOLDER, f"resident_{resident_id}.{ext}")
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        return False

    except Exception as e:
        print(f"Error deleting photo: {e}")
        return False


def save_photo(file, resident_id, db=None, resident=None):
    """
    Save photo to both Base64 (database) and file (filesystem)

    Args:
        file: FileStorage object from request.files
        resident_id: ID of resident
        db: SQLAlchemy db instance (optional, for saving to database)
        resident: Resident model instance (optional, for saving Base64)

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Validate photo
    is_valid, error_msg = validate_photo(file)
    if not is_valid:
        return False, error_msg

    # Convert to Base64
    try:
        base64_data = file_to_base64(file)
    except Exception as e:
        return False, f"Error processing photo: {str(e)}"

    # Save to file
    success, filename, error = save_photo_file(file, resident_id)
    if not success:
        return False, error

    # Save to database (Base64)
    if resident:
        try:
            resident.profile_photo_base64 = base64_data.encode('utf-8')
            resident.profile_image = filename
            if db:
                db.session.commit()
        except Exception as e:
            return False, f"Error saving to database: {str(e)}"

    return True, None


def load_photo(resident, prefer='file'):
    """
    Load photo for resident

    Args:
        resident: Resident model instance
        prefer: 'file' or 'base64' - which to prefer if both exist

    Returns:
        tuple: (photo_data, source, mime_type, error)
            - photo_data: bytes or Base64 string
            - source: 'file' or 'base64'
            - mime_type: 'image/jpeg' or 'image/png'
            - error: error message if any
    """
    image_ext = 'jpg'  # default

    if resident.profile_image:
        image_ext = resident.profile_image.rsplit('.', 1)[1].lower() if '.' in resident.profile_image else 'jpg'

    mime_type = 'image/jpeg' if image_ext in ['jpg', 'jpeg'] else 'image/png'

    # Try preferred source first
    if prefer == 'file' and resident.profile_image:
        filepath = os.path.join(PHOTO_FOLDER, resident.profile_image)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as f:
                    photo_data = f.read()
                return photo_data, 'file', mime_type, None
            except Exception as e:
                print(f"Error reading photo file: {e}")

    # Fallback to Base64
    if resident.profile_photo_base64:
        try:
            photo_data = resident.profile_photo_base64
            if isinstance(photo_data, bytes):
                photo_data = photo_data.decode('utf-8')
            return photo_data, 'base64', mime_type, None
        except Exception as e:
            print(f"Error reading Base64 photo: {e}")

    # Return default image
    return None, None, mime_type, "No photo available"


def get_photo_data_uri(resident, prefer='base64'):
    """
    Get photo as data URI for embedding in HTML

    Args:
        resident: Resident model instance
        prefer: 'file' or 'base64'

    Returns:
        str: Data URI string (e.g., "data:image/jpeg;base64,/9j/...")
    """
    photo_data, source, mime_type, error = load_photo(resident, prefer)

    if not photo_data:
        return None

    if source == 'base64':
        if isinstance(photo_data, bytes):
            photo_data = photo_data.decode('utf-8')
        return f"data:{mime_type};base64,{photo_data}"
    else:
        # For file source, convert to Base64
        if isinstance(photo_data, bytes):
            photo_b64 = base64.b64encode(photo_data).decode('utf-8')
            return f"data:{mime_type};base64,{photo_b64}"

    return None


def get_photo_url(resident):
    """
    Get photo URL for use in <img> src attribute

    Args:
        resident: Resident model instance

    Returns:
        str: URL path to photo
    """
    if resident.profile_image:
        return f"/static/images/{resident.profile_image}"
    return "/static/images/default_profile.png"


def cleanup_old_photo(resident_id):
    """
    Delete old photo file for resident (before uploading new one)

    Args:
        resident_id: ID of resident

    Returns:
        bool: Success status
    """
    return delete_photo_file(resident_id)

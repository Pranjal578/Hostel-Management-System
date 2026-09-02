"""
Photo Upload Handler Module

Handles photo upload, validation, storage (both Base64 and file),
and retrieval for resident profiles.
Now with Pillow-based image metadata (EXIF/GPS) sanitization.
"""

import os
import base64
import io
from PIL import Image
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
    Validate photo file — extension, size, and magic-byte content check.

    Args:
        file: FileStorage object from request.files

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not file or file.filename == '':
        return False, "No file selected"

    if not allowed_file(file.filename):
        return False, "Invalid file format. Only JPG, JPEG, and PNG allowed."

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_PHOTO_SIZE:
        return False, f"File too large. Maximum size is 5MB (Current: {file_size / 1024 / 1024:.1f}MB)"

    # Magic-byte check: confirm the actual file content matches an image
    try:
        from app.utils.validators import validate_image_magic_bytes
        ok, err = validate_image_magic_bytes(file)
        if not ok:
            return False, err
    except ImportError:
        pass  # Fallback: extension-only check if validators not yet available

    return True, None


def sanitize_image_metadata(file):
    """
    Strip EXIF/GPS metadata from image by opening and re-saving with Pillow.
    
    Args:
        file: FileStorage or file-like object
        
    Returns:
        BytesIO: A clean image file-like stream
    """
    file.seek(0)
    img = Image.open(file)
    
    # Strip EXIF: simply saving the image without exif/metadata parameters
    # strips it by default in Pillow.
    clean_io = io.BytesIO()
    
    # Preserving RGB/RGBA formats
    img_format = img.format if img.format else 'JPEG'
    img.save(clean_io, format=img_format)
    clean_io.seek(0)
    return clean_io


def file_to_base64(file_stream):
    """
    Convert sanitized file stream to Base64 string

    Args:
        file_stream: file-like stream object

    Returns:
        str: Base64 encoded string
    """
    file_stream.seek(0)
    file_data = file_stream.read()
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


def save_photo_file(sanitized_stream, filename):
    """
    Save photo file to filesystem

    Args:
        sanitized_stream: Sanitized BytesIO image stream
        filename: Destination filename

    Returns:
        tuple: (success: bool, error: str)
    """
    try:
        # Create folder if needed
        if not os.path.exists(PHOTO_FOLDER):
            os.makedirs(PHOTO_FOLDER)

        filepath = os.path.join(PHOTO_FOLDER, filename)

        # Save file from stream
        sanitized_stream.seek(0)
        with open(filepath, 'wb') as f:
            f.write(sanitized_stream.read())

        return True, None

    except Exception as e:
        error_msg = f"Error saving photo file: {str(e)}"
        print(error_msg)
        return False, error_msg


def delete_photo_file(resident_id):
    """
    Delete photo file from filesystem

    Args:
        resident_id: ID of resident

    Returns:
        bool: Success status
    """
    try:
        # Try both jpg/png
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
    Sanitize, check, and save photo to both Base64 (database) and file (filesystem)

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

    try:
        # Sanitize image (stripping EXIF metadata)
        sanitized_stream = sanitize_image_metadata(file)
        
        # Convert to Base64
        base64_data = file_to_base64(sanitized_stream)
        
        # Create filename
        ext = get_file_extension(file.filename)
        filename = f"resident_{resident_id}.{ext}"

        # Save to file
        success, error = save_photo_file(sanitized_stream, filename)
        if not success:
            return False, error

        # Save to database (Base64)
        if resident:
            resident.profile_photo_base64 = base64_data.encode('utf-8')
            resident.profile_image = filename
            if db:
                db.session.commit()

        return True, None
    except Exception as e:
        return False, f"Error processing and sanitizing photo: {str(e)}"


def load_photo(resident, prefer='file'):
    """
    Load photo for resident

    Args:
        resident: Resident model instance
        prefer: 'file' or 'base64' - which to prefer if both exist

    Returns:
        tuple: (photo_data, source, mime_type, error)
    """
    image_ext = 'jpg'

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

    return None, None, mime_type, "No photo available"


def get_photo_data_uri(resident, prefer='base64'):
    """
    Get photo as data URI for embedding in HTML
    """
    photo_data, source, mime_type, error = load_photo(resident, prefer)

    if not photo_data:
        return None

    if source == 'base64':
        if isinstance(photo_data, bytes):
            photo_data = photo_data.decode('utf-8')
        return f"data:{mime_type};base64,{photo_data}"
    else:
        if isinstance(photo_data, bytes):
            photo_b64 = base64.b64encode(photo_data).decode('utf-8')
            return f"data:{mime_type};base64,{photo_b64}"

    return None


def get_photo_url(resident):
    """
    Get photo URL for use in <img> src attribute
    """
    if resident and resident.profile_image:
        return f"/static/images/{resident.profile_image}"
    return "/static/images/default_profile.png"


def cleanup_old_photo(resident_id):
    """
    Delete old photo file for resident
    """
    return delete_photo_file(resident_id)

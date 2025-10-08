import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()

    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]

def save_and_resize_image(file_storage, base_name=None, max_size=(800, 800), thumb_size=(400, 300), quality=85):
    if not file_storage or file_storage.filename == "":
        return None, None

    filename = secure_filename(file_storage.filename)
    name, ext = os.path.splitext(filename)
    unique = f"{(base_name or uuid.uuid4().hex)}_{uuid.uuid4().hex}{ext}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, unique)

    file_storage.save(filepath)

    try:
        img = Image.open(filepath)
        img = img.convert("RGB")  # normalize
    except Exception:
        try:
            os.remove(filepath)
        except Exception:
            pass
        return None, None

    img.thumbnail(max_size, Image.LANCZOS)
    img.save(filepath, optimize=True, quality=quality)

    thumb_name = f"thumb_{unique}"
    thumb_path = os.path.join(upload_folder, thumb_name)

    thumb = Image.open(filepath)
    thumb.thumbnail(thumb_size, Image.LANCZOS)
    thumb.save(thumb_path, optimize=True, quality=quality)

    return unique, thumb_name
"""Store validated profile/listing photos without trusting upload filenames."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
from pathlib import Path
from uuid import uuid4
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from core.config import UPLOAD_DIR

MAX_PHOTO_BYTES = 5 * 1024 * 1024


def save_photo(upload, owner: str) -> str:
    if upload.size > MAX_PHOTO_BYTES:
        raise ValueError("Choose a photo smaller than 5 MB.")
    upload.seek(0)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as original:
                if original.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Use a JPEG, PNG, or WebP image.")
                photo = ImageOps.exif_transpose(original).convert("RGB")
                photo.thumbnail((1600, 1600))
                folder = Path(UPLOAD_DIR)
                folder.mkdir(parents=True, exist_ok=True)
                # owner is supplied by the application, never by the filename.
                filename = folder / f"{owner}_{uuid4().hex}.jpg"
                photo.save(filename, "JPEG", quality=85)
                return str(filename)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("This file could not be opened as a photo.") from exc

import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# Max sizes
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VOICE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "text/plain",
}
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


def get_message_type(mime_type: str) -> str:
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
    if mime_type in ALLOWED_AUDIO_TYPES:
        return "voice"
    if mime_type in ALLOWED_VIDEO_TYPES:
        return "video"
    if mime_type in ALLOWED_FILE_TYPES:
        return "file"
    return "file"


def upload_to_cloudinary(file_bytes: bytes, mime_type: str, filename: str) -> dict:
    msg_type = get_message_type(mime_type)

    # resource_type tells Cloudinary what it is
    resource_type = "auto"
    folder = f"pingspace/{msg_type}s"

    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type=resource_type,
        use_filename=True,
        unique_filename=True,
    )

    return {
        "file_url": result["secure_url"],
        "width": result.get("width"),
        "height": result.get("height"),
        "duration": result.get("duration"),
    }

ALL_ALLOWED_TYPES = set().union(
    ALLOWED_IMAGE_TYPES,
    ALLOWED_FILE_TYPES,
    ALLOWED_AUDIO_TYPES,
    ALLOWED_VIDEO_TYPES,
)
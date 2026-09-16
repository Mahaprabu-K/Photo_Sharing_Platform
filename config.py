import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:13122003@localhost:5432/photo_platform_db"
)

CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
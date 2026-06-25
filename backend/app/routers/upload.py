import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image and save it to the UPLOAD_DIR.
    Returns the URL path to the uploaded image.
    """
    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename while preserving the extension
    extension = ""
    if file.filename and "." in file.filename:
        extension = file.filename[file.filename.rindex(".") :]
    
    unique_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = upload_dir / unique_filename

    # Save the file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )
    finally:
        file.file.close()

    # The file will be accessible at /api/uploads/{filename} via StaticFiles
    return {"url": f"/api/uploads/{unique_filename}"}

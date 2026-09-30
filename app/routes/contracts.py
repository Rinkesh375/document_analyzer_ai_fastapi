from fastapi import APIRouter, UploadFile, File , HTTPException
import os
import uuid
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE,UPLOAD_DIR

router = APIRouter(prefix="/contracts", tags=["contacts"])


@router.post("/upload")
async def upload_contract(
    file:UploadFile = File(...)
):
    """
    Upload a PDF or TXT contract for analysis.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400,detail="File type not allowed")
    
    content = await file.read()
    
    size_mb = len(content) / (1024 * 1024)
    
    if size_mb > MAX_FILE_SIZE:
        raise HTTPException(status_code=400,detail="File size exceeds the maximum limit of file")
    
    os.makedirs(UPLOAD_DIR,exist_ok=True)
    
    unique_name = f"{uuid.uuid4().hex}{ext}"
    
    file_path = os.path.join(UPLOAD_DIR,unique_name)
    
    with open(file_path,"wb") as f:
        f.write(content)
    
    return {"message": "Contract uploaded successfully."}

from fastapi import APIRouter, UploadFile, File, HTTPException, status
import os
from uuid import uuid4
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR
from pathlib import Path
from service.document_parser import extract_text
from model import Contract
from database import contracts_collection

router = APIRouter(prefix="/contracts", tags=["contacts"])


# Convert MB → bytes once
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE * 1024 * 1024


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_contract(file: UploadFile = File(...)):
    """
    Upload a PDF or TXT contract for analysis.

    Validates the file type and size, then stores the file
    using a generated unique filename.
    """

    # --------------------------------------------------
    # 1. Validate that a file was actually provided
    # --------------------------------------------------
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was provided.",
        )

    # --------------------------------------------------
    # 2. Get and normalize the file extension
    # --------------------------------------------------
    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{extension or 'unknown'}' is not allowed. "
                f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # --------------------------------------------------
    # 3. Make sure upload directory exists
    # --------------------------------------------------
    upload_dir = Path(UPLOAD_DIR)

    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to prepare upload directory.",
        )

    # --------------------------------------------------
    # 4. Generate a unique filename
    # --------------------------------------------------
    unique_filename = f"{uuid4().hex}{extension}"
    file_path = upload_dir / unique_filename

    # --------------------------------------------------
    # 5. Stream file to disk instead of loading
    #    the entire file into memory
    # --------------------------------------------------
    total_size = 0
    chunk_size = 1024 * 1024  # 1 MB

    try:
        with file_path.open("wb") as output_file:

            while True:
                chunk = await file.read(chunk_size)

                if not chunk:
                    break

                total_size += len(chunk)

                # Check size while uploading
                if total_size > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"File size exceeds the maximum limit "
                            f"of {MAX_FILE_SIZE} MB."
                        ),
                    )

                output_file.write(chunk)

    except HTTPException:
        # Remove partially uploaded file
        if file_path.exists():
            file_path.unlink()

        raise

    except OSError:
        # Remove partially uploaded file if disk write fails
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save the uploaded file.",
        )

    finally:
        await file.close()

    parsed = extract_text(file_path)

    contract_data = Contract(
        filename=unique_filename,
        original_name=file.filename,
        text_content=parsed["text"] if isinstance(parsed, dict) else parsed,
        page_count=(
            len(parsed["page_count"].splitlines())
            if isinstance(parsed, dict)
            else len(parsed.splitlines())
        ),
        word_count=(
            len(parsed["word_count"].split())
            if isinstance(parsed, dict)
            else len(parsed.split())
        ),
    )

    doc = contract_data.model_dump()
    result = contracts_collection.insert_one(doc)
    contract_data.id = str(result.inserted_id)

    # --------------------------------------------------
    # 6. Return success response
    # --------------------------------------------------
    return {
        "message": "File uploaded and processed successfully",
        "contract": contract_data.model_dump(),
        "id": contract_data.id,
    }

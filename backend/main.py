import os
import uuid
from fastapi import Request
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from handlers import convert_txt, convert_docx, convert_pdf, convert_odt

# ==========================================
# SETUP & SANDBOX INITIALIZATION
# ==========================================

# Temporary sandbox directory strictly created INSIDE the workspace to comply with sandbox rules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SANDBOX_DIR = os.path.join(BASE_DIR, "temp_sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

# Rate limiter setup (5 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Nepali Unicode & Preeti Bidirectional Converter API",
    description="Decoupled backend API supporting TXT, DOCX, PDF, and ODT file conversion."
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration to connect decoupled frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),  # Use env variable for live URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# VALIDATION UTILITIES
# ==========================================

MAX_SIZE = 100 * 1024 * 1024  # 100 Megabytes size limit

SUPPORTED_EXTENSIONS = {
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
    ".odt": "application/vnd.oasis.opendocument.text"
}

def validate_magic_bytes(file_bytes: bytes, ext: str) -> bool:
    """
    Verifies that the file's binary magic bytes match the expected standard format signatures.
    """
    if ext == ".pdf":
        return file_bytes.startswith(b"%PDF")
    elif ext in [".docx", ".odt"]:
        # ZIP magic bytes signature
        return file_bytes.startswith(b"PK\x03\x04")
    elif ext == ".txt":
        # Make sure txt is not a binary file by verifying absence of null bytes in standard chunk
        return b"\x00" not in file_bytes[:1024]
    return False


def clean_sandbox_file(*paths):
    """
    Background worker that removes temporary sandboxed files after download completes.
    """
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"Cleanup: Safely deleted sandboxed temp file {os.path.basename(path)}")
        except Exception as e:
            print(f"Cleanup Error: Failed to remove sandboxed file {path}: {e}")


# ==========================================
# API CONVERT ROUTE
# ==========================================

@app.post("/api/convert")
@limiter.limit("5/minute")
async def convert_document(
    background_tasks: BackgroundTasks,
    request: Request = None,  # Required for slowapi limiter context mapping in FastAPI
    file: UploadFile = File(...),
    direction: str = Form(...)
):
    # 1. Validate Form Input Parameters
    if direction not in ["unicode_to_preeti", "preeti_to_unicode", "auto"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid conversion direction. Select either 'unicode_to_preeti', 'preeti_to_unicode', or 'auto'."
        )
        
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: '{ext}'. Supported types are: TXT, DOCX, PDF, and ODT."
        )

    # 2. Validate Size Limits (using spool read)
    # Read first chunk of bytes to verify magic bytes and size
    first_chunk = await file.read(2048)
    
    # Read remainder to compute exact size without loading whole file in memory
    size = len(first_chunk)
    while True:
        chunk = await file.read(65536)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the strict 100MB upload limit."
            )

    # Reset file cursor for saving
    await file.seek(0)
    
    # 3. Magic Bytes Validation
    if not validate_magic_bytes(first_chunk, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security signature check failed. The file magic bytes do not match standard '{ext}' headers."
        )

    # 4. Generate unique sandboxed temp paths inside the workspace temp_sandbox folder
    unique_id = str(uuid.uuid4())
    input_temp_path = os.path.join(SANDBOX_DIR, f"{unique_id}_input{ext}")
    output_temp_path = os.path.join(SANDBOX_DIR, f"{unique_id}_output{ext}")

    try:
        # Save uploaded file to sandbox
        with open(input_temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 5. Route upload to format-specific handler
        if ext == ".txt":
            convert_txt(input_temp_path, output_temp_path, direction)
        elif ext == ".docx":
            convert_docx(input_temp_path, output_temp_path, direction)
        elif ext == ".odt":
            convert_odt(input_temp_path, output_temp_path, direction)
        elif ext == ".pdf":
            convert_pdf(input_temp_path, output_temp_path, direction)
            
    except Exception as e:
        # Cleanup input immediately if conversion crashes before returning FileResponse
        clean_sandbox_file(input_temp_path, output_temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion error during processing: {str(e)}"
        )

    # 6. Stream file response back to user and schedule auto cleanup task
    download_filename = f"converted_{filename}"
    background_tasks.add_task(clean_sandbox_file, input_temp_path, output_temp_path)
    
    return FileResponse(
        path=output_temp_path,
        media_type="application/octet-stream",
        filename=download_filename,
        headers={"Content-Disposition": f"attachment; filename={download_filename}"}
    )

# Fix slowapi integration for request mapping parameter
# slowapi requires the Request object to be present in endpoints if we want to rate limit them.
# We modify FastAPI routing behavior or pass request parameter correctly.
from fastapi import Request
@app.middleware("http")
async def add_request_to_state(request: Request, call_next):
    # This middleware makes request objects globally visible for slowapi key resolving
    request.state.limiter = limiter
    response = await call_next(request)
    return response

"""
FastAPI web application for RAFT toolkit.
"""
import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from core.config import RaftConfig, get_config
from core.raft_engine import RaftEngine
from core.models import DocType, OutputFormat, OutputType, ChunkingStrategy

logger = logging.getLogger(__name__)

# Pydantic models for API
class ProcessingRequest(BaseModel):
    """Request model for dataset processing."""
    # I/O Configuration
    output_format: OutputFormat = "hf"
    output_type: OutputType = "jsonl"
    output_chat_system_prompt: Optional[str] = None
    output_completion_prompt_column: str = "prompt"
    output_completion_completion_column: str = "completion"
    
    # Processing Configuration
    distractors: int = Field(1, ge=0, le=10)
    p: float = Field(1.0, ge=0.0, le=1.0)
    questions: int = Field(5, ge=1, le=20)
    chunk_size: int = Field(512, ge=100, le=2048)
    doctype: DocType = "pdf"
    chunking_strategy: ChunkingStrategy = "semantic"
    chunking_params: Dict[str, Any] = Field(default_factory=dict)
    
    # AI Model Configuration
    completion_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"
    system_prompt_key: str = "gpt"
    
    # Performance Configuration
    workers: int = Field(1, ge=1, le=8)
    embed_workers: int = Field(1, ge=1, le=4)
    pace: bool = True

class ProcessingResponse(BaseModel):
    """Response model for dataset processing."""
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    """Job status model."""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    message: str = ""
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PreviewResponse(BaseModel):
    """Preview response model."""
    files_to_process: List[str]
    estimated_chunks: int
    estimated_qa_points: int
    doctype: str

# Global job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}

def get_raft_config() -> RaftConfig:
    """Dependency to get RAFT configuration."""
    return get_config()

# Create FastAPI app
app = FastAPI(
    title="RAFT Toolkit Web UI",
    description="Web interface for Retrieval Augmentation Fine-Tuning dataset generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint for containers."""
    return {"status": "healthy", "service": "raft-toolkit"}

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main UI."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    
    # Fallback basic HTML if file doesn't exist
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAFT Toolkit</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 40px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .status { margin-top: 20px; padding: 10px; border-radius: 4px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 RAFT Toolkit</h1>
                <p>Generate fine-tuning datasets with Retrieval Augmentation</p>
            </div>
            <div id="app">
                <p>The web UI is starting up. Please check the static files or use the API endpoints directly.</p>
                <p>API Documentation: <a href="/docs">/docs</a></p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/api/upload", response_model=Dict[str, str])
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing."""
    try:
        # Create temp directory for uploads
        upload_dir = Path(tempfile.gettempdir()) / "raft_uploads"
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "size": len(content)
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/preview", response_model=PreviewResponse)
async def get_preview(
    file_path: str,
    doctype: DocType,
    chunk_size: int = 512,
    questions: int = 5,
    config: RaftConfig = Depends(get_raft_config)
):
    """Get a preview of what would be processed."""
    try:
        # Override config with request parameters
        config.doctype = doctype
        config.chunk_size = chunk_size
        config.questions = questions
        
        engine = RaftEngine(config)
        preview = engine.get_processing_preview(Path(file_path))
        
        return PreviewResponse(
            files_to_process=preview['files_to_process'],
            estimated_chunks=preview['estimated_chunks'],
            estimated_qa_points=preview['estimated_qa_points'],
            doctype=preview['doctype']
        )
    
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/process", response_model=ProcessingResponse)
async def start_processing(
    request: ProcessingRequest,
    file_path: str,
    background_tasks: BackgroundTasks,
    config: RaftConfig = Depends(get_raft_config)
):
    """Start dataset processing."""
    try:
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Override config with request parameters
        config.doctype = request.doctype
        config.output_format = request.output_format
        config.output_type = request.output_type
        config.output_chat_system_prompt = request.output_chat_system_prompt
        config.output_completion_prompt_column = request.output_completion_prompt_column
        config.output_completion_completion_column = request.output_completion_completion_column
        config.distractors = request.distractors
        config.p = request.p
        config.questions = request.questions
        config.chunk_size = request.chunk_size
        config.chunking_strategy = request.chunking_strategy
        config.chunking_params = request.chunking_params
        config.completion_model = request.completion_model
        config.embedding_model = request.embedding_model
        config.system_prompt_key = request.system_prompt_key
        config.workers = request.workers
        config.embed_workers = request.embed_workers
        config.pace = request.pace
        
        # Set output path
        output_dir = Path(tempfile.gettempdir()) / "raft_outputs"
        output_dir.mkdir(exist_ok=True)
        config.output = str(output_dir / job_id)
        
        # Initialize job status
        jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Job queued for processing",
            "config": config,
            "file_path": file_path,
            "stats": None,
            "error": None
        }
        
        # Start background processing
        background_tasks.add_task(process_dataset_background, job_id)
        
        return ProcessingResponse(
            job_id=job_id,
            status="pending",
            message="Processing started"
        )
    
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

async def process_dataset_background(job_id: str):
    """Background task for dataset processing."""
    try:
        job = jobs[job_id]
        job["status"] = "processing"
        job["message"] = "Initializing processing..."
        
        config: RaftConfig = job["config"]
        file_path = Path(job["file_path"])
        
        # Create engine and process
        engine = RaftEngine(config)
        
        # Update progress
        job["progress"] = 0.1
        job["message"] = "Validating inputs..."
        
        engine.validate_inputs(file_path)
        
        job["progress"] = 0.2
        job["message"] = "Starting dataset generation..."
        
        # Generate dataset
        stats = engine.generate_dataset(file_path, config.output)
        
        # Mark as completed
        job["status"] = "completed"
        job["progress"] = 1.0
        job["message"] = f"Generated {stats['total_qa_points']} QA data points"
        job["stats"] = stats
        
    except Exception as e:
        logger.error(f"Error in background processing for job {job_id}: {e}")
        job = jobs.get(job_id, {})
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Processing failed: {str(e)}"

@app.get("/api/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        stats=job.get("stats"),
        error=job.get("error")
    )

@app.get("/api/jobs/{job_id}/download")
async def download_result(job_id: str):
    """Download processing result."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    config: RaftConfig = job["config"]
    output_path = Path(config.output)
    
    # Return the main output file
    if config.output_type == "jsonl":
        result_file = output_path.with_suffix(".jsonl")
    else:
        result_file = output_path.with_suffix(".parquet")
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        result_file,
        filename=f"raft_dataset_{job_id}.{config.output_type}",
        media_type="application/octet-stream"
    )

@app.get("/api/jobs", response_model=List[JobStatus])
async def list_jobs():
    """List all jobs."""
    return [
        JobStatus(
            job_id=job_id,
            status=job["status"],
            progress=job["progress"],
            message=job["message"],
            stats=job.get("stats"),
            error=job.get("error")
        )
        for job_id, job in jobs.items()
    ]

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its files."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    config: RaftConfig = job["config"]
    
    # Clean up output files
    try:
        output_path = Path(config.output)
        if output_path.exists():
            if output_path.is_dir():
                import shutil
                shutil.rmtree(output_path)
            else:
                output_path.unlink()
    except Exception as e:
        logger.warning(f"Error cleaning up files for job {job_id}: {e}")
    
    # Remove from jobs
    del jobs[job_id]
    
    return {"message": "Job deleted"}

def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    return app

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the web server."""
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server(reload=True)
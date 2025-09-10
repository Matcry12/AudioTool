#!/usr/bin/env python3
"""
Text-to-Speech API Server
RESTful API for converting text to speech using Edge TTS.
Compatible with Python 3.13+

Requirements:
    pip install fastapi uvicorn edge-tts

Run:
    python tts_api.py
    # or for production:
    uvicorn tts_api:app --host 0.0.0.0 --port 8000 --workers 4

API Documentation:
    http://localhost:8000/docs (interactive)
    http://localhost:8000/redoc (alternative)

Quick Example:
    # Start conversion
    curl -X POST http://localhost:8000/convert \
      -H "Content-Type: application/json" \
      -d '{"text": "Hello world", "voice": "en-US-JennyNeural"}'
    
    # Check status  
    curl http://localhost:8000/status/{task_id}
    
    # Download result
    curl -O http://localhost:8000/download/{task_id}/audio_001.mp3
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
import edge_tts
import re
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store conversion tasks
conversion_tasks: Dict[str, Dict[str, Any]] = {}

# Lifespan manager for cleanup
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup
    yield
    # Cleanup tasks on shutdown
    for task_id in list(conversion_tasks.keys()):
        if conversion_tasks[task_id]["status"] == "processing":
            conversion_tasks[task_id]["status"] = "cancelled"

app = FastAPI(
    title="TTS Converter API",
    description="""
    Convert text to high-quality audio using Edge TTS.
    
    ## Features
    - Multiple language support (English, Vietnamese)
    - Automatic text chunking for long content
    - Background processing with progress tracking
    - Optional audio merging with ffmpeg
    - RESTful API with async support
    
    ## Quick Start
    1. Install: `pip install fastapi uvicorn edge-tts`
    2. Run: `python tts_api.py`
    3. Open: http://localhost:8000/docs
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Request models
class ConversionRequest(BaseModel):
    text: str = Field(..., description="Text content to convert")
    voice: str = Field("en-US-JennyNeural", description="TTS voice to use")
    output_prefix: str = Field("audio", description="Prefix for output files")
    chunk_size_min: int = Field(1500, description="Minimum chunk size", ge=500, le=5000)
    chunk_size_max: int = Field(2000, description="Maximum chunk size", ge=500, le=5000)
    merge_chunks: bool = Field(True, description="Merge chunks with ffmpeg if available")
    keep_chunks: bool = Field(True, description="Keep individual chunk files")
    rate: str = Field("+0%", description="Speech rate adjustment")
    pitch: str = Field("+0Hz", description="Speech pitch adjustment")
    volume: str = Field("+0%", description="Speech volume adjustment")

    @field_validator('chunk_size_max')
    @classmethod
    def validate_chunk_sizes(cls, v: int, info):
        if info.data.get('chunk_size_min') and v < info.data['chunk_size_min']:
            raise ValueError('chunk_size_max must be >= chunk_size_min')
        return v

class ConversionResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Configuration
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Available voices
VOICES = {
    "en-US-JennyNeural": "English (US) - Female",
    "en-US-GuyNeural": "English (US) - Male", 
    "en-GB-SoniaNeural": "English (UK) - Female",
    "en-GB-RyanNeural": "English (UK) - Male",
    "en-AU-NatashaNeural": "English (Australian) - Female",
    "en-AU-WilliamNeural": "English (Australian) - Male",
    "vi-VN-HoaiMyNeural": "Vietnamese - Female",
    "vi-VN-NamMinhNeural": "Vietnamese - Male"
}

class TTSConverterAPI:
    """API-compatible TTS converter."""
    
    def __init__(self, task_id: str, output_folder: Path):
        self.task_id = task_id
        self.output_folder = output_folder
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
    async def update_progress(self, message: str, progress: Optional[float] = None):
        """Update task progress."""
        if self.task_id in conversion_tasks:
            conversion_tasks[self.task_id]["message"] = message
            conversion_tasks[self.task_id]["updated_at"] = datetime.now().isoformat()
            if progress is not None:
                conversion_tasks[self.task_id]["progress"] = progress
    
    def split_text_into_chunks(self, text: str, chunk_min: int, chunk_max: int) -> List[str]:
        """Split text into chunks respecting sentence boundaries."""
        chunks = []
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            target_end = min(current_pos + chunk_max, text_length)
            
            if target_end == text_length:
                chunk = text[current_pos:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            search_start = current_pos + chunk_min
            search_text = text[search_start:target_end]
            
            sentence_endings = list(re.finditer(r'[.!?]\s+', search_text))
            
            if sentence_endings:
                last_ending = sentence_endings[-1]
                actual_end = search_start + last_ending.end()
            else:
                break_patterns = [r'\n\s*\n', r',\s+', r'\s+']
                actual_end = None
                
                for pattern in break_patterns:
                    breaks = list(re.finditer(pattern, search_text))
                    if breaks:
                        last_break = breaks[-1]
                        actual_end = search_start + last_break.end()
                        break
                
                if actual_end is None:
                    actual_end = target_end
            
            chunk = text[current_pos:actual_end].strip()
            if chunk:
                chunks.append(chunk)
            
            current_pos = actual_end
        
        return chunks
    
    async def generate_chunk_audio(self, chunk_text: str, chunk_num: int, prefix: str, 
                                 voice: str, rate: str, pitch: str, volume: str) -> Path:
        """Generate MP3 audio for a single chunk."""
        output_filename = f"{prefix}_{chunk_num:03d}.mp3"
        output_path = self.output_folder / output_filename
        
        try:
            communicate = edge_tts.Communicate(
                text=chunk_text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            
            with output_path.open("wb") as f:
                async for chunk in communicate.stream():
                    chunk_type = chunk.get("type")
                    if chunk_type == "audio":
                        f.write(chunk["data"])
            
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise RuntimeError(f"Failed to generate audio file: {output_filename}")
            
            return output_path
            
        except Exception as e:
            if output_path.exists():
                output_path.unlink()
            raise RuntimeError(f"TTS generation failed for chunk {chunk_num}: {e}")
    
    async def merge_with_ffmpeg(self, chunk_files: List[Path], output_prefix: str, keep_chunks: bool) -> Optional[Path]:
        """Merge audio files using ffmpeg if available."""
        output_path = self.output_folder / f"{output_prefix}_merged.mp3"
        
        try:
            # Check if ffmpeg is available
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode != 0:
                return None
            
            # Create input file list
            list_file = self.output_folder / "chunk_list.txt"
            with open(list_file, 'w') as f:
                for chunk_file in chunk_files:
                    f.write(f"file '{chunk_file.name}'\n")
            
            # Run ffmpeg
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(list_file), '-c', 'copy',
                str(output_path), '-y',
                cwd=self.output_folder,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            list_file.unlink()
            
            if process.returncode == 0 and output_path.exists():
                # Delete chunks if requested
                if not keep_chunks:
                    for chunk_file in chunk_files:
                        try:
                            chunk_file.unlink()
                        except Exception:
                            pass
                return output_path
            
        except Exception:
            pass
        
        return None
    
    async def convert(self, text: str, voice: str, output_prefix: str,
                     chunk_min: int, chunk_max: int, merge_chunks: bool,
                     keep_chunks: bool, rate: str, pitch: str, volume: str) -> Dict[str, Any]:
        """Perform the actual conversion."""
        try:
            await self.update_progress("Splitting text into chunks...", 0.1)
            chunks = self.split_text_into_chunks(text, chunk_min, chunk_max)
            
            if not chunks:
                raise ValueError("No valid chunks created from text")
            
            await self.update_progress(f"Generating {len(chunks)} audio chunks...", 0.2)
            
            # Generate chunks with concurrent limit
            chunk_files = []
            semaphore = asyncio.Semaphore(3)  # Limit concurrent generations
            
            async def generate_with_progress(chunk: str, index: int):
                async with semaphore:
                    progress = 0.2 + (0.6 * index / len(chunks))
                    await self.update_progress(f"Generating chunk {index}/{len(chunks)}...", progress)
                    return await self.generate_chunk_audio(chunk, index, output_prefix, 
                                                          voice, rate, pitch, volume)
            
            tasks = [generate_with_progress(chunk, i+1) for i, chunk in enumerate(chunks)]
            chunk_files = await asyncio.gather(*tasks)
            
            result = {
                "chunks": [str(f) for f in chunk_files],
                "chunk_count": len(chunk_files),
                "output_folder": str(self.output_folder)
            }
            
            # Try to merge if requested
            if merge_chunks and chunk_files:
                await self.update_progress("Merging chunks...", 0.9)
                merged_file = await self.merge_with_ffmpeg(chunk_files, output_prefix, keep_chunks)
                if merged_file:
                    result["merged_file"] = str(merged_file)
            
            await self.update_progress("Conversion completed!", 1.0)
            return result
            
        except Exception as e:
            await self.update_progress(f"Error: {str(e)}", None)
            raise

# API Endpoints
@app.get("/", tags=["Info"])
async def root():
    """API information endpoint."""
    return {
        "name": "TTS Converter API",
        "version": "1.0.0",
        "description": "Convert text to speech using Edge TTS",
        "documentation": "/docs",
        "endpoints": {
            "POST /convert": "Start a new conversion",
            "GET /status/{task_id}": "Check conversion status",
            "GET /download/{task_id}/{filename}": "Download converted file",
            "GET /voices": "List available voices",
            "GET /tasks": "List all tasks",
            "DELETE /tasks/{task_id}": "Delete a task"
        }
    }

@app.get("/voices", tags=["Info"])
async def get_voices():
    """
    Get list of available TTS voices.
    
    Returns voices grouped by language with their codes and descriptions.
    """
    return {
        "voices": [
            {"code": code, "name": name}
            for code, name in VOICES.items()
        ]
    }

@app.post("/convert", response_model=ConversionResponse, tags=["Conversion"])
async def convert_text(request: ConversionRequest, background_tasks: BackgroundTasks):
    """
    Start a new text-to-speech conversion.
    
    The conversion runs asynchronously. Use the returned task_id to check progress.
    """
    # Validate voice
    if request.voice not in VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice. Available voices: {list(VOICES.keys())}")
    
    # Create task
    task_id = str(uuid.uuid4())
    output_folder = OUTPUT_DIR / task_id
    
    conversion_tasks[task_id] = {
        "task_id": task_id,
        "status": "processing",
        "progress": 0.0,
        "message": "Starting conversion...",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": None,
        "error": None
    }
    
    # Run conversion in background
    async def run_conversion():
        converter = TTSConverterAPI(task_id, output_folder)
        try:
            result = await converter.convert(
                text=request.text,
                voice=request.voice,
                output_prefix=request.output_prefix,
                chunk_min=request.chunk_size_min,
                chunk_max=request.chunk_size_max,
                merge_chunks=request.merge_chunks,
                keep_chunks=request.keep_chunks,
                rate=request.rate,
                pitch=request.pitch,
                volume=request.volume
            )
            conversion_tasks[task_id]["status"] = "completed"
            conversion_tasks[task_id]["result"] = result
            conversion_tasks[task_id]["progress"] = 1.0
        except Exception as e:
            conversion_tasks[task_id]["status"] = "failed"
            conversion_tasks[task_id]["error"] = str(e)
            logger.error(f"Conversion failed for task {task_id}: {e}")
    
    background_tasks.add_task(run_conversion)
    
    return ConversionResponse(
        task_id=task_id,
        status="processing",
        message="Conversion started successfully"
    )

@app.get("/status/{task_id}", response_model=TaskStatusResponse, tags=["Tasks"])
async def get_task_status(task_id: str):
    """
    Get status of a conversion task.
    
    Returns current progress, status, and result files when completed.
    """
    if task_id not in conversion_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(**conversion_tasks[task_id])

@app.get("/tasks", tags=["Tasks"])
async def list_tasks():
    """
    List all conversion tasks.
    
    Returns a summary of all tasks with their current status.
    """
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "created_at": task["created_at"],
                "message": task.get("message", "")
            }
            for task_id, task in conversion_tasks.items()
        ]
    }

@app.get("/download/{task_id}/{filename}", tags=["Download"])
async def download_file(task_id: str, filename: str):
    """
    Download a converted audio file.
    
    Use filenames from the task result to download individual chunks or merged file.
    """
    if task_id not in conversion_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = conversion_tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    file_path = OUTPUT_DIR / task_id / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check - ensure file is within task directory
    try:
        file_path.resolve().relative_to(OUTPUT_DIR / task_id)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )

@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(task_id: str):
    """
    Delete a task and its files.
    
    Removes the task from memory and deletes all associated audio files.
    """
    if task_id not in conversion_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Delete files
    output_folder = OUTPUT_DIR / task_id
    if output_folder.exists():
        import shutil
        shutil.rmtree(output_folder)
    
    # Remove from tasks
    del conversion_tasks[task_id]
    
    return {"message": "Task deleted successfully"}

# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("TTS Converter API")
    print("="*50)
    print("\nStarting server...")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Alternative docs: http://localhost:8000/redoc")
    print("\nExample usage:")
    print('  curl -X POST http://localhost:8000/convert -H "Content-Type: application/json" -d \'{"text": "Hello world"}\'')
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
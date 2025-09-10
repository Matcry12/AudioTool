# TTS API Tutorial for AI Systems

## Overview
This tutorial teaches AI systems how to interact with the Text-to-Speech (TTS) API to convert text into audio files. The API uses asynchronous processing for efficient handling of long texts.

## Core Concepts

### 1. API Architecture
- **REST API**: HTTP-based communication using JSON
- **Asynchronous**: Conversions run in background, check status separately
- **Task-based**: Each conversion gets a unique task_id for tracking
- **File-based Output**: Audio files are generated and stored on server

### 2. Workflow Pattern
```
[Text Input] → [Create Task] → [Monitor Progress] → [Download Audio]
```

## Step-by-Step Usage Guide

### Step 1: Start the API Server
```bash
# Install dependencies
pip install fastapi uvicorn edge-tts

# Run server
python tts_api.py
```

### Step 2: Create a Conversion Task

**Endpoint**: `POST /convert`

**Request Format**:
```json
{
  "text": "The text you want to convert to speech",
  "voice": "en-US-JennyNeural",
  "output_prefix": "my_audio",
  "chunk_size_min": 1500,
  "chunk_size_max": 2000,
  "merge_chunks": true,
  "keep_chunks": true,
  "rate": "+0%",
  "pitch": "+0Hz",
  "volume": "+0%"
}
```

**Parameters Explained**:
- `text` (required): The input text to convert
- `voice` (optional): TTS voice selection (default: "en-US-JennyNeural")
- `output_prefix` (optional): Filename prefix (default: "audio")
- `chunk_size_min/max` (optional): Text splitting boundaries (default: 1500-2000 chars)
- `merge_chunks` (optional): Combine chunks into single file (default: true)
- `keep_chunks` (optional): Retain individual chunk files (default: true)
- `rate/pitch/volume` (optional): Voice modulation (default: "+0%" for all)

**Response Format**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Conversion started successfully"
}
```

### Step 3: Monitor Task Progress

**Endpoint**: `GET /status/{task_id}`

**Response States**:

1. **Processing** (task running):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0.45,
  "message": "Generating chunk 3/5...",
  "created_at": "2024-01-10T12:00:00",
  "updated_at": "2024-01-10T12:00:15"
}
```

2. **Completed** (success):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "message": "Conversion completed!",
  "result": {
    "chunks": [
      "output/550e8400/my_audio_001.mp3",
      "output/550e8400/my_audio_002.mp3"
    ],
    "chunk_count": 2,
    "output_folder": "output/550e8400",
    "merged_file": "output/550e8400/my_audio_merged.mp3"
  }
}
```

3. **Failed** (error):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "Invalid voice specified"
}
```

### Step 4: Download Audio Files

**Endpoint**: `GET /download/{task_id}/{filename}`

Extract filename from the result:
- Use `merged_file` for single combined audio
- Use items from `chunks` array for individual parts

Example:
```
GET /download/550e8400-e29b-41d4-a716-446655440000/my_audio_merged.mp3
```

## Complete Python Example for AI

```python
import requests
import time
import json

class TTSAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def convert_text(self, text, voice="en-US-JennyNeural", wait_for_completion=True):
        """Convert text to speech and optionally wait for completion."""
        
        # Step 1: Start conversion
        response = requests.post(
            f"{self.base_url}/convert",
            json={
                "text": text,
                "voice": voice,
                "merge_chunks": True
            }
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to start conversion: {response.text}"}
        
        task = response.json()
        task_id = task["task_id"]
        
        if not wait_for_completion:
            return task
        
        # Step 2: Monitor progress
        while True:
            status_response = requests.get(f"{self.base_url}/status/{task_id}")
            if status_response.status_code != 200:
                return {"error": f"Failed to check status: {status_response.text}"}
            
            status = status_response.json()
            
            if status["status"] == "completed":
                return {
                    "success": True,
                    "task_id": task_id,
                    "files": status["result"]
                }
            elif status["status"] == "failed":
                return {
                    "error": status.get("error", "Unknown error"),
                    "task_id": task_id
                }
            
            time.sleep(1)  # Wait before next check
    
    def download_audio(self, task_id, filename, output_path):
        """Download audio file from completed task."""
        response = requests.get(
            f"{self.base_url}/download/{task_id}/{filename}",
            stream=True
        )
        
        if response.status_code != 200:
            return False
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True

# Usage example
client = TTSAPIClient()
result = client.convert_text("Hello, this is a test.", "en-US-JennyNeural")

if "success" in result:
    # Download merged file
    if "merged_file" in result["files"]:
        filename = result["files"]["merged_file"].split("/")[-1]
        client.download_audio(result["task_id"], filename, "output.mp3")
```

## Available Voices

### English Voices
- `en-US-JennyNeural` - US Female (default)
- `en-US-GuyNeural` - US Male
- `en-GB-SoniaNeural` - UK Female
- `en-GB-RyanNeural` - UK Male
- `en-AU-NatashaNeural` - Australian Female
- `en-AU-WilliamNeural` - Australian Male

### Vietnamese Voices
- `vi-VN-HoaiMyNeural` - Female
- `vi-VN-NamMinhNeural` - Male

## API Best Practices for AI

### 1. Error Handling
Always check response status codes:
- `200`: Success
- `400`: Invalid request (check parameters)
- `404`: Resource not found
- `500`: Server error

### 2. Polling Strategy
When checking task status:
- Poll every 1-2 seconds for short texts
- Poll every 5-10 seconds for long texts
- Implement exponential backoff for very long tasks

### 3. Resource Management
- Delete completed tasks after downloading: `DELETE /tasks/{task_id}`
- Don't create duplicate tasks for same text
- Implement retry logic for network failures

### 4. Text Preparation
- Remove excessive whitespace
- Ensure text encoding is UTF-8
- Split very long texts (>50k chars) into multiple requests

## Common Integration Patterns

### Pattern 1: Simple Conversion
```python
def simple_tts(text):
    # Create task
    task = create_conversion(text)
    # Wait for completion
    wait_for_task(task["task_id"])
    # Download result
    return download_merged_file(task["task_id"])
```

### Pattern 2: Batch Processing
```python
def batch_tts(texts):
    # Start all conversions
    tasks = [create_conversion(text) for text in texts]
    # Monitor all tasks
    results = [wait_for_task(t["task_id"]) for t in tasks]
    # Download all results
    return [download_merged_file(r["task_id"]) for r in results]
```

### Pattern 3: Streaming Integration
```python
def stream_tts(text_generator):
    for text in text_generator:
        task = create_conversion(text)
        yield wait_and_download(task["task_id"])
```

## Troubleshooting Guide

### Issue: Task stays in "processing" forever
- Check if text is extremely long
- Verify API server is still running
- Check server logs for errors

### Issue: "File not found" when downloading
- Ensure task status is "completed"
- Use exact filename from result
- Check if task was deleted

### Issue: Poor audio quality
- Try different voice options
- Adjust rate/pitch parameters
- Check input text formatting

## Performance Considerations

1. **Chunk Size Impact**:
   - Smaller chunks (1000-1500): Faster processing, more files
   - Larger chunks (2000-2500): Fewer files, may take longer

2. **Concurrent Requests**:
   - API handles multiple conversions simultaneously
   - Default limit: 3 concurrent chunk generations per task

3. **File Storage**:
   - Files stored in `output/{task_id}/` directory
   - Implement cleanup strategy for old files

## Security Notes

1. **Input Validation**: API validates all inputs
2. **Path Traversal**: Protected against directory access attacks
3. **Resource Limits**: Implement rate limiting in production

## Testing the API

### Quick Test Command
```bash
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message", "voice": "en-US-JennyNeural"}'
```

### Full Integration Test
```python
def test_api_integration():
    # Test 1: Simple conversion
    result = convert_text("Hello world")
    assert result["success"] == True
    
    # Test 2: Voice selection
    result = convert_text("Bonjour", voice="fr-FR-DeniseNeural")
    assert "task_id" in result
    
    # Test 3: Error handling
    result = convert_text("Test", voice="invalid-voice")
    assert "error" in result
    
    # Test 4: File download
    task = convert_text("Download test")
    files = download_all_files(task["task_id"])
    assert len(files) > 0
```

## Summary

This TTS API provides:
1. Asynchronous text-to-speech conversion
2. Multiple voice options
3. Automatic text chunking
4. Progress tracking
5. File download capabilities

For AI integration, focus on:
1. Creating conversion tasks
2. Monitoring progress
3. Downloading results
4. Proper error handling

The API is designed for ease of use while handling complex conversions efficiently.
#!/usr/bin/env python3
"""
Simple TTS with SRT Support
Test adding SRT generation to the existing TTS converter.
"""

import asyncio
import edge_tts
from pathlib import Path


class CustomSRTMaker:
    """Custom SRT maker that works with SentenceBoundary events."""
    
    def __init__(self):
        self.cues = []
        self.cue_index = 1
    
    def feed_sentence(self, sentence_chunk):
        """Feed a SentenceBoundary event to create SRT cue."""
        if sentence_chunk["type"] != "SentenceBoundary":
            return
        
        # Convert offset and duration from ticks to seconds
        start_ms = sentence_chunk["offset"] / 10000
        duration_ms = sentence_chunk["duration"] / 10000
        end_ms = start_ms + duration_ms
        
        # Convert to SRT time format
        start_time = self._ms_to_srt_time(start_ms)
        end_time = self._ms_to_srt_time(end_ms)
        
        # Create SRT cue
        cue = {
            'index': self.cue_index,
            'start': start_time,
            'end': end_time,
            'text': sentence_chunk.get('text', '').strip()
        }
        
        if cue['text']:
            self.cues.append(cue)
            self.cue_index += 1
    
    def _ms_to_srt_time(self, milliseconds):
        """Convert milliseconds to SRT time format."""
        hours = int(milliseconds // 3600000)
        minutes = int((milliseconds % 3600000) // 60000)
        seconds = int((milliseconds % 60000) // 1000)
        ms = int(milliseconds % 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
    
    def get_srt(self):
        """Generate SRT format string."""
        if not self.cues:
            return ""
        
        srt_lines = []
        for cue in self.cues:
            srt_lines.append(str(cue['index']))
            srt_lines.append(f"{cue['start']} --> {cue['end']}")
            srt_lines.append(cue['text'])
            srt_lines.append("")
        
        return "\n".join(srt_lines)


async def generate_chunk_with_srt(text, voice, chunk_num, prefix="story"):
    """Generate a single audio chunk with optional SRT."""
    
    output_dir = Path("C:/Users/fdtyw/Documents/TTS/Output")
    output_dir.mkdir(exist_ok=True)
    
    audio_file = output_dir / f"{prefix}_chunk_{chunk_num:03d}.mp3"
    srt_file = output_dir / f"{prefix}_chunk_{chunk_num:03d}.srt"
    
    print(f"Generating chunk {chunk_num}: {text[:50]}...")
    
    # Create communicate and SRT maker
    communicate = edge_tts.Communicate(text, voice)
    srt_maker = CustomSRTMaker()
    
    # Generate audio and collect subtitle events
    with open(audio_file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                srt_maker.feed_sentence(chunk)
    
    # Generate SRT file
    srt_content = srt_maker.get_srt()
    if srt_content:
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"Generated: {audio_file.name} + {srt_file.name} ({len(srt_maker.cues)} subtitles)")
    else:
        print(f"Generated: {audio_file.name} (no subtitles)")
    
    return str(audio_file), str(srt_file) if srt_content else None


async def main():
    """Test the SRT generation with sample chunks."""
    
    # Sample text chunks (like from your TTS converter)
    chunks = [
        "Hello everyone. This is the first part of our story. It contains multiple sentences for testing subtitle generation.",
        "Now we continue with the second chunk. This part has different timing. We want to see how the subtitles align with the audio.",
        "Finally, here is the third and final chunk. The subtitle timing should be accurate. This completes our test story."
    ]
    
    voice = "en-US-JennyNeural"
    prefix = "test_with_srt"
    
    print(f"Testing SRT generation with {len(chunks)} chunks")
    print(f"Voice: {voice}")
    print("=" * 50)
    
    results = []
    
    for i, chunk_text in enumerate(chunks, 1):
        try:
            audio_file, srt_file = await generate_chunk_with_srt(chunk_text, voice, i, prefix)
            results.append((audio_file, srt_file))
        except Exception as e:
            print(f"Error generating chunk {i}: {e}")
    
    print("=" * 50)
    print(f"Completed: {len(results)} chunks processed")
    
    # Show results
    for i, (audio_file, srt_file) in enumerate(results, 1):
        print(f"Chunk {i}: {Path(audio_file).name}")
        if srt_file:
            print(f"         {Path(srt_file).name}")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        print(f"\nSuccess! Generated {len(results)} audio+subtitle pairs")
    except Exception as e:
        print(f"Error: {e}")

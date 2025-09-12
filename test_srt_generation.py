#!/usr/bin/env python3
"""
Test SRT Generation with Edge TTS
Test script to verify subtitle generation works correctly.
"""

import asyncio
import edge_tts
from pathlib import Path


async def test_srt_generation():
    """Test SRT subtitle generation with Edge TTS."""
    
    text = "Hello everyone. This is a test subtitle file created with Edge TTS. We can generate both audio and subtitles at the same time."
    voice = "en-US-JennyNeural"
    
    print("Testing SRT generation with Edge TTS...")
    print(f"Text: {text}")
    print(f"Voice: {voice}")
    print("=" * 50)
    
    # Create communicate object
    communicate = edge_tts.Communicate(text, voice)
    sub_maker = edge_tts.SubMaker()
    
    # Save audio and collect subtitle events
    output_dir = Path("C:/Users/fdtyw/Documents/TTS")
    audio_file = output_dir / "test_srt_output.mp3"
    srt_file = output_dir / "test_srt_output.srt"
    
    print("Generating audio and collecting subtitle events...")
    
    word_boundary_count = 0
    audio_chunk_count = 0
    
    with open(audio_file, "wb") as f:
        async for chunk in communicate.stream():
            print(f"Received chunk type: {chunk.get('type')}")  # Debug
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                audio_chunk_count += 1
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(chunk)
                word_boundary_count += 1
                print(f"WordBoundary: {chunk}")  # Debug
    
    print(f"Audio chunks received: {audio_chunk_count}")
    print(f"WordBoundary events received: {word_boundary_count}")
    
    # Generate SRT content using the correct method
    try:
        srt_content = sub_maker.get_srt()  # This is the correct method
        print(f"OK SRT content generated ({len(srt_content)} characters)")
    except AttributeError:
        # Try alternative method names in case of version differences
        try:
            srt_content = sub_maker.generate_srt()
            print("OK SRT content generated with generate_srt() method")
        except AttributeError:
            try:
                srt_content = str(sub_maker)
                print("OK SRT content generated with __str__() method")
            except Exception as e:
                print(f"FAIL Failed to generate SRT: {e}")
                return False
    
    # Write subtitles
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    print(f"OK Audio saved: {audio_file}")
    print(f"OK Subtitles saved: {srt_file}")
    
    # Show sample of SRT content
    print("\nSample SRT content:")
    print("=" * 30)
    lines = srt_content.split('\n')[:15]  # First 15 lines
    for line in lines:
        print(line)
    if len(srt_content.split('\n')) > 15:
        print("... (truncated)")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_srt_generation())
        if success:
            print("\nSUCCESS SRT generation test completed successfully!")
        else:
            print("\nFAIL SRT generation test failed!")
    except Exception as e:
        print(f"\nERROR Test error: {e}")

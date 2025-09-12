#!/usr/bin/env python3
"""
Custom SRT Generator for Edge TTS
Creates SRT files from SentenceBoundary events when WordBoundary events are not available.
"""

import asyncio
import edge_tts
from pathlib import Path
from datetime import timedelta


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
        # Edge TTS uses 10,000 ticks per millisecond
        start_ms = sentence_chunk["offset"] / 10000  # Convert to milliseconds
        duration_ms = sentence_chunk["duration"] / 10000  # Convert to milliseconds
        end_ms = start_ms + duration_ms
        
        # Convert to SRT time format (HH:MM:SS,mmm)
        start_time = self._ms_to_srt_time(start_ms)
        end_time = self._ms_to_srt_time(end_ms)
        
        # Create SRT cue
        cue = {
            'index': self.cue_index,
            'start': start_time,
            'end': end_time,
            'text': sentence_chunk.get('text', '').strip()
        }
        
        if cue['text']:  # Only add non-empty text
            self.cues.append(cue)
            self.cue_index += 1
    
    def _ms_to_srt_time(self, milliseconds):
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(milliseconds // 3600000)
        minutes = int((milliseconds % 3600000) // 60000)
        seconds = int((milliseconds % 60000) // 1000)
        ms = int(milliseconds % 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
    
    def get_srt(self):
        """Generate SRT format string from collected cues."""
        if not self.cues:
            return ""
        
        srt_lines = []
        for cue in self.cues:
            srt_lines.append(str(cue['index']))
            srt_lines.append(f"{cue['start']} --> {cue['end']}")
            srt_lines.append(cue['text'])
            srt_lines.append("")  # Empty line between cues
        
        return "\n".join(srt_lines)


async def generate_audio_and_srt(text, voice, output_prefix):
    """Generate both audio and SRT files using Edge TTS."""
    
    print(f"Generating audio and SRT for: {text[:50]}...")
    print(f"Voice: {voice}")
    print("=" * 60)
    
    # Setup paths
    output_dir = Path("C:/Users/fdtyw/Documents/TTS/Output")
    output_dir.mkdir(exist_ok=True)
    
    audio_file = output_dir / f"{output_prefix}.mp3"
    srt_file = output_dir / f"{output_prefix}.srt"
    
    # Create communicate object and SRT maker
    communicate = edge_tts.Communicate(text, voice)
    srt_maker = CustomSRTMaker()
    
    # Generate audio and collect subtitle events
    audio_chunks = 0
    sentence_events = 0
    word_events = 0
    
    print("Processing TTS stream...")
    with open(audio_file, "wb") as f:
        async for chunk in communicate.stream():
            chunk_type = chunk.get("type")
            
            if chunk_type == "audio":
                f.write(chunk["data"])
                audio_chunks += 1
            elif chunk_type == "SentenceBoundary":
                srt_maker.feed_sentence(chunk)
                sentence_events += 1
                print(f"SentenceBoundary: offset={chunk.get('offset', 0)}, duration={chunk.get('duration', 0)}, text='{chunk.get('text', '')[:30]}...'")
            elif chunk_type == "WordBoundary":
                word_events += 1
                print(f"WordBoundary: offset={chunk.get('offset', 0)}, duration={chunk.get('duration', 0)}, text='{chunk.get('text', '')}'")
    
    # Generate SRT content
    srt_content = srt_maker.get_srt()
    
    # Write SRT file
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    # Report results
    print("=" * 60)
    print(f"Audio chunks: {audio_chunks}")
    print(f"SentenceBoundary events: {sentence_events}")
    print(f"WordBoundary events: {word_events}")
    print(f"SRT cues created: {len(srt_maker.cues)}")
    print(f"Audio saved: {audio_file}")
    print(f"SRT saved: {srt_file}")
    
    if srt_content:
        print("\nSample SRT content:")
        print("-" * 30)
        lines = srt_content.split('\n')[:10]  # First 10 lines
        for line in lines:
            print(line)
        if len(srt_content.split('\n')) > 10:
            print("... (truncated)")
    else:
        print("No SRT content generated!")
    
    return str(audio_file), str(srt_file)


async def test_multiple_texts():
    """Test SRT generation with different texts and voices."""
    
    test_cases = [
        {
            "text": "Hello everyone. This is a test subtitle file created with Edge TTS. We can generate both audio and subtitles at the same time. Each sentence should create a subtitle.",
            "voice": "en-US-JennyNeural",
            "prefix": "test_jenny_sentences"
        },
        {
            "text": "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet. Testing word boundaries and sentence timing.",
            "voice": "en-US-GuyNeural", 
            "prefix": "test_guy_pangram"
        },
        {
            "text": "Xin chào mọi người. Đây là một file phụ đề thử nghiệm được tạo bằng Edge TTS. Chúng ta có thể tạo cả âm thanh và phụ đề cùng một lúc.",
            "voice": "vi-VN-HoaiMyNeural",
            "prefix": "test_vietnamese"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST {i}/{len(test_cases)}")
        print(f"{'=' * 60}")
        
        try:
            audio_file, srt_file = await generate_audio_and_srt(
                test_case["text"], 
                test_case["voice"], 
                test_case["prefix"]
            )
            results.append({
                'test': i,
                'voice': test_case["voice"],
                'audio': audio_file,
                'srt': srt_file,
                'success': True
            })
        except Exception as e:
            print(f"ERROR in test {i}: {e}")
            results.append({
                'test': i,
                'voice': test_case["voice"], 
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    
    for result in results:
        status = "SUCCESS" if result['success'] else "FAILED"
        print(f"Test {result['test']} ({result['voice']}): {status}")
        if not result['success']:
            print(f"  Error: {result.get('error', 'Unknown')}")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(test_multiple_texts())
        success_count = sum(1 for r in results if r['success'])
        print(f"\nCompleted: {success_count}/{len(results)} tests successful")
    except Exception as e:
        print(f"FATAL ERROR: {e}")

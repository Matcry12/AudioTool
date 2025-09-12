#!/usr/bin/env python3
"""
Simple TTS Command Line with SRT Support
Easy-to-use command line version with SRT subtitle generation.
"""

import asyncio
import re
from pathlib import Path
import edge_tts
from typing import List


class CustomSRTMaker:
    """Custom SRT maker that works with SentenceBoundary events."""
    
    def __init__(self):
        self.cues = []
        self.cue_index = 1
    
    def feed_sentence(self, sentence_chunk):
        """Feed a SentenceBoundary event to create SRT cue."""
        if sentence_chunk["type"] != "SentenceBoundary":
            return
        
        start_ms = sentence_chunk["offset"] / 10000
        duration_ms = sentence_chunk["duration"] / 10000
        end_ms = start_ms + duration_ms
        
        start_time = self._ms_to_srt_time(start_ms)
        end_time = self._ms_to_srt_time(end_ms)
        
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


class SimpleTTSConverter:
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.voices = {
            "English Female": "en-US-JennyNeural",
            "Vietnamese Female": "vi-VN-HoaiMyNeural"
        }
        self.voice = "en-US-JennyNeural"
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
        
        # Ensure folders exist
        self.folder_path.mkdir(parents=True, exist_ok=True)
        (self.folder_path / "Output").mkdir(exist_ok=True)
    
    def read_text_file(self, filename: str) -> str:
        """Read text file."""
        file_path = self.folder_path / filename if not Path(filename).is_absolute() else Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            raise ValueError(f"File is empty: {filename}")
        
        print(f"Read {len(content)} characters from {file_path.name}")
        return content
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        chunks = []
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            # Find the end position
            target_end = min(current_pos + chunk_size, text_length)
            
            if target_end == text_length:
                chunk = text[current_pos:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # Look for sentence endings
            search_start = current_pos + chunk_size // 2
            search_text = text[search_start:target_end]
            
            sentence_endings = list(re.finditer(r'[.!?]\s+', search_text))
            
            if sentence_endings:
                last_ending = sentence_endings[-1]
                actual_end = search_start + last_ending.end()
            else:
                # Try other break points
                for pattern in [r'\n\s*\n', r',\s+', r'\s+']:
                    breaks = list(re.finditer(pattern, search_text))
                    if breaks:
                        last_break = breaks[-1]
                        actual_end = search_start + last_break.end()
                        break
                else:
                    actual_end = target_end
            
            chunk = text[current_pos:actual_end].strip()
            if chunk:
                chunks.append(chunk)
            current_pos = actual_end
        
        print(f"Split text into {len(chunks)} chunks")
        return chunks
    
    async def generate_chunk(self, chunk_text: str, chunk_num: int, prefix: str, generate_srt: bool) -> tuple:
        """Generate audio and optional SRT for a single chunk."""
        audio_filename = f"{prefix}_chunk_{chunk_num:03d}.mp3"
        srt_filename = f"{prefix}_chunk_{chunk_num:03d}.srt" if generate_srt else None
        
        output_dir = self.folder_path / "Output"
        audio_path = output_dir / audio_filename
        srt_path = output_dir / srt_filename if srt_filename else None
        
        print(f"Generating chunk {chunk_num}: {chunk_text[:50]}...")
        
        # Create communicate object
        communicate = edge_tts.Communicate(chunk_text, self.voice, rate=self.rate, 
                                         volume=self.volume, pitch=self.pitch)
        
        # Create SRT maker if needed
        srt_maker = CustomSRTMaker() if generate_srt else None
        
        # Generate audio and collect subtitle events
        with open(audio_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary" and srt_maker:
                    srt_maker.feed_sentence(chunk)
        
        # Generate SRT file if requested
        srt_result = None
        if generate_srt and srt_maker and srt_path:
            srt_content = srt_maker.get_srt()
            if srt_content:
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(srt_content)
                print(f"Generated: {audio_filename} + {srt_filename} ({len(srt_maker.cues)} subtitles)")
                srt_result = str(srt_path)
            else:
                print(f"Generated: {audio_filename} (no subtitles)")
        else:
            file_size = audio_path.stat().st_size
            print(f"Generated: {audio_filename} ({file_size} bytes)")
        
        return str(audio_path), srt_result
    
    async def convert_text_file(self, input_file: str, output_prefix: str, voice_choice: str, generate_srt: bool):
        """Convert entire text file to audio chunks with optional SRT."""
        print("=" * 60)
        print("TTS Converter with SRT Support")
        print("=" * 60)
        print(f"Input file: {input_file}")
        print(f"Voice: {voice_choice}")
        print(f"Generate SRT: {'Yes' if generate_srt else 'No'}")
        print(f"Output prefix: {output_prefix}")
        print()
        
        # Set voice
        if voice_choice in self.voices:
            self.voice = self.voices[voice_choice]
        
        try:
            # Read and split text
            text_content = self.read_text_file(input_file)
            chunks = self.split_text_into_chunks(text_content)
            
            if not chunks:
                raise ValueError("No chunks created from text")
            
            # Generate all chunks
            print(f"\nGenerating {len(chunks)} audio chunks...")
            if generate_srt:
                print("SRT subtitle generation enabled")
            print()
            
            audio_files = []
            srt_files = []
            
            for i, chunk in enumerate(chunks, 1):
                if not chunk.strip():
                    continue
                
                try:
                    audio_file, srt_file = await self.generate_chunk(chunk, i, output_prefix, generate_srt)
                    audio_files.append(audio_file)
                    if srt_file:
                        srt_files.append(srt_file)
                except Exception as e:
                    print(f"Error generating chunk {i}: {e}")
                    continue
            
            # Results
            print("\n" + "=" * 60)
            print("CONVERSION COMPLETED!")
            print("=" * 60)
            print(f"Audio chunks: {len(audio_files)} files in Output/")
            if generate_srt and srt_files:
                print(f"SRT subtitles: {len(srt_files)} files in Output/")
            print(f"Output prefix: {output_prefix}")
            print()
            print("Files created:")
            for i, audio_file in enumerate(audio_files):
                print(f"  {Path(audio_file).name}")
                if i < len(srt_files):
                    print(f"  {Path(srt_files[i]).name}")
            
            return audio_files, srt_files
            
        except Exception as e:
            print(f"\nCONVERSION FAILED: {e}")
            raise


def main():
    """Main function - configure your settings here."""
    
    # ===== CONFIGURATION =====
    FOLDER_PATH = r"C:\Users\fdtyw\Documents\TTS"
    INPUT_FILE = "Source/Prolouge to chapter 3 EN.txt"  # Your text file
    OUTPUT_PREFIX = "prologue"              # Prefix for output files  
    VOICE_CHOICE = "English Female"         # "English Female" or "Vietnamese Female"
    GENERATE_SRT = True                     # Generate SRT subtitle files?
    # =========================
    
    # Create converter
    converter = SimpleTTSConverter(FOLDER_PATH)
    
    try:
        # Run conversion
        audio_files, srt_files = asyncio.run(
            converter.convert_text_file(INPUT_FILE, OUTPUT_PREFIX, VOICE_CHOICE, GENERATE_SRT)
        )
        
        print(f"\nSUCCESS! Check the Output/ folder for your files.")
        print(f"Audio chunks: {len(audio_files)}")
        if GENERATE_SRT:
            print(f"SRT subtitles: {len(srt_files)}")
        
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

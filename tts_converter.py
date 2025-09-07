#!/usr/bin/env python3
"""
Text-to-Speech Story Converter
Splits long text files into chunks, converts each to MP3 using Edge TTS,
and merges them into a single audio file.
"""

import os
import asyncio
import re
from pathlib import Path
import edge_tts
from pydub import AudioSegment
from typing import List, Tuple


class TTSConverter:
    def __init__(self, folder_path: str, voice: str = "en-US-JennyNeural"):
        self.folder_path = Path(folder_path)
        self.voice = voice
        self.rate = "+0%"
        self.pitch = "+0%"
        self.chunk_size_min = 1500
        self.chunk_size_max = 2000
        
        # Voice options
        self.voices = {
            "English Female": "en-US-JennyNeural",
            "Vietnamese Female": "vi-VN-HoaiMyNeural"
        }
        
        # Ensure folder exists
        self.folder_path.mkdir(parents=True, exist_ok=True)
    
    def read_text_file(self, filename: str) -> str:
        """Read UTF-8 text file and return content."""
        file_path = self.folder_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError(f"File is empty: {filename}")
            
            print(f"✓ Read {len(content)} characters from {filename}")
            return content
            
        except UnicodeDecodeError:
            raise ValueError(f"File is not valid UTF-8: {filename}")
        except Exception as e:
            raise RuntimeError(f"Error reading file {filename}: {e}")
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks of 1500-2000 characters, respecting sentence boundaries."""
        chunks = []
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            # Calculate the target end position
            target_end = min(current_pos + self.chunk_size_max, text_length)
            
            # If we're at the end of the text, take everything remaining
            if target_end == text_length:
                chunk = text[current_pos:].strip()
                if chunk:  # Only add non-empty chunks
                    chunks.append(chunk)
                break
            
            # Find the best break point (sentence ending)
            # Look for sentence endings within our preferred range
            search_start = current_pos + self.chunk_size_min
            search_text = text[search_start:target_end]
            
            # Look for sentence endings (., !, ?) followed by whitespace
            sentence_endings = list(re.finditer(r'[.!?]\s+', search_text))
            
            if sentence_endings:
                # Use the last sentence ending in our range
                last_ending = sentence_endings[-1]
                actual_end = search_start + last_ending.end()
            else:
                # No sentence ending found, look for other break points
                # Try paragraph breaks, then commas, then spaces
                break_patterns = [r'\n\s*\n', r',\s+', r'\s+']
                actual_end = None
                
                for pattern in break_patterns:
                    breaks = list(re.finditer(pattern, search_text))
                    if breaks:
                        last_break = breaks[-1]
                        actual_end = search_start + last_break.end()
                        break
                
                # If no good break point found, just cut at max length
                if actual_end is None:
                    actual_end = target_end
            
            chunk = text[current_pos:actual_end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            current_pos = actual_end
        
        print(f"✓ Split text into {len(chunks)} chunks")
        
        # Print chunk size statistics
        if chunks:
            sizes = [len(chunk) for chunk in chunks]
            print(f"  Chunk sizes: {min(sizes)}-{max(sizes)} chars (avg: {sum(sizes)//len(sizes)})")
        
        return chunks
    
    async def generate_chunk_audio(self, chunk_text: str, chunk_num: int) -> str:
        """Generate MP3 audio for a single chunk."""
        output_filename = f"chunk_{chunk_num:03d}.mp3"
        output_path = self.folder_path / output_filename
        
        try:
            # Create TTS communication
            communicate = edge_tts.Communicate(
                chunk_text, 
                self.voice, 
                rate=self.rate, 
                pitch=self.pitch
            )
            
            # Save to file
            await communicate.save(str(output_path))
            
            print(f"✓ Generated {output_filename} ({len(chunk_text)} chars)")
            return str(output_path)
            
        except Exception as e:
            print(f"✗ Failed to generate {output_filename}: {e}")
            raise RuntimeError(f"TTS generation failed for chunk {chunk_num}: {e}")
    
    async def generate_all_chunks(self, chunks: List[str]) -> List[str]:
        """Generate audio files for all chunks."""
        print(f"\n🎤 Generating audio for {len(chunks)} chunks...")
        
        chunk_files = []
        
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():  # Skip empty chunks
                print(f"⚠ Skipping empty chunk {i}")
                continue
            
            try:
                chunk_file = await self.generate_chunk_audio(chunk, i)
                chunk_files.append(chunk_file)
            except Exception as e:
                print(f"✗ Error generating chunk {i}: {e}")
                # Continue with other chunks instead of failing completely
                continue
        
        if not chunk_files:
            raise RuntimeError("No audio chunks were successfully generated")
        
        print(f"✓ Successfully generated {len(chunk_files)} audio chunks")
        return chunk_files
    
    def merge_audio_files(self, chunk_files: List[str], output_filename: str = "story_audio.mp3") -> str:
        """Merge all chunk MP3 files into a single file."""
        output_path = self.folder_path / output_filename
        
        print(f"\n🔗 Merging {len(chunk_files)} audio files...")
        
        try:
            # Load the first audio file
            merged_audio = AudioSegment.from_mp3(chunk_files[0])
            print(f"✓ Loaded {Path(chunk_files[0]).name}")
            
            # Append each subsequent file
            for chunk_file in chunk_files[1:]:
                if not Path(chunk_file).exists():
                    print(f"⚠ Skipping missing file: {Path(chunk_file).name}")
                    continue
                
                try:
                    audio_segment = AudioSegment.from_mp3(chunk_file)
                    merged_audio += audio_segment
                    print(f"✓ Merged {Path(chunk_file).name}")
                except Exception as e:
                    print(f"⚠ Failed to merge {Path(chunk_file).name}: {e}")
                    continue
            
            # Export merged audio
            merged_audio.export(str(output_path), format="mp3")
            
            duration_seconds = len(merged_audio) / 1000
            duration_minutes = duration_seconds / 60
            
            print(f"✓ Merged audio saved as {output_filename}")
            print(f"  Duration: {duration_minutes:.1f} minutes ({duration_seconds:.1f} seconds)")
            print(f"  File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to merge audio files: {e}")
    
    async def convert_story(self, input_filename: str) -> str:
        """Main conversion function."""
        print(f"🎯 Starting TTS conversion for: {input_filename}")
        print(f"📁 Working directory: {self.folder_path}")
        print(f"🎙️ Voice: {self.voice} (rate: {self.rate}, pitch: {self.pitch})")
        print("─" * 60)
        
        try:
            # Step 1: Read the text file
            text_content = self.read_text_file(input_filename)
            
            # Step 2: Split into chunks
            chunks = self.split_text_into_chunks(text_content)
            
            if not chunks:
                raise ValueError("No valid chunks created from the text")
            
            # Step 3: Generate audio for each chunk
            chunk_files = await self.generate_all_chunks(chunks)
            
            # Step 4: Merge all chunks
            final_audio = self.merge_audio_files(chunk_files)
            
            print("─" * 60)
            print(f"🎉 SUCCESS! Story converted to audio:")
            print(f"   📄 Input: {input_filename}")
            print(f"   🎵 Output: {Path(final_audio).name}")
            print(f"   📊 Chunks: {len(chunk_files)} files")
            
            return final_audio
            
        except Exception as e:
            print("─" * 60)
            print(f"❌ CONVERSION FAILED: {e}")
            raise


def main():
    """Main function - modify the input filename here."""
    
    # Configuration
    FOLDER_PATH = r"C:\Users\fdtyw\Documents\TTS"
    INPUT_FILENAME = "script.txt"  # ← Change this to your text file name
    VOICE_CHOICE = "English Female"  # ← "English Female" or "Vietnamese Female"
    
    # Create converter instance
    converter = TTSConverter(FOLDER_PATH)
    
    # Set voice based on choice
    if VOICE_CHOICE in converter.voices:
        converter.voice = converter.voices[VOICE_CHOICE]
        print(f"🎙️ Selected voice: {VOICE_CHOICE} ({converter.voice})")
    else:
        print(f"⚠️ Unknown voice choice, using default: {converter.voice}")
    
    try:
        # Run the conversion
        asyncio.run(converter.convert_story(INPUT_FILENAME))
        
    except KeyboardInterrupt:
        print("\n⚠ Conversion interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

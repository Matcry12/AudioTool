#!/usr/bin/env python3
"""
Text-to-Speech Story Converter - Python 3.13 Compatible (Fixed)
Splits long text files into chunks and converts each to MP3 using Edge TTS.
Uses the robust streaming method for audio generation.
"""

import os
import asyncio
import re
import subprocess
from pathlib import Path
import edge_tts
from typing import List


class TTSConverter:
    def __init__(self, folder_path: str, voice: str = "en-US-JennyNeural"):
        self.folder_path = Path(folder_path)
        self.voice = voice
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
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
        file_path = self.folder_path / filename if not Path(filename).is_absolute() else Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError(f"File is empty: {filename}")
            
            print(f"Read {len(content)} characters from {file_path.name}")
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
        
        print(f"Split text into {len(chunks)} chunks")
        
        # Print chunk size statistics
        if chunks:
            sizes = [len(chunk) for chunk in chunks]
            print(f"  Chunk sizes: {min(sizes)}-{max(sizes)} chars (avg: {sum(sizes)//len(sizes)})")
        
        return chunks
    
    async def generate_chunk_audio_robust(self, chunk_text: str, chunk_num: int, prefix: str = "chunk") -> str:
        """Generate MP3 audio for a single chunk using robust streaming method."""
        output_filename = f"{prefix}_{chunk_num:03d}.mp3"
        output_path = self.folder_path / output_filename
        
        try:
            print(f"Generating {output_filename} ({len(chunk_text)} chars)...")
            
            # Create TTS communication using the same method as your working example
            communicate = edge_tts.Communicate(
                text=chunk_text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch
            )
            
            # Use streaming approach like in your working example
            with output_path.open("wb") as f:
                async for chunk in communicate.stream():
                    chunk_type = chunk.get("type")
                    if chunk_type == "audio":
                        f.write(chunk["data"])
            
            # Verify file was created and has content
            if not output_path.exists():
                raise RuntimeError(f"Output file was not created: {output_filename}")
            
            file_size = output_path.stat().st_size
            if file_size == 0:
                raise RuntimeError(f"Output file is empty: {output_filename}")
            
            print(f"Generated {output_filename} ({file_size} bytes)")
            return str(output_path)
            
        except Exception as e:
            print(f"Failed to generate {output_filename}: {e}")
            # Clean up failed file
            if output_path.exists():
                output_path.unlink()
            raise RuntimeError(f"TTS generation failed for chunk {chunk_num}: {e}")
    
    async def generate_all_chunks(self, chunks: List[str], prefix: str = "chunk") -> List[str]:
        """Generate audio files for all chunks."""
        print(f"\nGenerating audio for {len(chunks)} chunks...")
        
        chunk_files = []
        
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():  # Skip empty chunks
                print(f"Skipping empty chunk {i}")
                continue
            
            try:
                chunk_file = await self.generate_chunk_audio_robust(chunk, i, prefix)
                chunk_files.append(chunk_file)
            except Exception as e:
                print(f"Error generating chunk {i}: {e}")
                # Continue with other chunks instead of failing completely
                continue
        
        if not chunk_files:
            raise RuntimeError("No audio chunks were successfully generated")
        
        print(f"\nSuccessfully generated {len(chunk_files)} audio chunks")
        return chunk_files
    
    def try_merge_with_ffmpeg(self, chunk_files: List[str], output_filename: str = "merged_audio.mp3", keep_chunks: bool = True) -> str:
        """Try to merge audio files using ffmpeg if available."""
        # Determine output path based on where chunk files are located
        chunk_folder = Path(chunk_files[0]).parent
        output_path = chunk_folder / output_filename
        
        print(f"\nAttempting to merge {len(chunk_files)} audio files with ffmpeg...")
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            
            # Create input file list for ffmpeg
            list_file = chunk_folder / "chunk_list.txt"
            with open(list_file, 'w') as f:
                for chunk_file in chunk_files:
                    f.write(f"file '{Path(chunk_file).name}'\n")
            
            # Run ffmpeg to concatenate
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0', 
                '-i', str(list_file), '-c', 'copy', 
                str(output_path), '-y'
            ]
            
            print("Running ffmpeg...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=chunk_folder)
            
            # Clean up list file
            list_file.unlink()
            
            if result.returncode == 0:
                print(f"Successfully merged audio: {output_filename}")
                
                # Get file size
                file_size_mb = output_path.stat().st_size / (1024*1024)
                print(f"  File size: {file_size_mb:.1f} MB")
                
                # Delete chunks if requested
                if not keep_chunks:
                    print("Deleting individual chunk files...")
                    for chunk_file in chunk_files:
                        try:
                            Path(chunk_file).unlink()
                            print(f"  Deleted {Path(chunk_file).name}")
                        except Exception as e:
                            print(f"  Failed to delete {Path(chunk_file).name}: {e}")
                
                return str(output_path)
            else:
                print(f"ffmpeg merge failed: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("ffmpeg not found - cannot merge audio files")
            print("  Install ffmpeg from https://ffmpeg.org/ to enable merging")
            return None
        except Exception as e:
            print(f"ffmpeg merge error: {e}")
            return None
    
    async def convert_story(self, input_filename: str, output_prefix: str = "story", keep_chunks: bool = True) -> List[str]:
        """Main conversion function."""
        print(f"Starting TTS conversion for: {input_filename}")
        print(f"Working directory: {self.folder_path}")
        print(f"Voice: {self.voice}")
        print(f"Python 3.13 Mode: Creating individual chunks")
        print("=" * 60)
        
        try:
            # Step 1: Read the text file
            text_content = self.read_text_file(input_filename)
            
            # Step 2: Split into chunks
            chunks = self.split_text_into_chunks(text_content)
            
            if not chunks:
                raise ValueError("No valid chunks created from the text")
            
            # Step 3: Generate audio for each chunk
            chunk_files = await self.generate_all_chunks(chunks, output_prefix)
            
            # Step 4: Move files to Output folder
            output_folder = self.folder_path / "Output"
            output_folder.mkdir(exist_ok=True)
            
            moved_chunk_files = []
            print(f"\nMoving files to Output folder...")
            for chunk_file in chunk_files:
                source_path = Path(chunk_file)
                dest_path = output_folder / source_path.name
                source_path.rename(dest_path)
                moved_chunk_files.append(str(dest_path))
                print(f"Moved {source_path.name} to Output/")
            
            print("=" * 60)
            print(f"SUCCESS! Story converted to audio:")
            print(f"   Input: {input_filename}")
            print(f"   Output: {len(moved_chunk_files)} chunk files in Output/")
            print(f"   Prefix: {output_prefix}")
            print()
            print("Generated files in Output/:")
            for chunk_file in moved_chunk_files:
                file_size = Path(chunk_file).stat().st_size / 1024  # KB
                print(f"   - {Path(chunk_file).name} ({file_size:.1f} KB)")
            
            return moved_chunk_files
            
        except Exception as e:
            print("=" * 60)
            print(f"CONVERSION FAILED: {e}")
            raise


def main():
    """Main function - modify the input filename here."""
    
    # Configuration
    FOLDER_PATH = r"C:\Users\fdtyw\Documents\TTS"
    INPUT_FILENAME = "Source/script.txt"  # <- Change this to your text file name
    OUTPUT_PREFIX = "story"               # <- Prefix for output files
    VOICE_CHOICE = "English Female"       # <- "English Female" or "Vietnamese Female"
    TRY_MERGE = True                      # <- Try to merge with ffmpeg if available
    KEEP_CHUNKS = True                    # <- Keep individual chunk files after merging
    
    # Create converter instance
    converter = TTSConverter(FOLDER_PATH)
    
    # Set voice based on choice
    if VOICE_CHOICE in converter.voices:
        converter.voice = converter.voices[VOICE_CHOICE]
        print(f"Selected voice: {VOICE_CHOICE} ({converter.voice})")
    else:
        print(f"Unknown voice choice, using default: {converter.voice}")
    
    try:
        # Run the conversion
        chunk_files = asyncio.run(converter.convert_story(INPUT_FILENAME, OUTPUT_PREFIX, KEEP_CHUNKS))
        
        # Try to merge if requested
        if TRY_MERGE and chunk_files:
            merged_file = converter.try_merge_with_ffmpeg(chunk_files, f"{OUTPUT_PREFIX}_merged.mp3", KEEP_CHUNKS)
            if merged_file:
                print(f"\nBonus: Merged file created: {Path(merged_file).name}")
            else:
                print(f"\nTip: Use an audio editor to manually combine the {len(chunk_files)} chunk files")
        
        print(f"\nAll files saved in: {Path(chunk_files[0]).parent}")
        
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

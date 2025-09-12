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


class TTSConverter:
    def __init__(self, folder_path: str, voice: str = "en-US-JennyNeural", max_concurrent_chunks: int = 3):
        self.folder_path = Path(folder_path)
        self.voice = voice
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
        self.chunk_size_min = 1500
        self.chunk_size_max = 2000
        self.max_concurrent_chunks = max_concurrent_chunks  # Maximum chunks to process simultaneously
        
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
    
    async def generate_chunk_audio_robust(self, chunk_text: str, chunk_num: int, prefix: str = "chunk", generate_srt: bool = False) -> tuple:
        """Generate MP3 audio for a single chunk using robust streaming method."""
        output_filename = f"{prefix}_{chunk_num:03d}.mp3"
        srt_filename = f"{prefix}_{chunk_num:03d}.srt" if generate_srt else None
        output_path = self.folder_path / output_filename
        srt_path = self.folder_path / srt_filename if srt_filename else None
        
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
            
            # Create SRT maker if needed
            srt_maker = CustomSRTMaker() if generate_srt else None
            
            # Use streaming approach like in your working example
            with output_path.open("wb") as f:
                async for chunk in communicate.stream():
                    chunk_type = chunk.get("type")
                    if chunk_type == "audio":
                        f.write(chunk["data"])
                    elif chunk_type == "SentenceBoundary" and srt_maker:
                        srt_maker.feed_sentence(chunk)
            
            # Verify file was created and has content
            if not output_path.exists():
                raise RuntimeError(f"Output file was not created: {output_filename}")
            
            file_size = output_path.stat().st_size
            if file_size == 0:
                raise RuntimeError(f"Output file is empty: {output_filename}")
            
            # Generate SRT file if requested
            if generate_srt and srt_maker and srt_path:
                srt_content = srt_maker.get_srt()
                if srt_content:
                    with open(srt_path, "w", encoding="utf-8") as srt_file:
                        srt_file.write(srt_content)
                    print(f"Generated {srt_filename} ({len(srt_maker.cues)} cues)")
                else:
                    print(f"No SRT content generated for {srt_filename}")
                    srt_path = None
            
            print(f"Generated {output_filename} ({file_size} bytes)")
            return str(output_path), str(srt_path) if srt_path else None
            
        except Exception as e:
            print(f"Failed to generate {output_filename}: {e}")
            # Clean up failed files
            if output_path.exists():
                output_path.unlink()
            if srt_path and srt_path.exists():
                srt_path.unlink()
            raise RuntimeError(f"TTS generation failed for chunk {chunk_num}: {e}")
    
    async def generate_chunk_with_semaphore(self, semaphore: asyncio.Semaphore, chunk: str, index: int, prefix: str) -> tuple:
        """Generate a single chunk with semaphore control."""
        async with semaphore:
            try:
                chunk_file = await self.generate_chunk_audio_robust(chunk, index, prefix)
                return (index, chunk_file, None)
            except Exception as e:
                return (index, None, str(e))

    async def generate_all_chunks(self, chunks: List[str], prefix: str = "chunk") -> List[str]:
        """Generate audio files for all chunks with concurrent processing."""
        print(f"\nGenerating audio for {len(chunks)} chunks...")
        print(f"Processing up to {self.max_concurrent_chunks} chunks simultaneously...")
        
        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_concurrent_chunks)
        
        # Create tasks for all chunks
        tasks = []
        valid_chunk_count = 0
        
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():  # Skip empty chunks
                print(f"Skipping empty chunk {i}")
                continue
            
            valid_chunk_count += 1
            task = self.generate_chunk_with_semaphore(semaphore, chunk, i, prefix)
            tasks.append(task)
        
        # Process all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Sort results by index and collect successful files
        chunk_files = []
        errors = []
        
        for index, chunk_file, error in sorted(results, key=lambda x: x[0]):
            if chunk_file:
                chunk_files.append(chunk_file)
            else:
                errors.append((index, error))
        
        # Report any errors
        if errors:
            print(f"\nEncountered {len(errors)} errors during chunk generation:")
            for index, error in errors:
                print(f"  Chunk {index}: {error}")
        
        if not chunk_files:
            raise RuntimeError("No audio chunks were successfully generated")
        
        print(f"\nSuccessfully generated {len(chunk_files)} out of {valid_chunk_count} chunks")
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
    FOLDER_PATH = os.getcwd()
    INPUT_FILENAME = "Source/script.txt"  # <- Change this to your text file name
    OUTPUT_PREFIX = "story"               # <- Prefix for output files
    VOICE_CHOICE = "English Female"       # <- "English Female" or "Vietnamese Female"
    TRY_MERGE = True                      # <- Try to merge with ffmpeg if available
    KEEP_CHUNKS = True                    # <- Keep individual chunk files after merging
    GENERATE_SRT = True                   # <- Generate SRT subtitle files
    MAX_CONCURRENT_CHUNKS = 3             # <- Maximum chunks to process simultaneously (1-5 recommended)
    
    # Create converter instance with concurrent processing
    converter = TTSConverter(FOLDER_PATH, max_concurrent_chunks=MAX_CONCURRENT_CHUNKS)
    
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

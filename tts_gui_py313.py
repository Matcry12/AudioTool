#!/usr/bin/env python3
"""
TTS Converter GUI - Python 3.13 Compatible Version
A user-friendly interface for converting text files to speech using Edge TTS.
Supports English and Vietnamese voices with chunking (no audio merging due to pydub incompatibility).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import asyncio
import threading
import os
import re
import subprocess
from pathlib import Path
import edge_tts
from typing import List
import sys


class TTSConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS Story Converter (Python 3.13 Compatible)")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Default settings
        self.folder_path = Path(r"C:\Users\fdtyw\Documents\TTS")
        self.voices = {
            "English Female (Jenny)": "en-US-JennyNeural",
            "Vietnamese Female (Hoai My)": "vi-VN-HoaiMyNeural"
        }
        
        # Conversion state
        self.is_converting = False
        self.conversion_thread = None
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create and arrange GUI widgets."""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="TTS Story Converter", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Python 3.13 warning
        warning_frame = ttk.Frame(main_frame)
        warning_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        warning_label = ttk.Label(warning_frame, 
                                 text="⚠️ Python 3.13 Mode: Creates individual MP3 chunks (no auto-merging)",
                                 foreground="orange", font=("Arial", 9))
        warning_label.grid(row=0, column=0)
        
        # File selection
        ttk.Label(main_frame, text="Text File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(main_frame, textvariable=self.file_var, width=50)
        self.file_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        
        self.browse_button = ttk.Button(main_frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=2, column=2, pady=5)
        
        # Voice selection
        ttk.Label(main_frame, text="Voice:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar(value="English Female (Jenny)")
        voice_combo = ttk.Combobox(main_frame, textvariable=self.voice_var, 
                                  values=list(self.voices.keys()), state="readonly", width=30)
        voice_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Output prefix
        ttk.Label(main_frame, text="Output Prefix:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value="story")
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=30)
        output_entry.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="5")
        settings_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        settings_frame.columnconfigure(1, weight=1)
        
        # Chunk size
        ttk.Label(settings_frame, text="Chunk Size:").grid(row=0, column=0, sticky=tk.W)
        self.chunk_var = tk.StringVar(value="1500-2000")
        chunk_combo = ttk.Combobox(settings_frame, textvariable=self.chunk_var,
                                  values=["1000-1500", "1500-2000", "2000-2500"], 
                                  state="readonly", width=15)
        chunk_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Try merge checkbox
        self.try_merge_var = tk.BooleanVar(value=True)
        merge_cb = ttk.Checkbutton(settings_frame, text="Try to merge with ffmpeg (if available)",
                                  variable=self.try_merge_var)
        merge_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Keep chunks checkbox
        self.keep_chunks_var = tk.BooleanVar(value=True)
        keep_chunks_cb = ttk.Checkbutton(settings_frame, text="Keep individual chunk files",
                                        variable=self.keep_chunks_var)
        keep_chunks_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="Convert to Audio", 
                                        command=self.start_conversion)
        self.convert_button.grid(row=6, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=7, column=0, columnspan=3, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Conversion Log", padding="5")
        log_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=5)
        
        # Set initial folder
        self.folder_path.mkdir(parents=True, exist_ok=True)
        self.log(f"📁 Working directory: {self.folder_path}")
        self.log("⚠️ Python 3.13 compatibility mode: Individual chunks will be created")
        self.log("   Use external tools to merge MP3 files if needed")
    
    def browse_file(self):
        """Open file dialog to select text file."""
        file_types = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        initial_dir = self.folder_path / "Source" if (self.folder_path / "Source").exists() else self.folder_path
        
        filename = filedialog.askopenfilename(
            title="Select Text File",
            initialdir=initial_dir,
            filetypes=file_types
        )
        
        if filename:
            self.file_var.set(filename)
            # Auto-generate output prefix based on input
            input_name = Path(filename).stem
            self.output_var.set(input_name)
    
    def log(self, message):
        """Add message to log with timestamp."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log text."""
        self.log_text.delete(1.0, tk.END)
    
    def update_progress(self, message):
        """Update progress label."""
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def start_conversion(self):
        """Start the conversion process in a separate thread."""
        if self.is_converting:
            return
        
        # Validate inputs
        if not self.file_var.get():
            messagebox.showerror("Error", "Please select a text file")
            return
        
        if not Path(self.file_var.get()).exists():
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        # Start conversion
        self.is_converting = True
        self.convert_button.config(text="Converting...", state="disabled")
        self.progress_bar.start()
        
        # Run conversion in separate thread
        self.conversion_thread = threading.Thread(target=self.run_conversion)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
    
    def run_conversion(self):
        """Run the actual conversion process."""
        try:
            # Get settings
            chunk_range = self.chunk_var.get().split("-")
            chunk_min = int(chunk_range[0])
            chunk_max = int(chunk_range[1])
            
            voice_name = self.voices[self.voice_var.get()]
            output_prefix = self.output_var.get()
            input_file = self.file_var.get()
            
            # Create converter
            converter = TTSConverter(
                str(self.folder_path),
                voice=voice_name,
                chunk_min=chunk_min,
                chunk_max=chunk_max,
                progress_callback=self.update_progress,
                log_callback=self.log
            )
            
            # Run conversion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            chunk_files = loop.run_until_complete(
                converter.convert_story(input_file, output_prefix)
            )
            
            # Try to merge if requested and ffmpeg is available
            merged_file = None
            if self.try_merge_var.get() and chunk_files:
                merged_file = converter.try_merge_with_ffmpeg(
                    chunk_files, f"{output_prefix}_merged.mp3", self.keep_chunks_var.get()
                )
            
            loop.close()
            
            # Success message
            files_location = Path(chunk_files[0]).parent.name if chunk_files else "Output"
            message = f"✅ Conversion completed!\n📊 Created {len(chunk_files)} audio chunks in {files_location}/"
            if merged_file:
                message += f"\n🔗 Merged file: {Path(merged_file).name}"
            elif not self.keep_chunks_var.get() and merged_file is None:
                message += "\n⚠️ No merged file created (chunks would be deleted without merge)"
            
            self.root.after(0, self.conversion_complete, True, message)
            
        except Exception as e:
            self.root.after(0, self.conversion_complete, False, f"❌ Conversion failed: {str(e)}")
    
    def conversion_complete(self, success, message):
        """Handle conversion completion."""
        self.is_converting = False
        self.convert_button.config(text="Convert to Audio", state="normal")
        self.progress_bar.stop()
        
        if success:
            self.update_progress("Conversion completed!")
            self.log("─" * 50)
            self.log(message)
            messagebox.showinfo("Success", message)
        else:
            self.update_progress("Conversion failed!")
            self.log("─" * 50)
            self.log(message)
            messagebox.showerror("Error", message)


class TTSConverter:
    """Core TTS conversion logic - Python 3.13 compatible version."""
    
    def __init__(self, folder_path: str, voice: str = "en-US-JennyNeural", 
                 chunk_min: int = 1500, chunk_max: int = 2000,
                 progress_callback=None, log_callback=None):
        self.folder_path = Path(folder_path)
        self.voice = voice
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
        self.chunk_size_min = chunk_min
        self.chunk_size_max = chunk_max
        self.progress_callback = progress_callback or (lambda x: None)
        self.log_callback = log_callback or (lambda x: None)
        
        self.folder_path.mkdir(parents=True, exist_ok=True)
    
    def read_text_file(self, filename: str) -> str:
        """Read UTF-8 text file and return content."""
        file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError(f"File is empty: {filename}")
            
            self.log_callback(f"✓ Read {len(content)} characters from {file_path.name}")
            return content
            
        except UnicodeDecodeError:
            raise ValueError(f"File is not valid UTF-8: {filename}")
        except Exception as e:
            raise RuntimeError(f"Error reading file {filename}: {e}")
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks respecting sentence boundaries."""
        chunks = []
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            target_end = min(current_pos + self.chunk_size_max, text_length)
            
            if target_end == text_length:
                chunk = text[current_pos:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            search_start = current_pos + self.chunk_size_min
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
        
        self.log_callback(f"✓ Split text into {len(chunks)} chunks")
        
        if chunks:
            sizes = [len(chunk) for chunk in chunks]
            self.log_callback(f"  Chunk sizes: {min(sizes)}-{max(sizes)} chars (avg: {sum(sizes)//len(sizes)})")
        
        return chunks
    
    async def generate_chunk_audio(self, chunk_text: str, chunk_num: int, prefix: str) -> str:
        """Generate MP3 audio for a single chunk using robust streaming method."""
        output_filename = f"{prefix}_chunk_{chunk_num:03d}.mp3"
        output_path = self.folder_path / output_filename
        
        try:
            # Create TTS communication using the robust streaming method
            communicate = edge_tts.Communicate(
                text=chunk_text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch
            )
            
            # Use streaming approach for reliability
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
            
            self.log_callback(f"✓ Generated {output_filename} ({file_size} bytes)")
            return str(output_path)
            
        except Exception as e:
            self.log_callback(f"✗ Failed to generate {output_filename}: {e}")
            # Clean up failed file
            if output_path.exists():
                output_path.unlink()
            raise RuntimeError(f"TTS generation failed for chunk {chunk_num}: {e}")
    
    async def generate_all_chunks(self, chunks: List[str], prefix: str) -> List[str]:
        """Generate audio files for all chunks."""
        self.log_callback(f"🎤 Generating audio for {len(chunks)} chunks...")
        self.progress_callback("Generating audio chunks...")
        
        chunk_files = []
        
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():
                self.log_callback(f"⚠ Skipping empty chunk {i}")
                continue
            
            self.progress_callback(f"Generating chunk {i}/{len(chunks)}")
            
            try:
                chunk_file = await self.generate_chunk_audio(chunk, i, prefix)
                chunk_files.append(chunk_file)
            except Exception as e:
                self.log_callback(f"✗ Error generating chunk {i}: {e}")
                continue
        
        if not chunk_files:
            raise RuntimeError("No audio chunks were successfully generated")
        
        self.log_callback(f"✓ Successfully generated {len(chunk_files)} audio chunks")
        return chunk_files
    
    def try_merge_with_ffmpeg(self, chunk_files: List[str], output_filename: str, keep_chunks: bool = True) -> str:
        """Try to merge audio files using ffmpeg if available."""
        # Determine output path based on where chunk files are located
        chunk_folder = Path(chunk_files[0]).parent
        output_path = chunk_folder / output_filename
        
        self.log_callback("🔗 Attempting to merge with ffmpeg...")
        
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
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=chunk_folder)
            
            # Clean up list file
            list_file.unlink()
            
            if result.returncode == 0:
                self.log_callback(f"✓ Successfully merged audio with ffmpeg: {output_filename}")
                
                # Delete chunks if requested
                if not keep_chunks:
                    self.log_callback("🧹 Deleting individual chunk files...")
                    for chunk_file in chunk_files:
                        try:
                            Path(chunk_file).unlink()
                            self.log_callback(f"✓ Deleted {Path(chunk_file).name}")
                        except Exception as e:
                            self.log_callback(f"⚠ Failed to delete {Path(chunk_file).name}: {e}")
                
                return str(output_path)
            else:
                self.log_callback(f"✗ ffmpeg merge failed: {result.stderr}")
                return None
                
        except FileNotFoundError:
            self.log_callback("⚠ ffmpeg not found - cannot merge audio files")
            self.log_callback("  Install ffmpeg from https://ffmpeg.org/ to enable merging")
            return None
        except Exception as e:
            self.log_callback(f"✗ ffmpeg merge error: {e}")
            return None
    
    async def convert_story(self, input_filename: str, output_prefix: str) -> List[str]:
        """Main conversion function."""
        self.log_callback(f"🎯 Starting TTS conversion")
        self.log_callback(f"📄 Input: {Path(input_filename).name}")
        self.log_callback(f"🎙️ Voice: {self.voice}")
        self.log_callback("─" * 50)
        
        try:
            text_content = self.read_text_file(input_filename)
            chunks = self.split_text_into_chunks(text_content)
            
            if not chunks:
                raise ValueError("No valid chunks created from the text")
            
            chunk_files = await self.generate_all_chunks(chunks, output_prefix)
            
            # Move files to Output folder
            output_folder = self.folder_path / "Output"
            output_folder.mkdir(exist_ok=True)
            
            moved_chunk_files = []
            self.log_callback("🔄 Moving files to Output folder...")
            for chunk_file in chunk_files:
                source_path = Path(chunk_file)
                dest_path = output_folder / source_path.name
                source_path.rename(dest_path)
                moved_chunk_files.append(str(dest_path))
                self.log_callback(f"✓ Moved {source_path.name} to Output/")
            
            self.log_callback("─" * 50)
            self.log_callback(f"🎉 SUCCESS! Story converted to audio:")
            self.log_callback(f"   📄 Input: {Path(input_filename).name}")
            self.log_callback(f"   🎵 Output: {len(moved_chunk_files)} chunk files in Output/")
            self.log_callback(f"   📊 Prefix: {output_prefix}")
            
            return moved_chunk_files
            
        except Exception as e:
            self.log_callback("─" * 50)
            self.log_callback(f"❌ CONVERSION FAILED: {e}")
            raise


def main():
    """Launch the GUI application."""
    try:
        root = tk.Tk()
        app = TTSConverterGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
TTS Converter GUI with SRT Support
A user-friendly GUI for converting text files to speech with subtitle generation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import asyncio
import threading
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


class TTSConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS Story Converter with SRT Support")
        self.root.geometry("800x650")
        
        # Default settings
        self.folder_path = Path(r"C:\Users\fdtyw\Documents\TTS")
        self.voices = {
            "English Female (Jenny)": "en-US-JennyNeural",
            "Vietnamese Female (Hoai My)": "vi-VN-HoaiMyNeural"
        }
        
        # Conversion state
        self.is_converting = False
        
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
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="TTS Converter with SRT Subtitles", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        ttk.Label(main_frame, text="Text File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(main_frame, textvariable=self.file_var, width=50)
        self.file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        
        self.browse_button = ttk.Button(main_frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=1, column=2, pady=5)
        
        # Voice selection
        ttk.Label(main_frame, text="Voice:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar(value="English Female (Jenny)")
        voice_combo = ttk.Combobox(main_frame, textvariable=self.voice_var, 
                                  values=list(self.voices.keys()), state="readonly", width=30)
        voice_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Output prefix
        ttk.Label(main_frame, text="Output Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value="story")
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=30)
        output_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        settings_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Generate SRT checkbox (prominent)
        self.generate_srt_var = tk.BooleanVar(value=True)
        srt_cb = ttk.Checkbutton(settings_frame, text="✅ Generate SRT subtitle files (.srt)",
                                variable=self.generate_srt_var)
        srt_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Keep chunks checkbox
        self.keep_chunks_var = tk.BooleanVar(value=True)
        keep_chunks_cb = ttk.Checkbutton(settings_frame, text="Keep individual chunk files",
                                        variable=self.keep_chunks_var)
        keep_chunks_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="🎤 Convert to Audio + Subtitles", 
                                        command=self.start_conversion)
        self.convert_button.grid(row=5, column=0, columnspan=3, pady=20)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to convert")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=6, column=0, columnspan=3, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 10))
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Conversion Log", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=5)
        
        # Initialize
        self.folder_path.mkdir(parents=True, exist_ok=True)
        (self.folder_path / "Output").mkdir(exist_ok=True)
        self.log(f"Working directory: {self.folder_path}")
        self.log("SRT subtitle generation available! Enable in options above.")
    
    def browse_file(self):
        """Open file dialog to select text file."""
        file_types = [("Text files", "*.txt"), ("All files", "*.*")]
        initial_dir = self.folder_path / "Source" if (self.folder_path / "Source").exists() else self.folder_path
        
        filename = filedialog.askopenfilename(title="Select Text File", initialdir=initial_dir, filetypes=file_types)
        if filename:
            self.file_var.set(filename)
            input_name = Path(filename).stem
            self.output_var.set(input_name)
    
    def log(self, message):
        """Add message to log."""
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
        
        if not self.file_var.get():
            messagebox.showerror("Error", "Please select a text file")
            return
        
        if not Path(self.file_var.get()).exists():
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        self.is_converting = True
        self.convert_button.config(text="Converting...", state="disabled")
        self.progress_bar.start()
        
        self.conversion_thread = threading.Thread(target=self.run_conversion)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
    
    def run_conversion(self):
        """Run the actual conversion process."""
        try:
            voice_name = self.voices[self.voice_var.get()]
            output_prefix = self.output_var.get()
            input_file = self.file_var.get()
            generate_srt = self.generate_srt_var.get()
            
            converter = TTSConverter(str(self.folder_path), voice=voice_name, 
                                   progress_callback=self.update_progress, log_callback=self.log)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            chunk_files, srt_files = loop.run_until_complete(
                converter.convert_story(input_file, output_prefix, generate_srt)
            )
            
            loop.close()
            
            files_location = "Output"
            message = f"SUCCESS! Conversion completed!\n"
            message += f"Audio chunks: {len(chunk_files)} files in {files_location}/\n"
            if generate_srt and srt_files:
                message += f"SRT subtitles: {len(srt_files)} files in {files_location}/"
            else:
                message += "No subtitle files generated (SRT option disabled)"
            
            self.root.after(0, self.conversion_complete, True, message)
            
        except Exception as e:
            self.root.after(0, self.conversion_complete, False, f"Conversion failed: {str(e)}")
    
    def conversion_complete(self, success, message):
        """Handle conversion completion."""
        self.is_converting = False
        self.convert_button.config(text="🎤 Convert to Audio + Subtitles", state="normal")
        self.progress_bar.stop()
        
        if success:
            self.update_progress("Conversion completed successfully!")
            self.log("=" * 50)
            self.log(message)
            messagebox.showinfo("Success", message)
        else:
            self.update_progress("Conversion failed!")
            self.log("=" * 50)
            self.log(message)
            messagebox.showerror("Error", message)


class TTSConverter:
    """Core TTS conversion logic with SRT support."""
    
    def __init__(self, folder_path: str, voice: str = "en-US-JennyNeural", 
                 progress_callback=None, log_callback=None):
        self.folder_path = Path(folder_path)
        self.voice = voice
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
        self.chunk_size_min = 1500
        self.chunk_size_max = 2000
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
            
            self.log_callback(f"Read {len(content)} characters from {file_path.name}")
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
        
        self.log_callback(f"Split text into {len(chunks)} chunks")
        if chunks:
            sizes = [len(chunk) for chunk in chunks]
            self.log_callback(f"Chunk sizes: {min(sizes)}-{max(sizes)} chars (avg: {sum(sizes)//len(sizes)})")
        
        return chunks
    
    async def generate_chunk_audio(self, chunk_text: str, chunk_num: int, prefix: str, generate_srt: bool = False) -> tuple:
        """Generate MP3 audio and optional SRT for a single chunk."""
        output_filename = f"{prefix}_chunk_{chunk_num:03d}.mp3"
        srt_filename = f"{prefix}_chunk_{chunk_num:03d}.srt" if generate_srt else None
        
        output_path = self.folder_path / "Output" / output_filename
        srt_path = self.folder_path / "Output" / srt_filename if srt_filename else None
        
        try:
            # Create TTS communication
            communicate = edge_tts.Communicate(
                text=chunk_text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch
            )
            
            # Create SRT maker if needed
            srt_maker = CustomSRTMaker() if generate_srt else None
            
            # Use streaming approach
            with output_path.open("wb") as f:
                async for chunk in communicate.stream():
                    chunk_type = chunk.get("type")
                    if chunk_type == "audio":
                        f.write(chunk["data"])
                    elif chunk_type == "SentenceBoundary" and srt_maker:
                        srt_maker.feed_sentence(chunk)
            
            # Verify audio file was created
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
                    self.log_callback(f"Generated {output_filename} + {srt_filename} ({len(srt_maker.cues)} subtitles)")
                    return str(output_path), str(srt_path)
                else:
                    self.log_callback(f"Generated {output_filename} (no subtitles)")
                    return str(output_path), None
            else:
                self.log_callback(f"Generated {output_filename} ({file_size} bytes)")
                return str(output_path), None
            
        except Exception as e:
            self.log_callback(f"Failed to generate {output_filename}: {e}")
            # Clean up failed files
            if output_path.exists():
                output_path.unlink()
            if srt_path and srt_path.exists():
                srt_path.unlink()
            raise RuntimeError(f"TTS generation failed for chunk {chunk_num}: {e}")
    
    async def generate_all_chunks(self, chunks: List[str], prefix: str, generate_srt: bool = False) -> tuple:
        """Generate audio files for all chunks."""
        self.log_callback(f"Generating audio for {len(chunks)} chunks...")
        if generate_srt:
            self.log_callback("SRT subtitle generation enabled")
        
        chunk_files = []
        srt_files = []
        
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():
                self.log_callback(f"Skipping empty chunk {i}")
                continue
            
            self.progress_callback(f"Generating chunk {i}/{len(chunks)}")
            
            try:
                audio_file, srt_file = await self.generate_chunk_audio(chunk, i, prefix, generate_srt)
                chunk_files.append(audio_file)
                if srt_file:
                    srt_files.append(srt_file)
            except Exception as e:
                self.log_callback(f"Error generating chunk {i}: {e}")
                continue
        
        if not chunk_files:
            raise RuntimeError("No audio chunks were successfully generated")
        
        self.log_callback(f"Successfully generated {len(chunk_files)} audio chunks")
        if generate_srt and srt_files:
            self.log_callback(f"Generated {len(srt_files)} SRT subtitle files")
        
        return chunk_files, srt_files
    
    async def convert_story(self, input_filename: str, output_prefix: str, generate_srt: bool = False) -> tuple:
        """Main conversion function."""
        self.log_callback(f"Starting TTS conversion")
        self.log_callback(f"Input: {Path(input_filename).name}")
        self.log_callback(f"Voice: {self.voice}")
        if generate_srt:
            self.log_callback("SRT generation: Enabled")
        self.log_callback("-" * 50)
        
        try:
            text_content = self.read_text_file(input_filename)
            chunks = self.split_text_into_chunks(text_content)
            
            if not chunks:
                raise ValueError("No valid chunks created from the text")
            
            chunk_files, srt_files = await self.generate_all_chunks(chunks, output_prefix, generate_srt)
            
            self.log_callback("-" * 50)
            self.log_callback(f"SUCCESS! Story converted to audio:")
            self.log_callback(f"   Input: {Path(input_filename).name}")
            self.log_callback(f"   Audio chunks: {len(chunk_files)} files in Output/")
            if generate_srt and srt_files:
                self.log_callback(f"   SRT subtitles: {len(srt_files)} files in Output/")
            self.log_callback(f"   Prefix: {output_prefix}")
            
            return chunk_files, srt_files
            
        except Exception as e:
            self.log_callback("-" * 50)
            self.log_callback(f"CONVERSION FAILED: {e}")
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

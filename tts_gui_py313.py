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
        self.root.title("TTS Story Converter")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Configure modern theme
        self.setup_theme()
        
        # Default settings
        self.folder_path = Path.cwd()
        self.voices = {
            "English Female (Jenny)": "en-US-JennyNeural",
            "Vietnamese Female (Hoai My)": "vi-VN-HoaiMyNeural"
        }
        
        # Conversion state
        self.is_converting = False
        self.conversion_thread = None
        
        self.create_widgets()
        self.center_window()
    
    def setup_theme(self):
        """Configure modern color scheme and styles."""
        style = ttk.Style()
        
        # Configure colors
        self.colors = {
            'bg': '#f0f0f0',
            'card': '#ffffff',
            'primary': '#2563eb',
            'primary_hover': '#1d4ed8',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'text': '#1f2937',
            'text_secondary': '#6b7280'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Configure button styles
        style.configure('Primary.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       foreground='white')
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_hover']),
                           ('!active', self.colors['primary'])])
        
        # Configure frame styles
        style.configure('Card.TFrame', 
                       background=self.colors['card'],
                       relief='flat',
                       borderwidth=1)
        
        # Configure label styles
        style.configure('Heading.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       background=self.colors['bg'],
                       foreground=self.colors['text'])
        
        style.configure('Subheading.TLabel',
                       font=('Segoe UI', 12),
                       background=self.colors['bg'],
                       foreground=self.colors['text_secondary'])
    
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create and arrange GUI widgets with modern design."""
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header section
        header_frame = tk.Frame(main_container, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title with icon-like symbol
        title_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        title_frame.pack()
        
        icon_label = tk.Label(title_frame, text="🎵", font=('Segoe UI', 32), bg=self.colors['bg'])
        icon_label.pack(side='left', padx=(0, 10))
        
        title_label = ttk.Label(title_frame, text="TTS Story Converter", style='Heading.TLabel')
        title_label.pack(side='left')
        
        subtitle_label = ttk.Label(header_frame, text="Convert text files to high-quality audio", style='Subheading.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Content area with cards
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True)
        
        # Input card
        input_card = self.create_card(content_frame, "Input Configuration")
        input_card.pack(fill='x', pady=(0, 15))
        
        # File selection
        file_frame = tk.Frame(input_card, bg=self.colors['card'])
        file_frame.pack(fill='x', pady=(10, 5), padx=15)
        
        file_label = tk.Label(file_frame, text="📄 Text File", font=('Segoe UI', 11), 
                             bg=self.colors['card'], fg=self.colors['text'])
        file_label.pack(anchor='w')
        
        file_input_frame = tk.Frame(file_frame, bg=self.colors['card'])
        file_input_frame.pack(fill='x', pady=(5, 0))
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_input_frame, textvariable=self.file_var, 
                                   font=('Segoe UI', 10))
        self.file_entry.pack(side='left', fill='x', expand=True)
        
        self.browse_button = tk.Button(file_input_frame, text="Browse", 
                                      command=self.browse_file,
                                      bg=self.colors['primary'], fg='white',
                                      font=('Segoe UI', 10, 'bold'),
                                      relief='flat', padx=20, pady=5,
                                      cursor='hand2')
        self.browse_button.pack(side='right', padx=(10, 0))
        self.bind_button_hover(self.browse_button, self.colors['primary'], self.colors['primary_hover'])
        
        # Voice selection
        voice_frame = tk.Frame(input_card, bg=self.colors['card'])
        voice_frame.pack(fill='x', pady=5, padx=15)
        
        voice_label = tk.Label(voice_frame, text="🎤 Voice", font=('Segoe UI', 11),
                              bg=self.colors['card'], fg=self.colors['text'])
        voice_label.pack(anchor='w')
        
        self.voice_var = tk.StringVar(value="English Female (Jenny)")
        voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var,
                                  values=list(self.voices.keys()), 
                                  state="readonly", font=('Segoe UI', 10))
        voice_combo.pack(fill='x', pady=(5, 0))
        
        # Output prefix
        output_frame = tk.Frame(input_card, bg=self.colors['card'])
        output_frame.pack(fill='x', pady=(5, 15), padx=15)
        
        output_label = tk.Label(output_frame, text="💾 Output Prefix", font=('Segoe UI', 11),
                               bg=self.colors['card'], fg=self.colors['text'])
        output_label.pack(anchor='w')
        
        self.output_var = tk.StringVar(value="story")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var,
                               font=('Segoe UI', 10))
        output_entry.pack(fill='x', pady=(5, 0))
        
        # Settings card
        settings_card = self.create_card(content_frame, "Advanced Settings")
        settings_card.pack(fill='x', pady=(0, 15))
        
        settings_content = tk.Frame(settings_card, bg=self.colors['card'])
        settings_content.pack(fill='x', padx=15, pady=10)
        
        # Settings grid
        settings_grid = tk.Frame(settings_content, bg=self.colors['card'])
        settings_grid.pack(fill='x')
        
        # Chunk size and concurrent settings
        left_settings = tk.Frame(settings_grid, bg=self.colors['card'])
        left_settings.pack(side='left', fill='x', expand=True)
        
        chunk_label = tk.Label(left_settings, text="📊 Chunk Size", font=('Segoe UI', 10),
                              bg=self.colors['card'], fg=self.colors['text'])
        chunk_label.pack(anchor='w')
        
        self.chunk_var = tk.StringVar(value="1500-2000")
        chunk_combo = ttk.Combobox(left_settings, textvariable=self.chunk_var,
                                  values=["1000-1500", "1500-2000", "2000-2500"],
                                  state="readonly", font=('Segoe UI', 10), width=15)
        chunk_combo.pack(anchor='w', pady=(5, 10))
        
        right_settings = tk.Frame(settings_grid, bg=self.colors['card'])
        right_settings.pack(side='left', fill='x', expand=True, padx=(20, 0))
        
        concurrent_label = tk.Label(right_settings, text="⚡ Concurrent Processing", font=('Segoe UI', 10),
                                   bg=self.colors['card'], fg=self.colors['text'])
        concurrent_label.pack(anchor='w')
        
        self.concurrent_var = tk.StringVar(value="3")
        concurrent_combo = ttk.Combobox(right_settings, textvariable=self.concurrent_var,
                                       values=["1", "2", "3", "4", "5"],
                                       state="readonly", font=('Segoe UI', 10), width=15)
        concurrent_combo.pack(anchor='w', pady=(5, 10))
        
        # Checkboxes
        checkbox_frame = tk.Frame(settings_content, bg=self.colors['card'])
        checkbox_frame.pack(fill='x', pady=(10, 0))
        
        self.try_merge_var = tk.BooleanVar(value=True)
        merge_cb = tk.Checkbutton(checkbox_frame, text="Try to merge with ffmpeg (if available)",
                                 variable=self.try_merge_var, font=('Segoe UI', 10),
                                 bg=self.colors['card'], fg=self.colors['text'],
                                 activebackground=self.colors['card'])
        merge_cb.pack(anchor='w', pady=2)
        
        self.keep_chunks_var = tk.BooleanVar(value=True)
        keep_chunks_cb = tk.Checkbutton(checkbox_frame, text="Keep individual chunk files",
                                       variable=self.keep_chunks_var, font=('Segoe UI', 10),
                                       bg=self.colors['card'], fg=self.colors['text'],
                                       activebackground=self.colors['card'])
        keep_chunks_cb.pack(anchor='w', pady=2)
        
        # Convert button
        button_frame = tk.Frame(main_container, bg=self.colors['bg'])
        button_frame.pack(pady=20)
        
        self.convert_button = tk.Button(button_frame, text="🎵 Convert to Audio",
                                       command=self.start_conversion,
                                       bg=self.colors['primary'], fg='white',
                                       font=('Segoe UI', 12, 'bold'),
                                       relief='flat', padx=30, pady=12,
                                       cursor='hand2')
        self.convert_button.pack()
        self.bind_button_hover(self.convert_button, self.colors['primary'], self.colors['primary_hover'])
        
        # Progress section
        progress_card = self.create_card(main_container, "Progress")
        progress_card.pack(fill='x', pady=(0, 15))
        
        progress_content = tk.Frame(progress_card, bg=self.colors['card'])
        progress_content.pack(fill='x', padx=15, pady=10)
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = tk.Label(progress_content, textvariable=self.progress_var,
                                      font=('Segoe UI', 11), bg=self.colors['card'],
                                      fg=self.colors['text'])
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(progress_content, mode='indeterminate',
                                          style='TProgressbar')
        self.progress_bar.pack(fill='x', pady=(10, 0))
        
        # Log output card
        log_card = self.create_card(main_container, "Conversion Log")
        log_card.pack(fill='both', expand=True)
        
        log_content = tk.Frame(log_card, bg=self.colors['card'])
        log_content.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Log text with custom styling
        log_frame = tk.Frame(log_content, bg=self.colors['card'])
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                 font=('Consolas', 10),
                                                 bg='#1e293b', fg='#e2e8f0',
                                                 insertbackground='white',
                                                 relief='flat',
                                                 padx=10, pady=10)
        self.log_text.pack(fill='both', expand=True)
        
        # Clear log button
        clear_button = tk.Button(log_content, text="Clear Log",
                               command=self.clear_log,
                               bg=self.colors['text_secondary'], fg='white',
                               font=('Segoe UI', 9),
                               relief='flat', padx=15, pady=5,
                               cursor='hand2')
        clear_button.pack(anchor='e', pady=(10, 0))
        self.bind_button_hover(clear_button, self.colors['text_secondary'], '#4b5563')
        
        # Set initial folder
        self.folder_path.mkdir(parents=True, exist_ok=True)
        self.log(f"📁 Working directory: {self.folder_path}")
        self.log("✅ Ready to convert text files to audio")
    
    def bind_button_hover(self, button, normal_color, hover_color):
        """Add hover effect to buttons."""
        button.bind('<Enter>', lambda e: button.config(bg=hover_color))
        button.bind('<Leave>', lambda e: button.config(bg=normal_color))
        
    def create_card(self, parent, title):
        """Create a modern card widget."""
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat')
        
        # Card shadow effect
        card.configure(highlightbackground='#e5e7eb', highlightthickness=1)
        
        # Card title
        title_frame = tk.Frame(card, bg=self.colors['card'])
        title_frame.pack(fill='x', padx=15, pady=(15, 5))
        
        title_label = tk.Label(title_frame, text=title, 
                              font=('Segoe UI', 13, 'bold'),
                              bg=self.colors['card'], fg=self.colors['text'])
        title_label.pack(anchor='w')
        
        return card
    
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
    
    def log(self, message, color=None):
        """Add message to log with color coding."""
        # Configure tags for different message types
        self.log_text.tag_configure("success", foreground="#10b981")
        self.log_text.tag_configure("warning", foreground="#f59e0b")
        self.log_text.tag_configure("error", foreground="#ef4444")
        self.log_text.tag_configure("info", foreground="#3b82f6")
        
        # Determine color based on message content
        tag = None
        if color:
            tag = color
        elif "✅" in message or "Success" in message:
            tag = "success"
        elif "⚠" in message or "Warning" in message:
            tag = "warning"
        elif "❌" in message or "Error" in message or "✗" in message:
            tag = "error"
        elif "🎤" in message or "📁" in message or "⚡" in message:
            tag = "info"
        
        # Insert message with appropriate tag
        if tag:
            self.log_text.insert(tk.END, f"{message}\n", tag)
        else:
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
            
            # Get concurrent chunks setting
            max_concurrent = int(self.concurrent_var.get())
            
            # Create converter
            converter = TTSConverter(
                str(self.folder_path),
                voice=voice_name,
                chunk_min=chunk_min,
                chunk_max=chunk_max,
                progress_callback=self.update_progress,
                log_callback=self.log,
                max_concurrent_chunks=max_concurrent
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
                 progress_callback=None, log_callback=None, max_concurrent_chunks: int = 3):
        self.folder_path = Path(folder_path)
        self.voice = voice
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
        self.chunk_size_min = chunk_min
        self.chunk_size_max = chunk_max
        self.max_concurrent_chunks = max_concurrent_chunks
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
    
    async def generate_chunk_with_semaphore(self, semaphore: asyncio.Semaphore, chunk: str, index: int, prefix: str, total_chunks: int) -> tuple:
        """Generate a single chunk with semaphore control."""
        async with semaphore:
            self.progress_callback(f"Processing chunk {index}/{total_chunks}")
            try:
                chunk_file = await self.generate_chunk_audio(chunk, index, prefix)
                return (index, chunk_file, None)
            except Exception as e:
                return (index, None, str(e))

    async def generate_all_chunks(self, chunks: List[str], prefix: str) -> List[str]:
        """Generate audio files for all chunks with concurrent processing."""
        self.log_callback(f"🎤 Generating audio for {len(chunks)} chunks...")
        self.log_callback(f"⚡ Processing up to {self.max_concurrent_chunks} chunks simultaneously")
        self.progress_callback("Generating audio chunks concurrently...")
        
        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_concurrent_chunks)
        
        # Create tasks for all chunks
        tasks = []
        valid_chunk_count = 0
        
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():
                self.log_callback(f"⚠ Skipping empty chunk {i}")
                continue
            
            valid_chunk_count += 1
            task = self.generate_chunk_with_semaphore(semaphore, chunk, i, prefix, len(chunks))
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
            self.log_callback(f"\n⚠ Encountered {len(errors)} errors during chunk generation:")
            for index, error in errors:
                self.log_callback(f"  ✗ Chunk {index}: {error}")
        
        if not chunk_files:
            raise RuntimeError("No audio chunks were successfully generated")
        
        self.log_callback(f"✓ Successfully generated {len(chunk_files)} out of {valid_chunk_count} chunks")
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

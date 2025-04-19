# PlayMe v1.3 20250419.08:26
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from pygame import mixer
from mutagen.mp3 import MP3
import logger_playme
from logger_playme import log_error, log_debug

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        try:
            icon = tk.PhotoImage(file="/path/to/your/bin/Python/PlayMe/play-me_icon.png")
            self.root.iconphoto(False, icon)
        except Exception as e:
            log_error(f"Failed to load icon: {e}")
        log_debug("Starting PlayMe")
        self.root.title("PlayMe")
        self.root.geometry("610x380")
        self.root.resizable(0, 0)
        mixer.init()
        mixer.music.set_volume(0.7)
        log_debug("Mixer up")
        self.auto_next = False
        self.playlist_data = []
        self.song_duration = 0
        self.create_widgets()
        self.bind_shortcuts()
        self.root.after(1000, self.periodic_update)
        log_debug("Update per second scheduled")

    def create_widgets(self):
        log_debug("Create widgets")
        self.songs_frame = tk.LabelFrame(self.root, text="Playlist", font=("Arial", 12, "bold"), bg="black", fg="white")
        self.songs_frame.place(x=0, y=0, width=610, height=190)
        self.display_playlist = tk.Listbox(self.songs_frame, selectbackground="white", selectmode=tk.SINGLE, font=("Arial", 11, "italic"), bg="black", fg="white")
        self.scroll_y = tk.Scrollbar(self.songs_frame, orient=tk.VERTICAL, command=self.display_playlist.yview)
        self.scroll_x = tk.Scrollbar(self.songs_frame, orient=tk.HORIZONTAL, command=self.display_playlist.xview)
        self.display_playlist.config(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.display_playlist.pack(fill=tk.BOTH)
        self.display_playlist.bind("<Double-Button-1>", lambda e: self.play_song())
        self.metadata_label = tk.Label(self.root, text="Scooby Snacks for ALL!", font=("Arial", 11), bg="black", fg="white")
        self.metadata_label.place(x=0, y=190, width=610, height=50)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("whiteBlack.Horizontal.TProgressbar", troughcolor='black', bordercolor='black', background='white', lightcolor='white', darkcolor='white')
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, style="whiteBlack.Horizontal.TProgressbar")
        self.progress_bar.place(x=-1, y=240, width=612, height=20)
        self.control_frame = tk.LabelFrame(self.root, text="Controls", font=("Arial", 12, "bold"), bg="black", fg="white", padx=18, pady=5)
        self.control_frame.place(x=0, y=260, width=610, height=120)
        tk.Button(self.control_frame, text="Previous", width=8, font=("Arial", 10), fg="white", bg="black", command=self.play_previous_song).grid(row=0, column=0, padx=7, pady=5)
        tk.Button(self.control_frame, text="Play", width=8, font=("Arial", 10), fg="white", bg="black", command=self.play_song).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.control_frame, text="Next", width=8, font=("Arial", 10), fg="white", bg="black", command=self.play_next_song).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(self.control_frame, text="Pause", width=8, font=("Arial", 10), fg="white", bg="black", command=self.pause_song).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(self.control_frame, text="Resume", width=8, font=("Arial", 10), fg="white", bg="black", command=self.resume_song).grid(row=0, column=4, padx=5, pady=5)
        tk.Button(self.control_frame, text="Stop", width=8, font=("Arial", 10), fg="white", bg="black", command=self.stop_song).grid(row=0, column=5, padx=5, pady=5)
        tk.Button(self.control_frame, text="Clear", width=8, font=("Arial", 10), fg="white", bg="black", command=self.clear_playlist).grid(row=1, column=4, padx=5, pady=5)
        tk.Button(self.control_frame, text="Open", width=8, font=("Arial", 10), fg="white", bg="black", command=self.open_files).grid(row=1, column=5, padx=5, pady=5)
        tk.Button(self.control_frame, text="Save PL", width=8, font=("Arial", 10), fg="white", bg="black", command=self.save_playlist).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(self.control_frame, text="Load PL", width=8, font=("Arial", 10), fg="white", bg="black", command=self.load_playlist).grid(row=1, column=1, padx=5, pady=5)

        volume_label = tk.Label(self.control_frame, text="Volume", font=("Arial", 10), fg="white", bg="black")
        volume_label.grid(row=1, column=2, padx=5, pady=5)
        self.volume_slider = tk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL,command=self.volume_control, bg="black", fg="white", troughcolor="gray", highlightthickness=0)
        self.volume_slider.set(70)
        self.volume_slider.grid(row=1, column=3, padx=5, pady=5)
        log_debug("Widgets created")

    def bind_shortcuts(self):
        log_debug("Bind keyboard shortcuts")
        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("<n>", lambda e: self.play_next_song())
        self.root.bind("<b>", lambda e: self.play_previous_song())
        self.root.bind("<g>", lambda e: self.pause_song())
        self.root.bind("<h>", lambda e: self.resume_song())
        log_debug("Shortcuts bound")

    def volume_control(self, volume):
        vol = float(volume) / 100.0
        mixer.music.set_volume(vol)
        log_debug(f"Volume set to {vol:.2f}")

    def update_metadata(self, file_path):
        log_debug(f"Updating metadata for file: {file_path}")
        try:
            audio = MP3(file_path)
            title = audio.tags.get('TIT2', "Ruh Roh") if audio.tags else "Ruh Roh"
            artist = audio.tags.get('TPE1', "No Info Shaggy") if audio.tags else "No Info Shaggy"
            metadata_text = f"[ ON AIR ]     {title} ~ {artist}"
            self.song_duration = audio.info.length
            log_debug(f"Metadata read: Title='{title}', Artist='{artist}', Duration={self.song_duration:.2f} sec")
        except Exception as e:
            log_error(f"Error reading metadata: {e}")
            metadata_text = "[ ON AIR ] Ruh-Roh! No Meta Scooby Snacks Here"
            self.song_duration = 0
        self.metadata_label.config(text=metadata_text)
        self.progress_bar.config(maximum=self.song_duration if self.song_duration else 100)
        self.progress_var.set(0)

    def update_progress(self):
        if self.song_duration > 0 and mixer.music.get_busy():
            pos = mixer.music.get_pos() / 1000.0
            if pos > self.song_duration:
                pos = self.song_duration
            self.progress_var.set(pos)
            log_debug(f"Progress updated: {pos:.2f} sec")
        else:
            self.progress_var.set(0)

    def play_song(self):
        log_debug("Attempting to play selected song")
        try:
            index = self.display_playlist.curselection()[0]
            log_debug(f"Selected song index: {index}")
        except IndexError:
            messagebox.showinfo("Info", "Please select a song to play.")
            log_debug("No song selected to play")
            return
        file_path = self.playlist_data[index]
        try:
            mixer.music.load(file_path)
            log_debug(f"Loaded song file: {file_path}")
            mixer.music.play()
            log_debug("Playback started")
            self.update_metadata(file_path)
            self.auto_next = True
            log_debug("Auto next enabled")
        except Exception as e:
            log_error(f"Error playing song: {e}")
            log_debug(f"Error playing song: {e}")
            self.metadata_label.config(text="Error playing song.")

    def play_next_song(self):
        log_debug("Attempting to play next song")
        if not self.auto_next:
            log_debug("Auto next disabled; skipping next song")
            return
        try:
            index = self.display_playlist.curselection()[0]
            log_debug(f"Current song index for next song: {index}")
        except IndexError:
            index = 0
            log_debug("No current selection; defaulting to index 0 for next song")
        next_index = index + 1
        if next_index < len(self.playlist_data):
            self.display_playlist.selection_clear(0, tk.END)
            self.display_playlist.selection_set(next_index)
            self.display_playlist.activate(next_index)
            log_debug(f"Switching to next song at index {next_index}")
            self.play_song()
        else:
            self.auto_next = False
            log_debug("Reached end of playlist; disabling auto next")

    def play_previous_song(self):
        log_debug("Attempting to play previous song")
        try:
            index = self.display_playlist.curselection()[0]
            log_debug(f"Current song index for previous song: {index}")
        except IndexError:
            index = 0
            log_debug("No current selection; defaulting to index 0 for previous song")
        prev_index = index - 1
        if prev_index >= 0:
            self.display_playlist.selection_clear(0, tk.END)
            self.display_playlist.selection_set(prev_index)
            self.display_playlist.activate(prev_index)
            log_debug(f"Switching to previous song at index {prev_index}")
            self.play_song()
        else:
            self.auto_next = False
            log_debug("No previous song available; disabling auto next")

    def stop_song(self):
        log_debug("Stopping song")
        mixer.music.stop()
        self.metadata_label.config(text='')
        self.auto_next = False
        self.progress_var.set(0)

    def pause_song(self):
        log_debug("Pausing song")
        mixer.music.pause()
        self.auto_next = False

    def resume_song(self):
        log_debug("Resuming song")
        mixer.music.unpause()
        self.auto_next = True

    def toggle_play_pause(self):
        log_debug("Toggle play/pause triggered")
        if mixer.music.get_busy():
            log_debug("Music currently playing; pausing")
            self.pause_song()
        else:
            try:
                index = self.display_playlist.curselection()[0]
                log_debug(f"Resuming playback for selected song at index {index}")
            except IndexError:
                if self.playlist_data:
                    log_debug("No song selected; defaulting to first song to play")
                    self.display_playlist.selection_set(0)
                    self.play_song()
                    return
                else:
                    log_debug("Playlist empty; nothing to play")
                    return
            self.resume_song()

    def open_files(self):
        log_debug("Opening file dialog to select songs")
        files = filedialog.askopenfilenames(
            title="Where's the Scooby Snacks?",
            filetypes=(("MP3 Files", "*.mp3"), ("Ogg Files", "*.ogg"), ("Flac Files", "*.flac"), ("All Files", "*.*"))
        )
        log_debug(f"Files selected: {files}")
        self.add_file_paths(files)

    def add_file_paths(self, file_paths):
        log_debug("Adding selected file paths to playlist")
        count = 0
        for file in file_paths:
            if os.path.exists(file):
                self.playlist_data.append(file)
                self.display_playlist.insert(tk.END, os.path.basename(file))
                count += 1
                log_debug(f"Added: {file}")
            else:
                log_debug(f"File does not exist and was skipped: {file}")
        log_debug(f"Total files added: {count}")

    def clear_playlist(self):
        log_debug("Clearing playlist")
        self.playlist_data.clear()
        self.display_playlist.delete(0, tk.END)
        self.metadata_label.config(text='')
        self.auto_next = False
        self.progress_var.set(0)

    def save_playlist(self):
        log_debug("Saving playlist")
        if not self.playlist_data:
            messagebox.showinfo("Info", "No songs to save in playlist.")
            log_debug("Save playlist aborted: no songs")
            return
        file_path = filedialog.asksaveasfilename(
            title="Save Playlist",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    for song in self.playlist_data:
                        f.write(song + "\n")
                log_debug(f"Playlist saved successfully to {file_path}")
            except Exception as e:
                log_error(f"Error saving playlist: {e}")
                log_debug(f"Error saving playlist: {e}")
                messagebox.showerror("Error", "Could not save playlist.")

    def load_playlist(self):
        log_debug("Loading playlist from file")
        file_path = filedialog.askopenfilename(
            title="Load Playlist",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    lines = f.readlines()
                self.clear_playlist()
                for line in lines:
                    song_path = line.strip()
                    if os.path.exists(song_path):
                        self.playlist_data.append(song_path)
                        self.display_playlist.insert(tk.END, os.path.basename(song_path))
                        log_debug(f"Loaded song: {song_path}")
                    else:
                        log_debug(f"File does not exist while loading playlist: {song_path}")
                log_debug("Playlist loaded successfully")
            except Exception as e:
                log_error(f"Error loading playlist: {e}")
                log_debug(f"Error loading playlist: {e}")
                messagebox.showerror("Error", "Could not load playlist.")

    def periodic_update(self):
        self.update_progress()
        if self.auto_next and not mixer.music.get_busy():
            log_debug("No music playing and auto_next enabled; attempting to play next song")
            self.play_next_song()
        self.root.after(1000, self.periodic_update)

def main():
    log_debug("Starting PlayMe")
    try:
        os.chdir(r"/path/to/your/Music")
        log_debug("Changed directory to /path/to/your/Music")
    except Exception as e:
        log_error(f"Could not change directory: {e}")
        log_debug(f"Could not change directory: {e}")
    root = tk.Tk()
    app = MusicPlayer(root)
    if len(sys.argv) > 1:
        file_args = sys.argv[1:]
        log_debug(f"Command-line file arguments: {file_args}")
        app.add_file_paths(file_args)
    log_debug("Entering main event loop")
    root.mainloop()

if __name__ == "__main__":
    main()

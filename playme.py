# PlayMe v1.4.1 20250429.05:16 | Added cli option --stream-url=, cli file support, updated META info display 
import os, sys, vlc
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pygame import mixer
from mutagen.mp3 import MP3
import logger_playme
from logger_playme import log_error, log_debug

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        try:
            icon = tk.PhotoImage(file="~/bin/Python/PlayMe/play-me_icon.png")
            self.root.iconphoto(False, icon)
        except Exception as e:
            log_error(f"Failed to load: {e}")
        log_debug("Starting PlayMe")
        self.root.title("PlayMe")
        self.root.geometry("610x380")
        self.root.resizable(0, 0)
        mixer.init()
        mixer.music.set_volume(0.8)
        log_debug("Mixer up")
        self.auto_next = False
        self.playlist_data = []
        self.song_duration = 0
        self.vlc_instance = vlc.Instance()
        self.stream_player = None
        self.create_widgets()
        self.bind_shortcuts()
        self.root.after(1000, self.periodic_update)
        log_debug("Update per sec set")

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
        tk.Button(self.control_frame, text="Previous", width=8, font=("Arial", 9), fg="white", bg="black", command=self.play_previous_song).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(self.control_frame, text="Play", width=8, font=("Arial", 9), fg="white", bg="black", command=self.play_song).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.control_frame, text="Next", width=8, font=("Arial", 9), fg="white", bg="black", command=self.play_next_song).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(self.control_frame, text="Pause", width=8, font=("Arial", 9), fg="white", bg="black", command=self.pause_song).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(self.control_frame, text="Resume", width=8, font=("Arial", 9), fg="white", bg="black", command=self.resume_song).grid(row=0, column=4, padx=5, pady=5)
        tk.Button(self.control_frame, text="Stop", width=8, font=("Arial", 9), fg="white", bg="black", command=self.stop_song).grid(row=0, column=5, padx=5, pady=5)
        tk.Button(self.control_frame, text="Save PL", width=8, font=("Arial", 9), fg="white", bg="black", command=self.save_playlist).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(self.control_frame, text="Load PL", width=8, font=("Arial", 9), fg="white", bg="black", command=self.load_playlist).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.control_frame, text="Clear", width=8, font=("Arial", 9), fg="white", bg="black", command=self.clear_playlist).grid(row=1, column=2, padx=5, pady=5)
        tk.Button(self.control_frame, text="Open", width=8, font=("Arial", 9), fg="white", bg="black", command=self.open_files).grid(row=1, column=3, padx=5, pady=5)
        tk.Button(self.control_frame, text="Stream", width=8, font=("Arial", 9), fg="white", bg="black", command=self.play_stream).grid(row=1, column=4, padx=5, pady=5)
        self.volume_slider = tk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.volume_control, bg="black", fg="white", troughcolor="gray", highlightthickness=0, width=8)
        self.volume_slider.set(80)
        self.volume_slider.grid(row=1, column=5)
        log_debug("Widgets created")

    def bind_shortcuts(self):
        log_debug("Bind keyboard shortcuts")
        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("<n>", lambda e: self.play_next_song())
        self.root.bind("<p>", lambda e: self.play_previous_song())
        self.root.bind("<o>", lambda e: self.open_files())
        self.root.bind("<s>", lambda e: self.save_playlist())
        self.root.bind("<l>", lambda e: self.load_playlist())
        self.root.bind("<r>", lambda e: self.play_stream())
        log_debug("Shortcuts bound")

    def volume_control(self, volume):
        vol = float(volume) / 100.0
        mixer.music.set_volume(vol)
        if self.stream_player:
            self.stream_player.audio_set_volume(int(vol * 100))
        log_debug(f"Volume at {vol:.2f}")

    def update_metadata(self, file_path):
        log_debug(f"Updating metadata: {file_path}")
        try:
            audio = MP3(file_path)
            title = audio.tags.get('TIT2', "Ruh Roh") if audio.tags else "Ruh Roh"
            artist = audio.tags.get('TPE1', "No Info Shaggy") if audio.tags else "No Info Shaggy"
            metadata_text = f"[ ON AIR ] {title} ~ {artist}"
            self.song_duration = audio.info.length
            log_debug(f"Metadata: Title='{title}', Artist='{artist}', Duration={self.song_duration:.2f} sec")
        except Exception as e:
            log_error(f"Error reading metadata: {e}")
            metadata_text = "[ ON AIR ] Ruh-Roh! No Meta Scooby Snacks"
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
        if self.stream_player:
            self.stop_stream()
        try:
            index = self.display_playlist.curselection()[0]
            log_debug(f"Selected song index: {index}")
        except IndexError:
            messagebox.showinfo("Info", "Please select a song.")
            log_debug("No song selected")
            return
        file_path = self.playlist_data[index]
        try:
            mixer.music.load(file_path)
            log_debug(f"Loaded: {file_path}")
            mixer.music.play()
            log_debug("Playback started")
            self.update_metadata(file_path)
            self.auto_next = True
            log_debug("Auto next enabled")
        except Exception as e:
            log_error(f"Error playing: {e}")
            log_debug(f"Error playing: {e}")
            self.metadata_label.config(text="Error playing.")

    def play_stream(self):
        log_debug("Attempting to stream URL")
        self.stop_song()
        if self.stream_player:
            self.stop_stream()
        url = simpledialog.askstring("Stream URL", "Enter stream URL:")
        if not url:
            log_debug("No URL provided")
            return
        try:
            media = self.vlc_instance.media_new(url)
            self.stream_player = self.vlc_instance.media_player_new()
            self.stream_player.set_media(media)
            media.add_option("network-caching=300")  # caching in ms
            self.stream_player.play()
            self.metadata_label.config(text=f"[ STREAMING ] ...{url[-45:]}")
            log_debug(f"Streaming: {url}")
        except Exception as e:
            log_error(f"Error streaming: {e}")
            messagebox.showerror("Error", "Could not stream URL.")
            self.stream_player = None

    def stop_stream(self):
        if self.stream_player:
            log_debug("Stopping stream")
            self.stream_player.stop()
            self.stream_player = None
            self.metadata_label.config(text="")
            self.progress_var.set(0)

    def play_next_song(self):
        log_debug("Attempting to play next")
        if not self.auto_next:
            log_debug("Auto next disabled; skipping next song")
            return
        try:
            index = self.display_playlist.curselection()[0]
            log_debug(f"Current index next song: {index}")
        except IndexError:
            index = 0
            log_debug("No selection; defaulting to index 0")
        next_index = index + 1
        if next_index < len(self.playlist_data):
            self.display_playlist.selection_clear(0, tk.END)
            self.display_playlist.selection_set(next_index)
            self.display_playlist.activate(next_index)
            log_debug(f"Switching to {next_index}")
            self.play_song()
        else:
            self.auto_next = False
            log_debug("Reached end playlist; disabling auto next")

    def play_previous_song(self):
        log_debug("Attempting to play previous")
        try:
            index = self.display_playlist.curselection()[0]
            log_debug(f"Current index previous: {index}")
        except IndexError:
            index = 0
            log_debug("No current selection; defaulting to index 0")
        prev_index = index - 1
        if prev_index >= 0:
            self.display_playlist.selection_clear(0, tk.END)
            self.display_playlist.selection_set(prev_index)
            self.display_playlist.activate(prev_index)
            log_debug(f"Switching to previous index {prev_index}")
            self.play_song()
        else:
            self.auto_next = False
            log_debug("No previous song available; disabling auto next")

    def stop_song(self):
        log_debug("Stopping playback")
        mixer.music.stop()
        self.metadata_label.config(text='')
        self.auto_next = False
        self.progress_var.set(0)
        self.stop_stream()

    def pause_song(self):
        log_debug("Pausing")
        if mixer.music.get_busy():
            mixer.music.pause()
        if self.stream_player:
            self.stream_player.set_pause(1)
        self.auto_next = False

    def resume_song(self):
        log_debug("Resuming")
        if not mixer.music.get_busy() and self.display_playlist.curselection():
            mixer.music.unpause()
        if self.stream_player:
            self.stream_player.set_pause(0)
        self.auto_next = True

    def toggle_play_pause(self):
        log_debug("Toggle play/pause")
        if mixer.music.get_busy() or (self.stream_player and self.stream_player.is_playing()):
            log_debug("Audio currently playing; pausing")
            self.pause_song()
        else:
            try:
                index = self.display_playlist.curselection()[0]
                log_debug(f"Resuming playback at index {index}")
            except IndexError:
                if self.playlist_data:
                    log_debug("No song selected; defaulting to first")
                    self.display_playlist.selection_set(0)
                    self.play_song()
                    return
                else:
                    log_debug("Playlist empty; nothing to play")
                    return
            self.resume_song()

    def open_files(self):
        log_debug("Opening file dialog to select")
        files = filedialog.askopenfilenames(title="Where's the Scooby Snacks?",filetypes=(("MP3 Files", "*.mp3"), ("Ogg Files", "*.ogg"), ("Flac Files", "*.flac"), ("All Files", "*.*")))
        log_debug(f"Files selected: {files}")
        self.add_file_paths(files)

    def add_file_paths(self, file_paths):
        log_debug("Adding selected files to playlist")
        count = 0
        for file in file_paths:
            if os.path.exists(file):
                self.playlist_data.append(file)
                self.display_playlist.insert(tk.END, os.path.basename(file))
                count += 1
                log_debug(f"Added: {file}")
            else:
                log_debug(f"File does not exist, skipped: {file}")
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
        file_path = filedialog.asksaveasfilename(title="Save Playlist",defaultextension=".txt",filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "w") as f:
                    for song in self.playlist_data:
                        f.write(song + "\n")
                log_debug(f"Playlist saved {file_path}")
            except Exception as e:
                log_error(f"Error saving: {e}")
                log_debug(f"Error saving: {e}")
                messagebox.showerror("Error", "Could not save pl.")

    def load_playlist(self):
        log_debug("Loading playlist")
        file_path = filedialog.askopenfilename(title="Load Playlist",defaultextension=".txt",filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
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
                        log_debug(f"File does not exist: {song_path}")
                log_debug("Playlist loaded")
            except Exception as e:
                log_error(f"Error loading: {e}")
                log_debug(f"Error loading: {e}")
                messagebox.showerror("Error", "Could not load playlist.")

    def periodic_update(self):
        self.update_progress()
        if self.auto_next and not mixer.music.get_busy():
            log_debug("No music playing and auto_next enabled; attempting to play next song")
            self.play_next_song()
        self.root.after(1000, self.periodic_update)
    
    def play_stream_from_url(self, url):
        log_debug("Attempting to stream URL")
        self.stop_song()
        if self.stream_player:
            self.stop_stream()
        try:
            media = self.vlc_instance.media_new(url)
            self.stream_player = self.vlc_instance.media_player_new()
            self.stream_player.set_media(media)
            media.add_option("network-caching=300")  # caching in ms
            self.stream_player.play()
            self.metadata_label.config(text=f"[ STREAMING ] ...{url[-45:]}")
            log_debug(f"Streaming started from URL: {url}")
        except Exception as e:
            log_error(f"Error streaming URL: {e}")
            messagebox.showerror("Error", "Could not stream audio from the provided URL.")
            self.stream_player = None

def main():
    log_debug("Starting PlayMe")
    stream_url = None
    try:
        os.chdir(r"~/Music")
        log_debug("cd to ~/Music")
    except Exception as e:
        log_error(f"Could not change: {e}")
        log_debug(f"Could not change: {e}")
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--stream-url="):
                stream_url = arg.split("=")[1]
                log_debug(f"Stream URL: {stream_url}")
    root = tk.Tk()
    app = MusicPlayer(root)
    if len(sys.argv) > 1:
        file_args = [arg for arg in sys.argv[1:] if not arg.startswith("--stream-url=")]
        log_debug(f"Command-line arguments: {file_args}")
        app.add_file_paths(file_args)
    if stream_url:
        app.play_stream_from_url(stream_url)

    log_debug("Starting mainloop")
    root.mainloop()

if __name__ == "__main__":
    main()

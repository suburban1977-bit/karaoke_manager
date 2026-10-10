import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

_VLC_DLL_DIRECTORY = None
if getattr(sys, "frozen", False):
    bundled_vlc_dir = os.path.join(
        getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)),
        "vlc",
    )
    if os.path.isdir(bundled_vlc_dir):
        os.environ["PATH"] = bundled_vlc_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ["VLC_PLUGIN_PATH"] = os.path.join(bundled_vlc_dir, "plugins")
        if hasattr(os, "add_dll_directory"):
            _VLC_DLL_DIRECTORY = os.add_dll_directory(bundled_vlc_dir)

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("customtkinter is required. Install it with: pip install customtkinter")

try:
    import vlc
except ImportError:
    raise SystemExit("python-vlc is required. Install it with: pip install python-vlc")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SUPPORTED_EXTENSIONS = (
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm",
    ".mp3", ".wav", ".flac"
)

def get_vlc_args_for_main():
    return ["--quiet"]

def get_vlc_args_for_ext():
    return ["--quiet", "--no-audio"]

class VideoWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Karaoke Video Display (2nd Screen)")
        self.geometry("800x450")
        self.configure(bg="#050811")
        self.is_fullscreen = False

        self.video_panel = tk.Canvas(self, bg="#050811", highlightthickness=0)
        self.video_panel.pack(fill="both", expand=True)

        self.bind("<Escape>", lambda event: self.set_fullscreen(False))
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_fullscreen(self, state=True):
        self.is_fullscreen = state
        self.attributes("-fullscreen", self.is_fullscreen)
        self.update_idletasks()

    def on_close(self):
        self.set_fullscreen(False)
        self.withdraw()


class LocalKaraokeQueueApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Local Karaoke Queue Manager - Interactive Queue List")
        self.geometry("1360x950")
        self.minsize(1200, 800)
        self.configure(fg_color="#070C16")

        self.music_folder = ""
        self.local_files = []
        self.queue = []
        self.current_track = None
        self.is_repeat = False
        self.is_paused = False
        self.is_muted = False
        self.volume_level = 100
        self.is_user_seeking = False
        self.vlc_available = False
        self.queue_widgets = {}

        self.external_video_window = VideoWindow(self)
        self.external_video_window.withdraw()

        self._setup_vlc()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        page = ctk.CTkFrame(self, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=20, pady=20)
        page.grid_columnconfigure((0, 1), weight=1)
        page.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="KARAOKE NIGHT STUDIO",
            text_color="#38BDF8",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Interactive Queue Manager",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(2, 0))

        self.select_folder_btn = ctk.CTkButton(
            header,
            text="📁 Select Music/Video Folder",
            height=42,
            corner_radius=10,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            border_width=1,
            border_color="#334155",
            command=self.choose_music_folder,
        )
        self.select_folder_btn.grid(row=0, column=1, sticky="e")

        left_panel = ctk.CTkFrame(
            page,
            fg_color="#0F172A",
            corner_radius=18,
            border_width=1,
            border_color="#1E293B",
        )
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(1, weight=1)

        search_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_row.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        search_row.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search song title...",
            height=40,
            corner_radius=10,
            border_color="#334155",
            fg_color="#020617",
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.search_entry.bind("<Return>", lambda _e: self.search_local_files())

        self.clear_search_btn = ctk.CTkButton(
            search_row,
            text="✕ Clear",
            width=65,
            height=40,
            corner_radius=10,
            fg_color="#1E293B",
            hover_color="#334155",
            command=self.clear_search,
        )
        self.clear_search_btn.grid(row=0, column=1, padx=(0, 6))

        self.search_btn = ctk.CTkButton(
            search_row,
            text="Search",
            width=80,
            height=40,
            corner_radius=10,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.search_local_files,
        )
        self.search_btn.grid(row=0, column=2)

        self.results_frame = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 12))

        right_panel = ctk.CTkFrame(
            page,
            fg_color="#0F172A",
            corner_radius=18,
            border_width=1,
            border_color="#1E293B",
        )
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(2, weight=1)

        self.now_playing_frame = ctk.CTkFrame(
            right_panel,
            fg_color="#020617",
            corner_radius=12,
            border_width=1,
            border_color="#1E293B",
        )
        self.now_playing_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            self.now_playing_frame,
            text="NOW PLAYING",
            anchor="w",
            text_color="#38BDF8",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(9, 2))

        self.now_playing_label = ctk.CTkLabel(
            self.now_playing_frame,
            text="Nothing playing yet",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.now_playing_label.pack(anchor="w", fill="x", padx=12, pady=(0, 10))

        queue_heading = ctk.CTkFrame(right_panel, fg_color="transparent")
        queue_heading.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        queue_heading.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            queue_heading,
            text="QUEUE",
            anchor="w",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.queue_count_label = ctk.CTkLabel(
            queue_heading,
            text="0 songs",
            anchor="e",
            text_color="#64748B",
            font=ctk.CTkFont(size=10),
        )
        self.queue_count_label.grid(row=0, column=1, sticky="e")

        queue_box = ctk.CTkFrame(
            right_panel,
            fg_color="#0B1120",
            corner_radius=12,
            border_width=1,
            border_color="#334155",
        )
        queue_box.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))

        self.queue_scrollable = ctk.CTkScrollableFrame(
            queue_box, fg_color="transparent"
        )
        self.queue_scrollable.pack(fill="both", expand=True, padx=8, pady=8)

        self.video_frame = ctk.CTkFrame(right_panel, fg_color="#000000", height=160, corner_radius=12)
        self.video_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 8))

        seek_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        seek_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 6))
        seek_frame.grid_columnconfigure(1, weight=1)

        self.time_label_curr = ctk.CTkLabel(
            seek_frame,
            text="00:00",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
        )
        self.time_label_curr.grid(row=0, column=0, padx=(0, 8))

        self.seek_slider = ctk.CTkSlider(
            seek_frame,
            from_=0,
            to=1000,
            number_of_steps=1000,
            command=self.on_seek,
            button_color="#38BDF8",
            button_hover_color="#0284C7",
        )
        self.seek_slider.set(0)
        self.seek_slider.grid(row=0, column=1, sticky="ew")
        self.seek_slider.bind("<ButtonPress-1>", lambda e: self._start_seek())
        self.seek_slider.bind("<ButtonRelease-1>", lambda e: self._end_seek())

        self.time_label_total = ctk.CTkLabel(
            seek_frame,
            text="00:00",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
        )
        self.time_label_total.grid(row=0, column=2, padx=(8, 0))

        audio_frame = ctk.CTkFrame(
            right_panel,
            fg_color="#020617",
            corner_radius=12,
            border_width=1,
            border_color="#1E293B",
        )
        audio_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 8))
        audio_frame.grid_columnconfigure(1, weight=1)

        self.mute_btn = ctk.CTkButton(
            audio_frame,
            text="🔊 Sound: ON",
            width=110,
            height=32,
            corner_radius=8,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.toggle_mute,
        )
        self.mute_btn.grid(row=0, column=0, padx=(12, 10), pady=8)

        self.volume_slider = ctk.CTkSlider(
            audio_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.on_volume_change,
            button_color="#38BDF8",
            button_hover_color="#0284C7",
        )
        self.volume_slider.set(100)
        self.volume_slider.grid(row=0, column=1, sticky="ew", padx=4, pady=8)

        self.volume_label = ctk.CTkLabel(
            audio_frame,
            text="100%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
            width=45,
        )
        self.volume_label.grid(row=0, column=2, padx=(4, 12), pady=8)

        screen_controls_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        screen_controls_frame.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 8))
        screen_controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.open_screen_btn = ctk.CTkButton(
            screen_controls_frame,
            text="📺 Open 2nd Screen",
            height=32,
            corner_radius=8,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.open_second_screen,
        )
        self.open_screen_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.fullscreen_btn = ctk.CTkButton(
            screen_controls_frame,
            text="⛶ Fullscreen",
            height=32,
            corner_radius=8,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.enable_fullscreen,
        )
        self.fullscreen_btn.grid(row=0, column=1, sticky="ew", padx=2)

        self.exit_fullscreen_btn = ctk.CTkButton(
            screen_controls_frame,
            text="✕ Exit Screen",
            height=32,
            corner_radius=8,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.close_second_screen,
        )
        self.exit_fullscreen_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        controls_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        controls_frame.grid(row=7, column=0, sticky="ew", padx=16, pady=(0, 12))
        controls_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.play_button = ctk.CTkButton(
            controls_frame,
            text="▶ Play Next",
            height=40,
            corner_radius=10,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.play_next,
        )
        self.play_button.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self.pause_button = ctk.CTkButton(
            controls_frame,
            text="⏸ Pause",
            height=40,
            corner_radius=10,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_pause,
        )
        self.pause_button.grid(row=0, column=1, sticky="ew", padx=3)

        self.stop_button = ctk.CTkButton(
            controls_frame,
            text="⏹ Stop",
            height=40,
            corner_radius=10,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.stop_playback,
        )
        self.stop_button.grid(row=0, column=2, sticky="ew", padx=3)

        self.repeat_button = ctk.CTkButton(
            controls_frame,
            text="🔁 Repeat: OFF",
            height=40,
            corner_radius=10,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_repeat,
        )
        self.repeat_button.grid(row=0, column=3, sticky="ew", padx=3)

        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="Clear Queue",
            height=40,
            corner_radius=10,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.clear_queue,
        )
        self.clear_button.grid(row=0, column=4, sticky="ew", padx=(3, 0))

        ctk.CTkLabel(
            page,
            text="made by David/Daviro",
            text_color="#64748B",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=2, column=0, columnspan=2, sticky="e", pady=(4, 0))

        self.after(500, self._bind_main_window)
        self.update_progress_timer()

    def _setup_vlc(self):
        try:
            self.vlc_instance_main = vlc.Instance(*get_vlc_args_for_main())
            self.media_player_main = self.vlc_instance_main.media_player_new()

            self.vlc_instance_ext = vlc.Instance(*get_vlc_args_for_ext())
            self.media_player_ext = self.vlc_instance_ext.media_player_new()

            self.media_player_main.audio_set_volume(self.volume_level)
            self.media_player_main.audio_set_mute(self.is_muted)

            self.vlc_available = True
        except Exception as e:
            messagebox.showerror(
                "VLC Engine Error",
                f"VLC initialization failed: {e}\n\nMake sure VLC Media Player is installed on this computer.",
            )
            self.vlc_available = False

    def _bind_main_window(self):
        if not self.vlc_available:
            return
        try:
            self.video_frame.update_idletasks()
            handle = self.video_frame.winfo_id()
            if handle:
                if sys.platform.startswith("win"):
                    self.media_player_main.set_hwnd(handle)
                else:
                    self.media_player_main.set_xwindow(handle)
        except Exception:
            pass

    def _bind_external_window(self):
        if not self.vlc_available:
            return
        try:
            self.external_video_window.update_idletasks()
            handle = self.external_video_window.video_panel.winfo_id()
            if handle:
                if sys.platform.startswith("win"):
                    self.media_player_ext.set_hwnd(handle)
                else:
                    self.media_player_ext.set_xwindow(handle)
        except Exception:
            pass

    def _set_main_state_from_media(self, path):
        if not self.vlc_available:
            return
        try:
            self.media_player_main.stop()
        except Exception:
            pass

        try:
            media = self.vlc_instance_main.media_new(path)
            self.media_player_main.set_media(media)
            self.media_player_main.audio_set_volume(self.volume_level)
            self.media_player_main.audio_set_mute(self.is_muted)
            self._bind_main_window()
            self.media_player_main.play()
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play main media: {e}")

    def _set_external_state_from_media(self, path):
        if not self.vlc_available:
            return
        if not self.external_video_window.winfo_viewable():
            return

        try:
            self.media_player_ext.stop()
        except Exception:
            pass

        try:
            self.external_video_window.update_idletasks()
            media = self.vlc_instance_ext.media_new(path)
            self.media_player_ext.set_media(media)
            self._bind_external_window()
            if self.media_player_main.get_state() in (vlc.State.Playing, vlc.State.Paused):
                self.media_player_ext.play()
                pos = self.media_player_main.get_position()
                if pos >= 0:
                    self.media_player_ext.set_position(pos)
        except Exception as e:
            print(f"Secondary screen playback error: {e}")

    def choose_music_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.music_folder = folder
            self.scan_folder()

    def scan_folder(self):
        self.local_files.clear()
        for root, _, files in os.walk(self.music_folder):
            for file in files:
                if file.lower().endswith(SUPPORTED_EXTENSIONS):
                    self.local_files.append((os.path.splitext(file)[0], os.path.join(root, file)))
        self.search_local_files()

    def clear_search(self):
        self.search_entry.delete(0, "end")
        self.search_local_files()

    def search_local_files(self):
        for w in self.results_frame.winfo_children():
            w.destroy()

        query = self.search_entry.get().strip().casefold()
        matches = [
            (name, path) for name, path in self.local_files
            if not query or query in name.casefold()
        ][:50]

        if not matches:
            ctk.CTkLabel(self.results_frame, text="No matching songs found.", text_color="#64748B").pack(pady=20)
            return

        for _, (name, path) in enumerate(matches):
            card = ctk.CTkFrame(self.results_frame, fg_color="#1E293B", corner_radius=10)
            card.pack(fill="x", padx=4, pady=3)

            ctk.CTkLabel(
                card,
                text=name,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left", padx=12, pady=8, expand=True, fill="x")

            ctk.CTkButton(
                card,
                text="＋ Add",
                width=60,
                height=28,
                fg_color="#0284C7",
                hover_color="#0369A1",
                command=lambda n=name, p=path: self.add_to_queue(n, p),
            ).pack(side="right", padx=8)

    def add_to_queue(self, name, path):
        self.queue.append((name, path))
        self.refresh_queue()

    def refresh_queue(self):
        for w in self.queue_scrollable.winfo_children():
            w.destroy()

        count = len(self.queue)
        self.queue_count_label.configure(text=f"{count} song{'s' if count != 1 else ''}")

        if not self.queue:
            ctk.CTkLabel(self.queue_scrollable, text="Queue is empty.", text_color="#64748B").pack(pady=20)
            return

        for idx, (name, _) in enumerate(self.queue):
            row = ctk.CTkFrame(self.queue_scrollable, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#334155")
            row.pack(fill="x", padx=2, pady=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row, text=f"{idx + 1}. {name}", anchor="w",
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=0, column=0, sticky="w", padx=10, pady=8)

            ctk.CTkButton(
                row, text="▶", width=35, height=26,
                fg_color="#0284C7", hover_color="#0369A1",
                command=lambda q_idx=idx: self.play_queued_track(q_idx)
            ).grid(row=0, column=1, padx=(4, 2), pady=4)

            ctk.CTkButton(
                row, text="↑", width=35, height=26,
                fg_color="#64748B", hover_color="#94A3B8",
                command=lambda q_idx=idx: self.move_up(q_idx)
            ).grid(row=0, column=2, padx=2, pady=4)

            ctk.CTkButton(
                row, text="↓", width=35, height=26,
                fg_color="#64748B", hover_color="#94A3B8",
                command=lambda q_idx=idx: self.move_down(q_idx)
            ).grid(row=0, column=3, padx=2, pady=4)

            ctk.CTkButton(
                row, text="✕", width=35, height=26,
                fg_color="#334155", hover_color="#B91C1C",
                command=lambda q_idx=idx: self.remove_from_queue(q_idx)
            ).grid(row=0, column=4, padx=(2, 8), pady=4)

    def play_queued_track(self, index):
        if not 0 <= index < len(self.queue):
            return
        if not self.vlc_available:
            messagebox.showerror("VLC Required", "VLC is not initialized.")
            return

        _, path = self.queue.pop(index)
        self.refresh_queue()
        self._play_track(path)

    def move_up(self, index):
        if index > 0:
            self.queue[index], self.queue[index - 1] = self.queue[index - 1], self.queue[index]
            self.refresh_queue()

    def move_down(self, index):
        if index < len(self.queue) - 1:
            self.queue[index], self.queue[index + 1] = self.queue[index + 1], self.queue[index]
            self.refresh_queue()

    def remove_from_queue(self, index):
        if not 0 <= index < len(self.queue):
            return
        self.queue.pop(index)
        self.refresh_queue()

    def toggle_pause(self):
        if not self.vlc_available or not self.current_track:
            return

        state = self.media_player_main.get_state()
        if state in (vlc.State.Playing, vlc.State.Paused):
            if state == vlc.State.Playing:
                self.media_player_main.pause()
                if self.external_video_window.winfo_viewable():
                    self.media_player_ext.pause()
                self.is_paused = True
                self.pause_button.configure(text="▶ Resume", fg_color="#0284C7", hover_color="#0369A1")
            else:
                self.media_player_main.play()
                if self.external_video_window.winfo_viewable():
                    self.media_player_ext.play()
                self.is_paused = False
                self.pause_button.configure(text="⏸ Pause", fg_color="#1E293B", hover_color="#334155")

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.vlc_available:
            self.media_player_main.audio_set_mute(self.is_muted)
            if self.external_video_window.winfo_viewable():
                self.media_player_ext.audio_set_mute(True)

        if self.is_muted:
            self.mute_btn.configure(text="🔇 Muted", fg_color="#DC2626", hover_color="#B91C1C")
        else:
            self.mute_btn.configure(text="🔊 Sound: ON", fg_color="#1E293B", hover_color="#334155")

    def on_volume_change(self, value):
        self.volume_level = int(value)
        self.volume_label.configure(text=f"{self.volume_level}%")
        if self.vlc_available:
            self.media_player_main.audio_set_volume(self.volume_level)

    def _start_seek(self):
        self.is_user_seeking = True

    def _end_seek(self):
        self.is_user_seeking = False

    def on_seek(self, value):
        if not self.vlc_available:
            return
        if self.media_player_main.get_state() in (vlc.State.Playing, vlc.State.Paused):
            pos = float(value) / 1000.0
            self.media_player_main.set_position(pos)
            if self.external_video_window.winfo_viewable():
                self.media_player_ext.set_position(pos)

    def update_progress_timer(self):
        if self.vlc_available and not self.is_user_seeking:
            if self.current_track:
                state = self.media_player_main.get_state()
                if state in (vlc.State.Playing, vlc.State.Paused):
                    pos = self.media_player_main.get_position()
                    if pos >= 0:
                        self.seek_slider.set(pos * 1000)

                    time_ms = self.media_player_main.get_time()
                    length_ms = self.media_player_main.get_length()

                    if time_ms >= 0:
                        s = int(time_ms / 1000)
                        self.time_label_curr.configure(text=f"{s // 60:02d}:{s % 60:02d}")

                    if length_ms > 0:
                        s_total = int(length_ms / 1000)
                        self.time_label_total.configure(text=f"{s_total // 60:02d}:{s_total % 60:02d}")

                elif state == vlc.State.Ended:
                    if self.is_repeat and self.current_track:
                        _, path = self.current_track
                        self._play_track(path)
                    elif self.queue:
                        self.play_next()
                    else:
                        self.seek_slider.set(0)
                        self.time_label_curr.configure(text="00:00")
                        self.now_playing_label.configure(text="Playback finished")

        self.after(250, self.update_progress_timer)

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        if self.is_repeat:
            self.repeat_button.configure(text="🔁 Repeat: ON", fg_color="#2563EB", hover_color="#1D4ED8")
        else:
            self.repeat_button.configure(text="🔁 Repeat: OFF", fg_color="#1E293B", hover_color="#334155")

    def open_second_screen(self):
        self.external_video_window.deiconify()
        self.external_video_window.attributes("-topmost", True)
        self.external_video_window.update()
        if self.current_track:
            _, path = self.current_track
            self._set_external_state_from_media(path)

    def enable_fullscreen(self):
        self.open_second_screen()
        self.external_video_window.set_fullscreen(True)

    def close_second_screen(self):
        self.external_video_window.attributes("-topmost", False)
        self.external_video_window.set_fullscreen(False)
        try:
            self.media_player_ext.stop()
        except Exception:
            pass
        self.external_video_window.withdraw()

    def _play_track(self, path):
        if not self.vlc_available:
            messagebox.showerror("VLC Required", "VLC Media Player is not initialized.")
            return

        name = os.path.splitext(os.path.basename(path))[0]
        self.current_track = (name, path)
        self.now_playing_label.configure(text=name)
        self.is_paused = False
        self.pause_button.configure(text="⏸ Pause", fg_color="#1E293B", hover_color="#334155")

        self._set_main_state_from_media(path)
        if self.external_video_window.winfo_viewable():
            self._set_external_state_from_media(path)

    def play_next(self):
        if not self.queue:
            return

        _, path = self.queue.pop(0)
        self.refresh_queue()
        self._play_track(path)

    def stop_playback(self):
        if self.vlc_available:
            try:
                self.media_player_main.stop()
                self.media_player_ext.stop()
            except Exception:
                pass
            self.is_paused = False
            self.current_track = None
            self.now_playing_label.configure(text="Nothing playing yet")
            self.pause_button.configure(text="⏸ Pause", fg_color="#1E293B", hover_color="#334155")
            self.seek_slider.set(0)
            self.time_label_curr.configure(text="00:00")
            self.time_label_total.configure(text="00:00")

    def clear_queue(self):
        self.queue.clear()
        self.refresh_queue()

    def close_app(self):
        if self.vlc_available:
            try:
                self.media_player_main.stop()
                self.media_player_ext.stop()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = LocalKaraokeQueueApp()
    app.mainloop()

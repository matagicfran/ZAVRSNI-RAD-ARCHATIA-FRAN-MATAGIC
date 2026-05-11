import tkinter as tk
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from core.detector import ArchitectureDetector
from core.image_processor import prepare_image
from core.model_loader import ModelManager
from gui.styles import COLORS, FONTS, LAYOUT
from gui.widgets import Card, Divider, SectionLabel, SidebarButton
from utils.helpers import (
    clear_analysis_history,
    load_analysis_history,
    save_analysis_history,
    shorten_filename,
)


class EnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARCHATIA")
        self._set_window_icon()
        self.root.geometry("1560x880")
        self.root.minsize(1240, 720)
        self.root.configure(bg=COLORS["app_bg"])

        # Podaci o trenutno odabranoj slici
        self.selected_image_path = None
        self.processed_image_path = None
        self.preview_photo = None
        self.model_manager = ModelManager()
        self.detector = ArchitectureDetector(self.model_manager)
        self.analysis_history = load_analysis_history()
        self.last_analysis_results = []
        self.workspace_accepts_new_image = True
        self.model_loading = True
        self.splash = None
        self.splash_logo_photo = None
        self.splash_spinner_step = 0
        self.splash_status_label = None
        self.splash_progress_label = None
        self.first_model_download = False
        self.fade_step = 0
        self.fade_overlay = None
        self.lightbox = None
        self.lightbox_photo = None
        self.lightbox_fade_step = 0
        self.lightbox_base_image = None
        self.lightbox_image_frame = None
        self.lightbox_image_label = None
        self.lightbox_close_button = None
        self.lightbox_image_item = None
        self.lightbox_close_box = None
        self.lightbox_close_text = None
        self.lightbox_image_bounds = None
        self.lightbox_close_bounds = None
        self.drop_enabled = False

        self.setup_ui()
        self._sync_analyze_button()
        self._load_models_async()

    def _set_window_icon(self):
        icon_path = self._asset_path("archatialogo.ico")
        if not icon_path.exists():
            return

        try:
            self.root.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

    def _asset_path(self, filename):
        return Path(__file__).resolve().parent.parent / "assets" / filename

    def setup_ui(self):
        # Glavni dijelovi prozora
        self._build_shell()
        self._build_sidebar()
        self._build_history()
        self._build_main()
        self._set_status("")
        self._show_splash_loading()
        self._animate_splash_spinner()

    def _build_shell(self):
        # Lijevi izbornik
        self.sidebar = tk.Frame(
            self.root,
            bg=COLORS["panel_bg_alt"],
            width=LAYOUT["sidebar_width"],
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Srednji panel za povijest analiza
        self.history_panel = tk.Frame(
            self.root,
            bg=COLORS["panel_bg"],
            width=LAYOUT["history_width"],
        )
        self.history_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(1, 0))
        self.history_panel.pack_propagate(False)

        # Glavni dio aplikacije
        self.main = tk.Frame(self.root, bg=COLORS["app_bg"])
        self.main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _build_sidebar(self):
        # Naziv aplikacije
        brand = tk.Frame(self.sidebar, bg=COLORS["panel_bg_alt"])
        brand.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(28, 20))

        tk.Label(
            brand,
            text="ARCHATIA",
            font=FONTS["brand"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        tk.Label(
            brand,
            text="Analiza arhitektonskog stila",
            font=FONTS["small"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

        Divider(self.sidebar).pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 22))

        # Gumbi za osnovne radnje
        SectionLabel(self.sidebar, text="Radnje", bg=COLORS["panel_bg_alt"]).pack(
            anchor="w", padx=LAYOUT["panel_pad"], pady=(0, 10)
        )

        self.btn_select = SidebarButton(
            self.sidebar,
            text="Odaberi sliku",
            icon="+",
            variant="primary",
            command=self.select_image,
        )
        self.btn_select.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 10))

        self.btn_analyze = SidebarButton(
            self.sidebar,
            text="Analiziraj stil",
            icon=">",
            variant="secondary",
            command=self.analyze_style,
        )
        self.btn_analyze.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 10))

        self.btn_reset_workspace = SidebarButton(
            self.sidebar,
            text="Nova analiza",
            icon="↳",
            variant="fresh",
            command=self.reset_workspace,
        )
        self.btn_reset_workspace.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 10))

        self.btn_clear = SidebarButton(
            self.sidebar,
            text="Očisti povijest",
            icon="x",
            variant="danger",
            command=self.clear_history,
        )
        self.btn_clear.pack(fill=tk.X, padx=LAYOUT["panel_pad"])

        # Status aplikacije
        status = tk.Frame(self.sidebar, bg=COLORS["panel_bg_alt"])
        status.pack(side=tk.BOTTOM, fill=tk.X, padx=LAYOUT["panel_pad"], pady=24)

        SectionLabel(status, text="Status", bg=COLORS["panel_bg_alt"]).pack(anchor="w")
        self.status_label = tk.Label(
            status,
            text="",
            font=FONTS["body"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text_secondary"],
            justify="left",
            anchor="w",
            wraplength=LAYOUT["sidebar_width"] - (LAYOUT["panel_pad"] * 2),
        )
        self.status_label.pack(fill=tk.X, pady=(8, 0))

        self.progress_frame = tk.Frame(status, bg=COLORS["panel_bg_alt"])
        self.progress_frame.pack(fill=tk.X, pady=(10, 0))

        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            height=8,
            bg=COLORS["surface"],
            highlightthickness=0,
            bd=0,
        )
        self.progress_canvas.pack(fill=tk.X)

        self.progress_fill = self.progress_canvas.create_rectangle(
            0,
            0,
            0,
            8,
            fill=COLORS["accent"],
            width=0,
        )

        self.progress_label = tk.Label(
            status,
            text="0%",
            font=FONTS["small"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text_muted"],
            justify="left",
            anchor="w",
            wraplength=LAYOUT["sidebar_width"] - (LAYOUT["panel_pad"] * 2),
        )
        self.progress_label.pack(fill=tk.X, pady=(5, 0))
        self.progress_frame.pack_forget()
        self.progress_label.pack_forget()

    def _build_history(self):
        # Naslov povijesti analiza
        header = tk.Frame(self.history_panel, bg=COLORS["panel_bg"])
        header.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(26, 18))

        tk.Label(
            header,
            text="Povijest analiza",
            font=FONTS["title"],
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Prethodni rezultati prikazuju se ovdje.",
            font=FONTS["small"],
            bg=COLORS["panel_bg"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

        # Kartice povijesti analiza
        history_wrap = Card(self.history_panel, bg=COLORS["surface"])
        history_wrap.pack(
            fill=tk.BOTH,
            expand=True,
            padx=LAYOUT["panel_pad"],
            pady=(0, LAYOUT["panel_pad"]),
        )

        self.history_canvas = tk.Canvas(
            history_wrap,
            bg=COLORS["surface"],
            highlightthickness=0,
            bd=0,
        )
        self.history_scroll = tk.Scrollbar(
            history_wrap,
            orient=tk.VERTICAL,
            command=self.history_canvas.yview,
            width=LAYOUT["scrollbar_width"],
            bg=COLORS["accent_dark"],
            troughcolor=COLORS["panel_bg_alt"],
            activebackground=COLORS["accent"],
            relief=tk.FLAT,
            bd=0,
        )
        self.history_canvas.configure(yscrollcommand=self.history_scroll.set)
        self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.history_list = tk.Frame(self.history_canvas, bg=COLORS["surface"])
        self.history_window = self.history_canvas.create_window(
            (0, 0),
            window=self.history_list,
            anchor="nw",
        )
        self.history_list.bind("<Configure>", self._update_history_scroll)
        self.history_canvas.bind("<Configure>", self._resize_history_window)
        self._bind_history_mousewheel()
        self._render_history()

    def _build_main(self):
        # Desni glavni sadržaj
        content = tk.Frame(self.main, bg=COLORS["app_bg"])
        content.pack(
            fill=tk.BOTH,
            expand=True,
            padx=LAYOUT["outer_pad"],
            pady=LAYOUT["outer_pad"],
        )

        header = tk.Frame(content, bg=COLORS["app_bg"])
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Radna površina",
            font=FONTS["title"],
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT)

        tk.Label(
            content,
            text="Odaberite fotografiju građevine i pokrenite analizu stila.",
            font=FONTS["body"],
            bg=COLORS["app_bg"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 18))

        self._build_image_panel(content)
        self._build_results_panel(content)

    def _build_image_panel(self, parent):
        # Prozor za preview slike
        self.image_card = Card(parent, bg=COLORS["surface"], height=340)
        self.image_card.pack(fill=tk.X)
        self.image_card.pack_propagate(False)

        self.image_preview_frame = tk.Frame(self.image_card, bg=COLORS["surface"])
        self.image_preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 10))

        # Dio gdje se prikazuje sama slika
        self.image_area = tk.Frame(self.image_preview_frame, bg=COLORS["surface"])
        self.image_area.pack(fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(
            self.image_area,
            text="📷",
            font=FONTS["empty_icon"],
            bg=COLORS["surface"],
            fg=COLORS["accent"],
        )
        self.image_label.pack(expand=True)
        self.image_label.bind("<Button-1>", self._open_image_lightbox)

        # Tekst ispod previewa slike
        self.image_info_frame = tk.Frame(self.image_preview_frame, bg=COLORS["surface"])
        self.image_info_frame.pack(fill=tk.X, pady=(10, 0))

        self.image_title_label = tk.Label(
            self.image_info_frame,
            text="Nije odabrana slika",
            font=FONTS["section"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
            anchor="center",
        )
        self.image_title_label.pack(fill=tk.X)

        self.image_hint_label = tk.Label(
            self.image_info_frame,
            text="Koristite gumb 'Odaberi sliku' ili povucite fotografiju ovdje.",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            anchor="center",
            wraplength=760,
        )
        self.image_hint_label.pack(fill=tk.X, pady=(3, 0))
        self._setup_drag_and_drop()

    def _setup_drag_and_drop(self):
        # Drag-and-drop radi kada je dostupan tkinterdnd2 root.
        try:
            from tkinterdnd2 import DND_FILES
        except ImportError:
            self._setup_windows_drag_and_drop()
            return

        drop_widgets = (
            self.image_card,
            self.image_preview_frame,
            self.image_area,
            self.image_label,
            self.image_info_frame,
            self.image_title_label,
            self.image_hint_label,
        )

        for widget in drop_widgets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._handle_image_drop)
                widget.dnd_bind("<<DragEnter>>", self._handle_drag_enter)
                widget.dnd_bind("<<DragLeave>>", self._handle_drag_leave)
            except tk.TclError:
                self._setup_windows_drag_and_drop()
                return

        self.drop_enabled = True

    def _setup_windows_drag_and_drop(self):
        # Fallback za Windows kada tkinterdnd2 nije dostupan.
        try:
            import windnd
        except ImportError:
            return

        drop_widgets = (
            self.image_card,
            self.image_preview_frame,
            self.image_area,
            self.image_label,
            self.image_info_frame,
            self.image_title_label,
            self.image_hint_label,
        )

        for widget in drop_widgets:
            try:
                windnd.hook_dropfiles(widget, func=self._handle_windnd_drop)
            except Exception:
                continue

        self.drop_enabled = True

    def _handle_windnd_drop(self, files):
        if not files:
            return

        first_file = files[0]
        if isinstance(first_file, bytes):
            first_file = first_file.decode("utf-8", errors="ignore")
        self._load_dropped_image(first_file)

    def _handle_drag_enter(self, _event):
        self.image_card.configure(highlightbackground=COLORS["accent"])
        self.image_hint_label.configure(text="Otpustite fotografiju za odabir.")

    def _handle_drag_leave(self, _event):
        self.image_card.configure(highlightbackground=COLORS["border_soft"])
        self._refresh_image_hint()

    def _handle_image_drop(self, event):
        self.image_card.configure(highlightbackground=COLORS["border_soft"])
        dropped_paths = self.root.tk.splitlist(event.data)
        if not dropped_paths:
            self._refresh_image_hint()
            return

        self._load_dropped_image(dropped_paths[0])

    def _load_dropped_image(self, dropped_path):
        if not self.workspace_accepts_new_image:
            self._set_status("Za novu sliku prvo odaberite 'Nova analiza'.")
            self._refresh_image_hint()
            return

        image_path = Path(dropped_path)
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            messagebox.showwarning(
                "Nepodržana datoteka",
                "Povucite JPG, PNG, BMP ili WEBP fotografiju građevine.",
            )
            self._refresh_image_hint()
            return

        self._load_selected_image(image_path)

    def _refresh_image_hint(self):
        if self.selected_image_path:
            self.image_hint_label.configure(text=str(self.selected_image_path))
        else:
            self.image_hint_label.configure(
                text="Koristite gumb 'Odaberi sliku' ili povucite fotografiju ovdje."
            )

    def _build_results_panel(self, parent):
        # Prozor za rezultate analize
        header = tk.Frame(parent, bg=COLORS["app_bg"])
        header.pack(fill=tk.X, pady=(24, 10))

        tk.Label(
            header,
            text="Rezultati analize",
            font=FONTS["title"],
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT)

        results_wrap = Card(parent, bg=COLORS["surface"])
        results_wrap.pack(fill=tk.BOTH, expand=True)

        self.results_back_button = tk.Button(
            results_wrap,
            text="Povratak",
            font=FONTS["button"],
            bg=COLORS["surface_hover"],
            fg=COLORS["text"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["panel_bg_alt"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self._return_to_results,
            padx=14,
            pady=8,
        )

        self.results_text = tk.Text(
            results_wrap,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["body"],
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            padx=LAYOUT["card_padx"],
            pady=LAYOUT["card_pady"],
            cursor="arrow",
            insertwidth=0,
            selectbackground=COLORS["accent_dark"],
            selectforeground=COLORS["text"],
        )

        results_scroll = tk.Scrollbar(
            results_wrap,
            orient=tk.VERTICAL,
            command=self.results_text.yview,
            width=LAYOUT["scrollbar_width"],
            bg=COLORS["surface_soft"],
            troughcolor=COLORS["panel_bg"],
            activebackground=COLORS["accent"],
            relief=tk.FLAT,
            bd=0,
        )
        self.results_text.configure(yscrollcommand=results_scroll.set)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_back_button.pack_forget()

        # Stilovi za tekst rezultata
        self.results_text.tag_configure(
            "title",
            font=FONTS["section"],
            foreground=COLORS["accent"],
            spacing3=10,
        )
        self.results_text.tag_configure(
            "normal",
            font=FONTS["body"],
            foreground=COLORS["text_secondary"],
            spacing3=6,
        )
        self.results_text.tag_configure(
            "muted",
            font=FONTS["body"],
            foreground=COLORS["text_muted"],
            spacing3=6,
        )
        self.results_text.tag_configure(
            "high",
            font=FONTS["body_bold"],
            foreground="#8DD694",
            spacing3=6,
        )
        self.results_text.tag_configure(
            "medium",
            font=FONTS["body_bold"],
            foreground=COLORS["accent"],
            spacing3=6,
        )
        self.results_text.tag_configure(
            "low",
            font=FONTS["body_bold"],
            foreground="#DFA08E",
            spacing3=6,
        )

        self._show_model_loading_message()

    def select_image(self):
        # Otvaranje prozora za odabir slike
        if not self.workspace_accepts_new_image:
            self._set_status("Za novu sliku prvo odaberite 'Nova analiza'.")
            return

        file_path = filedialog.askopenfilename(
            title="Odaberi sliku",
            filetypes=(
                ("Slikovne datoteke", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Sve datoteke", "*.*"),
            ),
        )
        if not file_path:
            return

        self._load_selected_image(file_path)

    def _load_selected_image(self, file_path):
        # Ucitavanje slike iz dijaloga ili drag-and-drop zone
        try:
            self._show_image_preview(file_path)
            processing_result = prepare_image(file_path)
            self.processed_image_path = processing_result["processed_path"]
            self._show_selected_image_info(Path(file_path), processing_result)
            if self._current_image_has_history():
                self._show_already_analyzed_message()
            self.workspace_accepts_new_image = False
            self._sync_analyze_button()
        except ImportError:
            messagebox.showerror(
                "Nedostaje biblioteka",
                "Za prikaz slike potrebno je instalirati Pillow:\n\npip install -r requirements.txt",
            )
            self._set_status("Pillow nije instaliran.")
            self._sync_analyze_button()
        except Exception as error:
            messagebox.showerror(
                "Greška pri učitavanju slike",
                f"Sliku nije moguće prikazati.\n\n{error}",
            )
            self._set_status("Odabrana slika se ne može prikazati.")
            self._sync_analyze_button()

    def analyze_style(self):
        # Pokretanje analize odabrane slike
        if not self.selected_image_path:
            messagebox.showwarning(
                "Nije odabrana slika",
                "Prvo odaberite sliku za analizu.",
            )
            return

        if self._current_image_has_history():
            self._set_status("Ova slika je već u povijesti analiza.")
            self._sync_analyze_button()
            return

        image_path = self.processed_image_path or self.selected_image_path
        self._set_status("Analiza je u tijeku...")
        self._show_analysis_loading()
        self.btn_analyze.configure(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._analyze_style_worker,
            args=(image_path,),
            daemon=True,
        )
        thread.start()

    def _analyze_style_worker(self, image_path):
        try:
            results = self.detector.detect(image_path, top_k=5)
            self.root.after(0, lambda: self._show_analysis_results(results))
        except Exception as error:
            self.root.after(0, lambda error=error: self._show_analysis_error(error))

    def _show_analysis_loading(self):
        # Kratka poruka dok se analiza izvodi
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Analiza je u tijeku\n", "title")
        self.results_text.insert(
            tk.END,
            "Molimo pričekajte dok sustav uspoređuje sliku s arhitektonskim stilovima.",
            "normal",
        )
        self.results_text.configure(state=tk.DISABLED)

    def _show_analysis_results(self, results, save_to_history=True):
        # Prikaz rezultata analize u GUI-u
        self.last_analysis_results = results
        self.results_back_button.pack_forget()
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Arhitektonski stil\n", "title")

        if not results:
            self.results_text.insert(tk.END, "Nije pronađen rezultat analize.", "normal")
        else:
            self.results_text.insert(
                tk.END,
                "Najvjerojatniji stilovi prema odabranoj slici:\n\n",
                "normal",
            )
            for index, result in enumerate(results, start=1):
                percent = result["confidence"] * 100
                level_label, level_tag, level_icon, _level_color = self._confidence_level(percent)
                result_tag = f"result_{index}"
                self.results_text.insert(
                    tk.END,
                    f"{index}. {self._display_style_name(result['name'])}\n",
                    ("normal", result_tag),
                )
                self.results_text.insert(
                    tk.END,
                    f"{level_icon} Pouzdanost: {level_label} ({percent:.1f}%)\n\n",
                    (level_tag, result_tag),
                )
                self.results_text.tag_configure(result_tag, lmargin1=0, lmargin2=0)
                self.results_text.tag_bind(
                    result_tag,
                    "<Button-1>",
                    lambda _event, item=result: self._show_style_details(item),
                )
                self.results_text.tag_bind(
                    result_tag,
                    "<Enter>",
                    lambda _event: self.results_text.configure(cursor="hand2"),
                )
                self.results_text.tag_bind(
                    result_tag,
                    "<Leave>",
                    lambda _event: self.results_text.configure(cursor="arrow"),
                )
            if save_to_history:
                self._add_history_entry(results[0], results)

        self.results_text.configure(state=tk.DISABLED)
        self._sync_analyze_button()
        self._set_status("Analiza je završena.")

    def _show_analysis_error(self, error):
        # Prikaz greške ako analiza ne uspije
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Analiza nije uspjela\n", "title")
        self.results_text.insert(tk.END, str(error), "normal")
        self.results_text.configure(state=tk.DISABLED)
        self._sync_analyze_button()
        self._set_status("Analiza nije uspjela.")

    def _show_model_loading_message(self, dots="..."):
        # Poruka u rezultatima dok se AI model učitava
        self.results_back_button.pack_forget()
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, f"AI model se učitava{dots}\n", "title")
        self.results_text.insert(
            tk.END,
            "Pričekajte trenutak prije analize slike.",
            "normal",
        )
        self.results_text.configure(state=tk.DISABLED)

    def _show_ready_message(self):
        # Početna poruka nakon što je AI model spreman
        self.results_back_button.pack_forget()
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "ARCHATIA je spremna\n", "title")
        self.results_text.insert(
            tk.END,
            "Odaberite fotografiju građevine i pokrenite analizu stila.",
            "normal",
        )
        self.results_text.configure(state=tk.DISABLED)

    def _show_model_error_message(self):
        # Poruka ako se AI model ne uspije učitati
        self.results_back_button.pack_forget()
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "AI model nije učitan\n", "title")
        self.results_text.insert(
            tk.END,
            "Provjerite internet vezu i instalirane biblioteke pa ponovno pokrenite program.",
            "normal",
        )
        self.results_text.configure(state=tk.DISABLED)

    def _show_splash_loading(self):
        if self.splash and self.splash.winfo_exists():
            return

        self.splash = tk.Frame(self.root, bg=COLORS["app_bg"])
        self.splash.configure(bg=COLORS["app_bg"])
        self.splash.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.splash.lift()

        container = tk.Frame(self.splash, bg=COLORS["app_bg"])
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            container,
            text="🏛️",
            font=("Segoe UI Emoji", 70),
            bg=COLORS["app_bg"],
            fg=COLORS["accent"],
        ).pack(pady=(0, 14))

        tk.Label(
            container,
            text="ARCHATIA",
            font=("Segoe UI", 34, "bold"),
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
        ).pack()

        self.splash_status_label = tk.Label(
            container,
            text="Učitavanje modela",
            font=("Segoe UI", 13),
            bg=COLORS["app_bg"],
            fg=COLORS["text_muted"],
        )
        self.splash_status_label.pack(pady=(8, 0))

        self.splash_progress_label = tk.Label(
            container,
            text="",
            font=FONTS["small"],
            bg=COLORS["app_bg"],
            fg=COLORS["text_muted"],
        )
        self.splash_progress_label.pack(pady=(5, 0))

        self.splash_spinner = tk.Canvas(
            container,
            width=82,
            height=82,
            bg=COLORS["app_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.splash_spinner.pack(pady=(28, 0))
        self.root.update_idletasks()

    def _animate_splash_spinner(self):
        if not self.model_loading or not self.splash or not self.splash.winfo_exists():
            return

        self.splash.lift()
        self.splash_spinner.delete("all")
        start = (self.splash_spinner_step * 22) % 360
        self.splash_spinner.create_oval(
            12,
            12,
            70,
            70,
            outline=COLORS["surface_soft"],
            width=7,
        )
        self.splash_spinner.create_arc(
            12,
            12,
            70,
            70,
            start=start,
            extent=105,
            outline=COLORS["accent"],
            width=7,
            style=tk.ARC,
        )
        self.splash_spinner_step += 1
        self.root.after(55, self._animate_splash_spinner)

    def _hide_splash_loading(self):
        if self.splash and self.splash.winfo_exists():
            self.splash.destroy()
        self.splash = None
        self.splash_status_label = None
        self.splash_progress_label = None

    def _fade_in_main_content(self):
        if self.fade_overlay and self.fade_overlay.winfo_exists():
            self.fade_overlay.destroy()

        self.fade_step = 0
        self.fade_overlay = tk.Frame(self.root, bg=COLORS["app_bg"])
        self.fade_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.fade_overlay.lift()
        self._fade_overlay_step()

    def _fade_overlay_step(self):
        if not self.fade_overlay or not self.fade_overlay.winfo_exists():
            return

        shades = (
            COLORS["app_bg"],
            "#242421",
            "#292824",
            "#2E2C28",
            "#33312C",
        )
        if self.fade_step >= len(shades):
            self.fade_overlay.destroy()
            self.fade_overlay = None
            return

        self.fade_overlay.configure(bg=shades[self.fade_step])
        self.fade_step += 1
        self.root.after(35, self._fade_overlay_step)

    def _show_style_details(self, result):
        # Detalji odabranog ponuđenog stila
        percent = result["confidence"] * 100
        level_label, level_tag, level_icon, _level_color = self._confidence_level(percent)
        features = ", ".join(result.get("features", [])[:5]) or "nisu spremljeni"
        materials = ", ".join(result.get("materials", [])[:4]) or "nije spremljeno"
        regions = ", ".join(result.get("regions", [])[:4]) or "nije spremljeno"

        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, f"{self._display_style_name(result['name'])}\n", "title")
        self.results_text.insert(
            tk.END,
            f"{level_icon} Pouzdanost: {level_label} ({percent:.1f}%)\n\n",
            level_tag,
        )
        self.results_text.insert(tk.END, "Što je ovaj stil?\n", "title")
        self.results_text.insert(
            tk.END,
            (
                f"Razdoblje: {result.get('period', 'nije navedeno')}\n"
                f"Najčešće regije: {regions}\n"
                f"Materijali: {materials}\n\n"
            ),
            "normal",
        )
        self.results_text.insert(tk.END, "Zašto ga je sustav odabrao?\n", "title")
        self.results_text.insert(
            tk.END,
            f"Najvažniji vizualni tragovi: {features}.\n\n",
            "normal",
        )
        self.results_text.configure(state=tk.DISABLED)
        self.results_back_button.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(0, 16))

    def _return_to_results(self):
        # Povratak s detalja stila na popis rezultata
        if self.last_analysis_results:
            self._show_analysis_results(self.last_analysis_results, save_to_history=False)

    def _confidence_level(self, percent):
        # Razina pouzdanosti prema postotku rezultata
        if percent >= 60:
            return "velika", "high", "🟢", "#8DD694"
        if percent >= 30:
            return "srednja", "medium", "🟡", COLORS["accent"]
        return "mala", "low", "🔴", "#DFA08E"

    def _display_style_name(self, style_name):
        # Kraci nazivi su citljiviji u karticama i rezultatima.
        aliases = {
            "Staroegipatska arhitektura": "Egipat",
            "Klasična grčka arhitektura": "Grčka",
            "Rimska arhitektura": "Rim",
            "Bizantska arhitektura": "Bizant",
            "Islamska arhitektura": "Islam",
            "Viktorijanska arhitektura": "Viktorijanski",
            "High-tech arhitektura": "High-tech",
            "Suvremena arhitektura": "Suvremena",
            "Organska arhitektura": "Organska",
            "Vernakularna arhitektura": "Vernakularna",
            "Mediteranska arhitektura": "Mediteranska",
            "Osmanska arhitektura": "Osmanska",
            "Mogulska arhitektura": "Mogulska",
            "Tradicionalna kineska arhitektura": "Kineska",
            "Tradicionalna japanska arhitektura": "Japanska",
            "Održiva / zelena arhitektura": "Održiva / zelena",
        }
        if style_name in aliases:
            return aliases[style_name]
        return style_name.replace(" arhitektura", "").replace(" Arhitektura", "")

    def _show_image_preview(self, file_path):
        # Učitavanje odabrane slike u preview
        image_path = self._load_preview_image(file_path)
        self.selected_image_path = image_path
        self._set_status("Slika je odabrana. Spremno za analizu.")

    def _load_preview_image(self, file_path):
        # Prikaz slike u preview prozoru
        from PIL import Image, ImageOps, ImageTk

        image_path = Path(file_path)
        self.root.update_idletasks()

        max_width = max(self.image_preview_frame.winfo_width() - 40, 360)
        max_height = 205

        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        self.preview_photo = ImageTk.PhotoImage(image)

        self.image_label.configure(
            image=self.preview_photo,
            text="",
            width=max_width,
            height=max_height,
            cursor="hand2",
        )
        self.image_title_label.configure(text=image_path.name)
        self.image_hint_label.configure(
            text=str(image_path),
            wraplength=max(self.image_preview_frame.winfo_width() - 60, 360),
        )
        return image_path

    def _open_image_lightbox(self, _event=None):
        if not self.selected_image_path:
            return

        image_path = Path(self.selected_image_path)
        if not image_path.exists():
            return

        try:
            from PIL import Image, ImageOps, ImageTk
        except ImportError:
            messagebox.showerror(
                "Nedostaje biblioteka",
                "Za uvećani prikaz slike potrebno je instalirati Pillow:\n\npip install -r requirements.txt",
            )
            return

        if self.lightbox and self.lightbox.winfo_exists():
            self.lightbox.destroy()

        self.root.update_idletasks()
        max_width = max(int(self.root.winfo_width() * 0.78), 420)
        max_height = max(int(self.root.winfo_height() * 0.76), 320)

        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        self.lightbox_base_image = image.copy()
        self.lightbox_photo = ImageTk.PhotoImage(self.lightbox_base_image)

        overlay_bg = "#171612"
        self.lightbox = tk.Canvas(
            self.root,
            bg=overlay_bg,
            highlightthickness=0,
            bd=0,
        )
        self.lightbox.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lightbox.lift()
        self.lightbox.bind("<Button-1>", self._handle_lightbox_click)
        self.lightbox.bind("<Escape>", self._close_image_lightbox)
        self.root.bind("<Escape>", self._close_image_lightbox, add="+")
        self.lightbox.focus_set()

        self.lightbox_image_item = self.lightbox.create_image(
            0,
            0,
            image=self.lightbox_photo,
            anchor="center",
        )

        self.lightbox_close_box = self.lightbox.create_rectangle(
            0,
            0,
            44,
            44,
            fill=COLORS["accent"],
            outline="",
        )
        self.lightbox_close_text = self.lightbox.create_text(
            0,
            0,
            text="×",
            font=("Segoe UI", 22, "bold"),
            fill="#111111",
        )
        self.lightbox.itemconfigure(self.lightbox_close_text, text="x")
        self.lightbox.bind("<Configure>", lambda _event: self._position_lightbox_items(), add="+")
        self.lightbox.update_idletasks()
        self._position_lightbox_items()

        self.lightbox_fade_step = 0
        self.root.after(20, self._animate_lightbox_fade)

    def _animate_lightbox_fade(self):
        if not self.lightbox or not self.lightbox.winfo_exists():
            return

        if not self.lightbox_base_image:
            return

        shades = ("#22201C", "#1F1D19", "#1C1A16", "#191713", "#171612")
        scales = (0.90, 0.94, 0.97, 0.99, 1.0)
        if self.lightbox_fade_step < len(shades):
            from PIL import Image, ImageTk

            shade = shades[self.lightbox_fade_step]
            scale = scales[self.lightbox_fade_step]
            width = max(1, int(self.lightbox_base_image.width * scale))
            height = max(1, int(self.lightbox_base_image.height * scale))
            animated_image = self.lightbox_base_image.resize((width, height), Image.Resampling.LANCZOS)
            self.lightbox_photo = ImageTk.PhotoImage(animated_image)

            self.lightbox.configure(bg=shade)
            self.lightbox.itemconfigure(self.lightbox_image_item, image=self.lightbox_photo)
            self.lightbox.update_idletasks()
            self._position_lightbox_items()
            self.lightbox_fade_step += 1
            self.root.after(34, self._animate_lightbox_fade)

    def _position_lightbox_items(self):
        if not self.lightbox or not self.lightbox.winfo_exists():
            return
        if not self.lightbox_photo:
            return
        if not self.lightbox_image_item or not self.lightbox_close_box or not self.lightbox_close_text:
            return

        canvas_width = max(self.lightbox.winfo_width(), self.root.winfo_width(), 1)
        canvas_height = max(self.lightbox.winfo_height(), self.root.winfo_height(), 1)
        image_width = self.lightbox_photo.width()
        image_height = self.lightbox_photo.height()
        center_x = canvas_width // 2
        center_y = canvas_height // 2
        left = center_x - (image_width // 2)
        top = center_y - (image_height // 2)
        right = left + image_width
        bottom = top + image_height

        self.lightbox_image_bounds = (left, top, right, bottom)
        self.lightbox.coords(self.lightbox_image_item, center_x, center_y)

        size = 44
        close_left = right - size
        close_top = top
        self.lightbox_close_bounds = (
            close_left,
            close_top,
            close_left + size,
            close_top + size,
        )
        close_center_x = close_left + (size // 2)
        close_center_y = close_top + (size // 2)
        self.lightbox.coords(self.lightbox_close_box, *self.lightbox_close_bounds)
        self.lightbox.coords(self.lightbox_close_text, close_center_x, close_center_y - 2)
        self.lightbox.tag_raise(self.lightbox_close_box)
        self.lightbox.tag_raise(self.lightbox_close_text)

    def _handle_lightbox_click(self, event):
        if self._point_in_bounds(event.x, event.y, self.lightbox_close_bounds):
            self._close_image_lightbox()
            return "break"
        if self._point_in_bounds(event.x, event.y, self.lightbox_image_bounds):
            return "break"
        self._close_image_lightbox()
        return "break"

    def _point_in_bounds(self, x, y, bounds):
        if not bounds:
            return False
        left, top, right, bottom = bounds
        return left <= x <= right and top <= y <= bottom

    def _close_image_lightbox(self, _event=None):
        if self.lightbox and self.lightbox.winfo_exists():
            self.lightbox.destroy()
        self.lightbox = None
        self.lightbox_photo = None
        self.lightbox_base_image = None
        self.lightbox_image_item = None
        self.lightbox_close_box = None
        self.lightbox_close_text = None
        self.lightbox_image_bounds = None
        self.lightbox_close_bounds = None

    def _open_image_lightbox(self, _event=None):
        if not self.selected_image_path:
            return

        image_path = Path(self.selected_image_path)
        if not image_path.exists():
            return

        try:
            from PIL import Image, ImageOps, ImageTk
        except ImportError:
            messagebox.showerror(
                "Nedostaje biblioteka",
                "Za uvecani prikaz slike potrebno je instalirati Pillow:\n\npip install -r requirements.txt",
            )
            return

        self._close_image_lightbox()
        self.root.update_idletasks()

        max_width = max(int(self.root.winfo_width() * 0.78), 420)
        max_height = max(int(self.root.winfo_height() * 0.76), 320)
        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        self.lightbox_base_image = image.copy()
        self.lightbox_photo = ImageTk.PhotoImage(self.lightbox_base_image)

        overlay_bg = "#171612"
        self.lightbox = tk.Frame(self.root, bg=overlay_bg)
        self.lightbox.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lightbox.lift()
        self.lightbox.bind("<Button-1>", self._handle_lightbox_click)
        self.lightbox.bind("<Escape>", self._close_image_lightbox)
        self.root.bind("<Escape>", self._close_image_lightbox, add="+")
        self.lightbox.focus_set()

        self.lightbox_image_frame = tk.Frame(self.lightbox, bg=overlay_bg)
        self.lightbox_image_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.lightbox_image_label = tk.Label(
            self.lightbox_image_frame,
            image=self.lightbox_photo,
            bg=overlay_bg,
            bd=0,
        )
        self.lightbox_image_label.pack()
        self.lightbox_image_label.bind("<Button-1>", lambda _event: "break")

        self.lightbox_close_button = tk.Button(
            self.lightbox,
            text="x",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS["accent"],
            fg="#111111",
            activebackground=COLORS["accent"],
            activeforeground="#111111",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            width=2,
            height=1,
            command=self._close_image_lightbox,
        )

        self.lightbox.update_idletasks()
        self._position_lightbox_items()
        self.lightbox_fade_step = 0
        self.root.after(20, self._animate_lightbox_fade)

    def _animate_lightbox_fade(self):
        if not self.lightbox or not self.lightbox.winfo_exists():
            return
        if not self.lightbox_base_image:
            return

        shades = ("#22201C", "#1F1D19", "#1C1A16", "#191713", "#171612")
        scales = (0.90, 0.94, 0.97, 0.99, 1.0)
        if self.lightbox_fade_step < len(shades):
            from PIL import Image, ImageTk

            shade = shades[self.lightbox_fade_step]
            scale = scales[self.lightbox_fade_step]
            width = max(1, int(self.lightbox_base_image.width * scale))
            height = max(1, int(self.lightbox_base_image.height * scale))
            animated_image = self.lightbox_base_image.resize((width, height), Image.Resampling.LANCZOS)
            self.lightbox_photo = ImageTk.PhotoImage(animated_image)

            self.lightbox.configure(bg=shade)
            self.lightbox_image_frame.configure(bg=shade)
            self.lightbox_image_label.configure(bg=shade, image=self.lightbox_photo)
            self.lightbox.update_idletasks()
            self._position_lightbox_items()
            self.lightbox_fade_step += 1
            self.root.after(34, self._animate_lightbox_fade)

    def _position_lightbox_items(self):
        if not self.lightbox or not self.lightbox.winfo_exists():
            return
        if not self.lightbox_image_frame or not self.lightbox_image_frame.winfo_exists():
            return
        if not self.lightbox_close_button or not self.lightbox_close_button.winfo_exists():
            return

        self.lightbox.update_idletasks()
        x = self.lightbox_image_frame.winfo_x() + self.lightbox_image_frame.winfo_width() - 44
        y = self.lightbox_image_frame.winfo_y()
        self.lightbox_close_button.place(x=x, y=y, width=44, height=44)
        self.lightbox_close_button.lift()

    def _handle_lightbox_click(self, _event=None):
        self._close_image_lightbox()
        return "break"

    def _close_image_lightbox(self, _event=None):
        if self.lightbox and self.lightbox.winfo_exists():
            self.lightbox.destroy()
        self.lightbox = None
        self.lightbox_photo = None
        self.lightbox_base_image = None
        self.lightbox_image_frame = None
        self.lightbox_image_label = None
        self.lightbox_close_button = None
        self.lightbox_image_item = None
        self.lightbox_close_box = None
        self.lightbox_close_text = None
        self.lightbox_image_bounds = None
        self.lightbox_close_bounds = None

    def _show_selected_image_info(self, image_path, processing_result):
        # Ispis osnovnih informacija o slici
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Slika je odabrana\n", "title")
        self.results_text.insert(
            tk.END,
            "Možete pokrenuti analizu.\n\n",
            "normal",
        )
        self.results_text.insert(tk.END, f"Naziv datoteke: {image_path.name}\n", "muted")
        self.results_text.insert(tk.END, f"Lokacija: {image_path}\n", "muted")
        self.results_text.configure(state=tk.DISABLED)

    def _show_already_analyzed_message(self):
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Slika je već analizirana\n", "title")
        self.results_text.insert(
            tk.END,
            "Rezultat za ovu fotografiju već postoji u povijesti analiza.",
            "normal",
        )
        self.results_text.configure(state=tk.DISABLED)
        self._set_status("Ova slika je već u povijesti analiza.")

    def reset_workspace(self):
        # Cisti samo radnu povrsinu i rezultate, povijest ostaje spremljena.
        self._close_image_lightbox()
        self.selected_image_path = None
        self.processed_image_path = None
        self.preview_photo = None
        self.last_analysis_results = []
        self.workspace_accepts_new_image = True
        self.results_back_button.pack_forget()

        self.image_label.configure(
            image="",
            text="📷",
            width=0,
            height=0,
            cursor="arrow",
        )
        self.image_title_label.configure(text="Nije odabrana slika")
        self.image_hint_label.configure(
            text="Koristite gumb 'Odaberi sliku' ili povucite fotografiju ovdje.",
            wraplength=max(self.image_preview_frame.winfo_width() - 60, 360),
        )

        if self.model_loading:
            self._set_status("")
            self._show_splash_loading()
            self._animate_splash_spinner()
            self._show_model_loading_message()
        else:
            self._set_status("Spremno za odabir slike.")
            self._show_ready_message()
        self._sync_analyze_button()

    def _set_status(self, message):
        # Promjena statusa u lijevom izborniku
        self.status_label.configure(text=message)

    def _load_models_async(self):
        # Učitavanje AI modela u pozadini da GUI ne zablokira
        self.first_model_download = False
        self._update_splash_model_message(0)
        thread = threading.Thread(target=self._load_models_worker, daemon=True)
        thread.start()

    def _load_models_worker(self):
        statuses = self.model_manager.load_all(self._thread_safe_progress)
        self.root.after(0, lambda: self._update_model_status(statuses))

    def _thread_safe_progress(self, value):
        # Sigurno osvježavanje progress bara iz pozadinske dretve
        self.root.after(0, lambda: self._set_model_progress(value))

    def _set_model_progress(self, value):
        # Popunjavanje progress bara za učitavanje modela
        value = max(0, min(100, int(value)))
        if value == 30:
            self.first_model_download = True
        self._update_splash_model_message(value)
        self.progress_label.configure(text=f"{value}%")

        width = max(self.progress_canvas.winfo_width(), 1)
        fill_width = int(width * (value / 100))
        self.progress_canvas.coords(self.progress_fill, 0, 0, fill_width, 8)

    def _update_splash_model_message(self, value):
        if not self.splash or not self.splash.winfo_exists():
            return

        if self.first_model_download and value < 95:
            title = "Prvo preuzimanje modela"
            detail = f"Preuzimanje može potrajati... {value}%"
        else:
            title = "Učitavanje modela"
            detail = f"{value}%"

        if self.splash_status_label and self.splash_status_label.winfo_exists():
            self.splash_status_label.configure(text=title)
        if self.splash_progress_label and self.splash_progress_label.winfo_exists():
            self.splash_progress_label.configure(text=detail)

    def _update_model_status(self, statuses):
        # Nakon učitavanja ostaje samo glavni status
        self.model_loading = False
        self._hide_splash_loading()
        self._fade_in_main_content()
        self._set_model_progress(100)
        self.progress_frame.pack_forget()
        self.progress_label.pack_forget()

        if all(status.loaded for status in statuses):
            if self.selected_image_path:
                self._set_status("Slika je odabrana. Spremno za analizu.")
            else:
                self._set_status("Spremno za odabir slike.")
            if not self.selected_image_path and not self.last_analysis_results:
                self._show_ready_message()
        else:
            self._set_status("Model nije učitan. Provjerite internet vezu i biblioteke.")
            self._show_model_error_message()

        self._sync_analyze_button()

    def _add_history_entry(self, top_result, results):
        # Spremanje jedne analize u lokalnu povijest
        if not self.selected_image_path:
            return

        percent = top_result["confidence"] * 100
        level_label, _level_tag, _level_icon, level_color = self._confidence_level(percent)
        entry = {
            "style_name": top_result["name"],
            "filename": Path(self.selected_image_path).name,
            "image_path": str(self.selected_image_path),
            "processed_image_path": str(self.processed_image_path) if self.processed_image_path else "",
            "confidence": percent,
            "confidence_label": level_label,
            "color": level_color,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "results": results,
        }
        self.analysis_history.insert(0, entry)
        self.analysis_history = self.analysis_history[:50]
        save_analysis_history(self.analysis_history)
        self._render_history()

    def _render_history(self):
        # Iscrtavanje povijesti analiza u srednjem panelu
        for widget in self.history_list.winfo_children():
            widget.destroy()

        if not self.analysis_history:
            self.history_scroll.pack_forget()
            self.history_canvas.yview_moveto(0)
            tk.Label(
                self.history_list,
                text="Još nema spremljenih analiza.",
                font=FONTS["body"],
                bg=COLORS["surface"],
                fg=COLORS["text_muted"],
                justify="left",
                wraplength=LAYOUT["history_width"] - 80,
            ).pack(anchor="w", padx=16, pady=16)
            return

        if not self.history_scroll.winfo_ismapped():
            self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for entry in self.analysis_history:
            self._create_history_card(entry)

    def _create_history_card(self, entry):
        # Jedna kartica u povijesti analiza
        card_bg = COLORS["panel_bg_alt"]
        hover_bg = "#2C2A25"

        card = tk.Frame(
            self.history_list,
            bg=card_bg,
            highlightbackground=COLORS["border_soft"],
            highlightthickness=1,
            cursor="hand2",
        )
        card.pack(fill=tk.X, padx=12, pady=(12, 0))

        content = tk.Frame(card, bg=card_bg)
        content.pack(fill=tk.X, padx=16, pady=14)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, minsize=34)

        text_frame = tk.Frame(content, bg=card_bg)
        text_frame.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        title_label = tk.Label(
            text_frame,
            text=self._display_style_name(entry.get("style_name", "NEPOZNAT STIL")).upper(),
            font=FONTS["section"],
            bg=card_bg,
            fg=COLORS["text"],
            anchor="w",
            wraplength=LAYOUT["history_width"] - 150,
            justify="left",
        )
        title_label.pack(fill=tk.X)

        filename_label = tk.Label(
            text_frame,
            text=shorten_filename(entry.get("filename", "nepoznata_slika")),
            font=FONTS["body"],
            bg=card_bg,
            fg=COLORS["text_muted"],
            anchor="w",
        )
        filename_label.pack(fill=tk.X, pady=(4, 0))

        indicator = tk.Canvas(
            content,
            width=26,
            height=26,
            bg=card_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        indicator.grid(row=0, column=1, sticky="e")
        indicator.create_oval(
            3,
            3,
            23,
            23,
            fill=entry.get("color", COLORS["accent"]),
            outline="",
        )
        delete_button = tk.Button(
            content,
            text="x",
            font=FONTS["caption"],
            bg=COLORS["danger_bg"],
            fg=COLORS["danger"],
            activebackground=COLORS["danger_hover"],
            activeforeground=COLORS["danger"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            width=2,
            height=1,
            padx=0,
            pady=0,
        )
        delete_button.configure(command=lambda item=entry: self._delete_history_entry(item))

        hover_widgets = (card, content, text_frame, indicator, delete_button)
        color_widgets = (card, content, text_frame, title_label, filename_label, indicator)

        def set_card_bg(color):
            for widget in color_widgets:
                widget.configure(bg=color)

        def show_delete(_event=None):
            set_card_bg(hover_bg)
            if not delete_button.winfo_ismapped():
                indicator.grid_remove()
                delete_button.grid(row=0, column=1, sticky="e")

        def hide_delete(_event=None):
            pointer_x = self.root.winfo_pointerx()
            pointer_y = self.root.winfo_pointery()
            target = self.root.winfo_containing(pointer_x, pointer_y)
            current = target
            while current is not None:
                if current is card:
                    return
                current = getattr(current, "master", None)

            set_card_bg(card_bg)
            delete_button.grid_remove()
            indicator.grid(row=0, column=1, sticky="e")

        delete_button.grid(row=0, column=1, sticky="e")
        delete_button.grid_remove()

        self._bind_history_card(card, entry, skip_widgets={delete_button})
        for widget in hover_widgets:
            widget.bind("<Enter>", show_delete, add="+")
            widget.bind("<Leave>", hide_delete, add="+")
        delete_button.bind("<Button-1>", lambda event: self._stop_history_delete_click(event, entry))

    def _bind_history_card(self, widget, entry, skip_widgets=None):
        # Klik na karticu povijesti prikazuje spremljeni rezultat
        skip_widgets = skip_widgets or set()
        if widget in skip_widgets:
            return

        widget.bind("<Button-1>", lambda _event, item=entry: self._show_history_entry(item))
        for child in widget.winfo_children():
            if child in skip_widgets:
                continue
            child.bind("<Button-1>", lambda _event, item=entry: self._show_history_entry(item))
            self._bind_history_child(child, entry, skip_widgets)

    def _bind_history_child(self, widget, entry, skip_widgets=None):
        skip_widgets = skip_widgets or set()
        if widget in skip_widgets:
            return

        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda _event, item=entry: self._show_history_entry(item))
        for child in widget.winfo_children():
            self._bind_history_child(child, entry, skip_widgets)

    def _stop_history_delete_click(self, event, entry):
        self._delete_history_entry(entry)
        return "break"

    def _delete_history_entry(self, entry):
        should_reset_workspace = self._history_entry_is_current(entry)
        self.analysis_history = [
            item
            for item in self.analysis_history
            if item is not entry and item != entry
        ]
        save_analysis_history(self.analysis_history)
        self._render_history()
        if should_reset_workspace or not self.analysis_history:
            self.reset_workspace()
        self._sync_analyze_button()
        self._set_status("Stavka je uklonjena iz povijesti analiza.")

    def _history_entry_is_current(self, entry):
        if not self.selected_image_path:
            return False

        selected_paths = {
            self._normalize_path(self.selected_image_path),
            self._normalize_path(self.processed_image_path),
        }
        selected_paths.discard("")

        history_paths = {
            self._normalize_path(path)
            for path in self._history_image_candidates(entry)
        }
        history_paths.discard("")
        return bool(selected_paths.intersection(history_paths))

    def _show_history_entry(self, entry):
        # Prikaz rezultata koji je spremljen u povijesti
        self.workspace_accepts_new_image = False
        self._show_history_preview(entry)
        results = entry.get("results", [])
        if not results and entry.get("style_name"):
            results = [
                {
                    "name": entry["style_name"],
                    "confidence": entry.get("confidence", 0) / 100,
                    "period": "nije spremljeno",
                    "regions": [],
                    "materials": [],
                    "features": [],
                }
            ]
        if results:
            self._show_analysis_results(results, save_to_history=False)
            self._set_status("Prikazan je spremljeni rezultat iz povijesti.")
            self._sync_analyze_button()

    def _show_history_preview(self, entry):
        # Prikaz slike povezane sa spremljenom analizom
        preview_path = self._existing_path(*self._history_image_candidates(entry))
        processed_path = self._existing_path(entry.get("processed_image_path"))

        if preview_path:
            try:
                self.selected_image_path = preview_path
                self.processed_image_path = processed_path or preview_path
                self._load_preview_image(preview_path)
                return
            except Exception:
                pass

        self.selected_image_path = None
        self.processed_image_path = None
        self.image_label.configure(image="", text="📷")
        self.image_label.configure(cursor="arrow")
        self.image_title_label.configure(text=entry.get("filename", "Slika nije pronađena"))
        self.image_hint_label.configure(
            text="Originalna slika više nije dostupna na računalu.",
            wraplength=max(self.image_preview_frame.winfo_width() - 60, 360),
        )

    def _existing_path(self, *paths):
        # Pronalazi prvu postojeću putanju slike
        for path in paths:
            if not path:
                continue
            candidate = Path(path)
            if candidate.exists():
                return candidate
        return None

    def _sync_analyze_button(self):
        if self.workspace_accepts_new_image:
            self.btn_select.configure(state=tk.NORMAL)
        else:
            self.btn_select.configure(state=tk.DISABLED)

        if not self.selected_image_path or self.model_loading or self._current_image_has_history():
            self.btn_analyze.configure(state=tk.DISABLED)
        else:
            self.btn_analyze.configure(state=tk.NORMAL)

    def _current_image_has_history(self):
        if not self.selected_image_path:
            return False

        selected_paths = {
            self._normalize_path(self.selected_image_path),
            self._normalize_path(self.processed_image_path),
        }
        selected_paths.discard("")

        for entry in self.analysis_history:
            history_paths = set()
            for path in self._history_image_candidates(entry):
                history_paths.add(self._normalize_path(path))
            history_paths.discard("")
            if selected_paths.intersection(history_paths):
                return True
        return False

    def _normalize_path(self, path):
        if not path:
            return ""
        try:
            return str(Path(path).resolve(strict=False)).casefold()
        except (OSError, TypeError, ValueError):
            return str(path).casefold()

    def _history_image_candidates(self, entry):
        # Putanje za nove i starije zapise povijesti
        candidates = [entry.get("image_path"), entry.get("processed_image_path")]
        filename = entry.get("filename")
        if filename:
            processed_name = f"{Path(filename).stem.replace(' ', '_')}_processed.jpg"
            candidates.append(Path("data") / "processed" / processed_name)
        return candidates

    def _update_history_scroll(self, _event=None):
        # Osvježavanje scroll područja povijesti
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def _bind_history_mousewheel(self):
        self.history_canvas.bind("<Enter>", self._activate_history_mousewheel)
        self.history_canvas.bind("<Leave>", self._deactivate_history_mousewheel)

    def _activate_history_mousewheel(self, _event=None):
        if self._history_can_scroll():
            self.history_canvas.bind_all("<MouseWheel>", self._scroll_history)

    def _deactivate_history_mousewheel(self, _event=None):
        self.history_canvas.unbind_all("<MouseWheel>")

    def _scroll_history(self, event):
        if not self._history_can_scroll():
            return
        self.history_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _history_can_scroll(self):
        if not self.analysis_history:
            return False
        scroll_bbox = self.history_canvas.bbox("all")
        if not scroll_bbox:
            return False
        return scroll_bbox[3] > self.history_canvas.winfo_height()

    def _resize_history_window(self, event):
        # Kartice prate širinu panela povijesti
        self.history_canvas.itemconfigure(self.history_window, width=event.width)

    def clear_history(self):
        # Brisanje povijesti uz potvrdu korisnika
        confirmed = messagebox.askyesno(
            "Brisanje povijesti",
            "Odabrana radnja ne može se poništiti.\n\nJeste li sigurni da želite nastaviti?",
        )
        if not confirmed:
            return

        self.analysis_history = []
        clear_analysis_history()
        self._render_history()
        self._set_status("Povijest analiza je očišćena.")
        self._sync_analyze_button()

    def _write_readonly(self, widget, text):
        # Upis teksta u zaključani Text widget
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state=tk.DISABLED)

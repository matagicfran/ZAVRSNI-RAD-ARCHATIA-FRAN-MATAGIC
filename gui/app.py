import tkinter as tk
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

from core.detector import ArchitectureDetector
from core.image_processor import prepare_image
from core.model_loader import ModelManager
from gui.styles import COLORS, FONTS, LAYOUT
from gui.widgets import Card, Divider, SectionLabel, SidebarButton


class EnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARCHATIA")
        self.root.geometry("1500x880")
        self.root.minsize(1180, 720)
        self.root.configure(bg=COLORS["app_bg"])

        # Podaci o trenutno odabranoj slici
        self.selected_image_path = None
        self.processed_image_path = None
        self.preview_photo = None
        self.model_manager = ModelManager()
        self.detector = ArchitectureDetector(self.model_manager)

        self.setup_ui()
        self._load_models_async()

    def setup_ui(self):
        # Glavni dijelovi prozora
        self._build_shell()
        self._build_sidebar()
        self._build_history()
        self._build_main()
        self._set_status("Učitavanje modela...")

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

        self.btn_clear = SidebarButton(
            self.sidebar,
            text="Očisti povijest",
            icon="x",
            variant="danger",
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

        # Tekstualni prikaz povijesti
        history_wrap = Card(self.history_panel, bg=COLORS["surface"])
        history_wrap.pack(
            fill=tk.BOTH,
            expand=True,
            padx=LAYOUT["panel_pad"],
            pady=(0, LAYOUT["panel_pad"]),
        )

        self.history_box = tk.Text(
            history_wrap,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["body"],
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            padx=16,
            pady=16,
            cursor="arrow",
            insertwidth=0,
            selectbackground=COLORS["accent_dark"],
            selectforeground=COLORS["text"],
        )

        history_scroll = tk.Scrollbar(
            history_wrap,
            orient=tk.VERTICAL,
            command=self.history_box.yview,
            width=LAYOUT["scrollbar_width"],
            bg=COLORS["surface_soft"],
            troughcolor=COLORS["panel_bg"],
            activebackground=COLORS["accent"],
            relief=tk.FLAT,
            bd=0,
        )
        self.history_box.configure(yscrollcommand=history_scroll.set)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._write_readonly(
            self.history_box,
            "Još nema spremljenih analiza.\n\nNakon obrade slike, rezultati će se prikazati u ovom panelu.",
        )

    def _build_main(self):
        # Desni glavni sadržaj
        content = tk.Frame(self.main, bg=COLORS["app_bg"])
        content.pack(
            fill=tk.BOTH,
            expand=True,
            padx=LAYOUT["outer_pad"],
            pady=LAYOUT["outer_pad"],
        )

        tk.Label(
            content,
            text="Radna površina",
            font=FONTS["title"],
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w")

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
            text="Koristite gumb 'Odaberi sliku' u lijevom izborniku.",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            anchor="center",
            wraplength=760,
        )
        self.image_hint_label.pack(fill=tk.X, pady=(3, 0))

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

        self.results_text.configure(state=tk.NORMAL)
        self.results_text.insert(tk.END, "Dobrodošli u ARCHATIA\n", "title")
        self.results_text.insert(
            tk.END,
            "Sustav je spreman za analizu arhitektonskog stila.\n\n",
            "normal",
        )
        for step in (
            "1. Odaberite fotografiju građevine.",
            "2. Pokrenite analizu stila.",
            "3. Pregledajte rezultat i spremljenu povijest.",
        ):
            self.results_text.insert(tk.END, f"{step}\n", "muted")
        self.results_text.configure(state=tk.DISABLED)

    def select_image(self):
        # Otvaranje prozora za odabir slike
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

        try:
            self._show_image_preview(file_path)
            processing_result = prepare_image(file_path)
            self.processed_image_path = processing_result["processed_path"]
            self._show_selected_image_info(Path(file_path), processing_result)
        except ImportError:
            messagebox.showerror(
                "Nedostaje biblioteka",
                "Za prikaz slike potrebno je instalirati Pillow:\n\npip install -r requirements.txt",
            )
            self._set_status("Pillow nije instaliran.")
        except Exception as error:
            messagebox.showerror(
                "Greška pri učitavanju slike",
                f"Sliku nije moguće prikazati.\n\n{error}",
            )
            self._set_status("Odabrana slika se ne može prikazati.")

    def analyze_style(self):
        # Pokretanje analize odabrane slike
        if not self.selected_image_path:
            messagebox.showwarning(
                "Nije odabrana slika",
                "Prvo odaberite sliku za analizu.",
            )
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

    def _show_analysis_results(self, results):
        # Prikaz rezultata analize u GUI-u
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
                level_label, level_tag, level_icon = self._confidence_level(percent)
                self.results_text.insert(
                    tk.END,
                    f"{index}. {result['name']}\n",
                    "normal",
                )
                self.results_text.insert(
                    tk.END,
                    f"{level_icon} Pouzdanost: {level_label} ({percent:.1f}%)\n\n",
                    level_tag,
                )

        self.results_text.configure(state=tk.DISABLED)
        self.btn_analyze.configure(state=tk.NORMAL)
        self._set_status("Analiza je završena.")

    def _show_analysis_error(self, error):
        # Prikaz greške ako analiza ne uspije
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Analiza nije uspjela\n", "title")
        self.results_text.insert(tk.END, str(error), "normal")
        self.results_text.configure(state=tk.DISABLED)
        self.btn_analyze.configure(state=tk.NORMAL)
        self._set_status("Analiza nije uspjela.")

    def _confidence_level(self, percent):
        # Razina pouzdanosti prema postotku rezultata
        if percent >= 60:
            return "visoka", "high", "🟢"
        if percent >= 30:
            return "srednja", "medium", "🟡"
        return "niska", "low", "🔴"

    def _show_image_preview(self, file_path):
        # Učitavanje i smanjivanje slike za preview
        from PIL import Image, ImageOps, ImageTk

        image_path = Path(file_path)
        self.root.update_idletasks()

        max_width = max(self.image_preview_frame.winfo_width() - 40, 360)
        max_height = 205

        image = Image.open(image_path)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        self.preview_photo = ImageTk.PhotoImage(image)
        self.selected_image_path = image_path

        self.image_label.configure(
            image=self.preview_photo,
            text="",
            width=max_width,
            height=max_height,
        )
        self.image_title_label.configure(text=image_path.name)
        self.image_hint_label.configure(
            text=str(image_path),
            wraplength=max(self.image_preview_frame.winfo_width() - 60, 360),
        )
        self._set_status("Slika je odabrana. Spremno za analizu.")

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

    def _set_status(self, message):
        # Promjena statusa u lijevom izborniku
        self.status_label.configure(text=message)

    def _load_models_async(self):
        # Učitavanje AI modela u pozadini da GUI ne zablokira
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
        self.progress_label.configure(text=f"{value}%")

        width = max(self.progress_canvas.winfo_width(), 1)
        fill_width = int(width * (value / 100))
        self.progress_canvas.coords(self.progress_fill, 0, 0, fill_width, 8)

    def _update_model_status(self, statuses):
        # Nakon učitavanja ostaje samo glavni status
        self._set_model_progress(100)
        self.progress_frame.pack_forget()
        self.progress_label.pack_forget()

        if all(status.loaded for status in statuses):
            if self.selected_image_path:
                self._set_status("Slika je odabrana. Spremno za analizu.")
            else:
                self._set_status("Spremno za odabir slike.")
        else:
            self._set_status("Model nije učitan. Provjerite internet vezu i biblioteke.")

    def _write_readonly(self, widget, text):
        # Upis teksta u zaključani Text widget
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state=tk.DISABLED)

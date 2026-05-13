import os
import queue
import threading
import ctypes
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
from app.config import APP_NAME, PROCESSED_DIR
from app.downloader import ImageDownloader
from app.processor import ImageProcessor
from app.scraper import BHImageScraper
from app.utils import clean_text, slugify


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("viddium.viddi.imagens")

        self.title(APP_NAME)
        self.geometry("1400x900")
        self.minsize(820, 560)
        self.configure(fg_color="#0f1115")

        self.last_output_folder = None
        self.status_queue = queue.Queue()
        
        self.scraper = BHImageScraper()
        self.downloader = ImageDownloader()
        self.processor = ImageProcessor()
        self.selected_local_images = []
        self.local_folder_name_var = tk.StringVar()

        self.colors = {
            "bg": "#0f1115",
            "panel": "#151922",
            "panel_2": "#1b2130",
            "panel_3": "#10141c",
            "accent": "#b7ef07",
            "accent_hover": "#a3d906",
            "text": "#f3f5f7",
            "muted": "#aab2bf",
            "border": "#2a3140",
            "button_dark": "#252c38",
            "button_dark_hover": "#313a49",
            "success": "#b7ef07",
            "error": "#ff6b6b",
            "log_bg": "#0b0e13",
            "footer_bg": "#0a0d12",
        }

        self._load_assets()
        self._build_ui()
        self.after(200, self._poll_status_queue)

    def _font(self, family="Inter", size=12, weight="normal"):
        return ctk.CTkFont(family=family, size=size, weight=weight)

    def _load_assets(self):
        self.header_logo = None

        base_dir = Path(__file__).resolve().parents[1]
        icon_path = base_dir / "assets" / "icon.ico"
        logo_path = base_dir / "assets" / "logo.png"

        try:
            if icon_path.exists():
                self.iconbitmap(default=str(icon_path))
        except Exception:
            pass

        try:
            if logo_path.exists():
                logo = Image.open(logo_path)
                self.header_logo = ctk.CTkImage(
                    light_image=logo,
                    dark_image=logo,
                    size=self._fit_size(logo.size, 352, 100),
                )
        except Exception:
            self.header_logo = None

    def _fit_size(self, original_size, max_width, max_height):
        w, h = original_size
        scale = min(max_width / w, max_height / h)
        return max(1, int(w * scale)), max(1, int(h * scale))

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=self.colors["bg"],
            corner_radius=0
        )
        self.main_scroll.grid(row=0, column=0, sticky="nsew")

        self.main_scroll.grid_columnconfigure(0, weight=1)
        self.main_scroll.grid_rowconfigure(1, weight=1)

        self._build_header(self.main_scroll)
        self._build_main_content(self.main_scroll)
        self._build_footer(self.main_scroll)

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(28, 16))
        header.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        if self.header_logo:
            logo_label = ctk.CTkLabel(left, image=self.header_logo, text="")
            logo_label.pack(anchor="w")
        else:
            title = ctk.CTkLabel(
                left,
                text="Viddi",
                text_color=self.colors["text"],
                font=self._font("Inter", 32, "bold"),
            )
            title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            left,
            text="Processamento de imagens para produtos B&H",
            text_color=self.colors["muted"],
            font=self._font("Inter", 13),
        )
        subtitle.pack(anchor="w", pady=(10, 0))

        status_card = ctk.CTkFrame(
            header,
            fg_color=self.colors["panel"],
            corner_radius=18,
            border_width=1,
            border_color=self.colors["border"],
        )
        status_card.grid(row=0, column=1, sticky="e", padx=(20, 0))

        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(padx=16, pady=14)

        ctk.CTkLabel(
            status_inner,
            text="● Status",
            text_color=self.colors["accent"],
            font=self._font("Inter", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        self.header_status_title = ctk.CTkLabel(
            status_inner,
            text="Pronto para uso",
            text_color=self.colors["text"],
            font=self._font("Verdana", 13, "bold"),
        )
        self.header_status_title.pack(anchor="w")

        self.header_status_subtitle = ctk.CTkLabel(
            status_inner,
            text="Tudo pronto para começar",
            text_color=self.colors["muted"],
            font=self._font("Inter", 10),
        )
        self.header_status_subtitle.pack(anchor="w", pady=(4, 0))

    def _build_main_content(self, parent):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 12))
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._build_top_card(container)
        self._build_local_card(container)

        body = ctk.CTkFrame(container, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        self._build_log_card(left)
        self._build_summary_card(right)

    def _build_top_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors["panel"],
            corner_radius=20,
            border_width=1,
            border_color=self.colors["border"],
        )
        card.grid(row=0, column=0, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=18)

        ctk.CTkLabel(
            inner,
            text="LINK DO PRODUTO",
            text_color=self.colors["accent"],
            font=self._font("Inter", 12, "bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text="Cole o link do produto da B&H Photo Video",
            text_color=self.colors["muted"],
            font=self._font("Verdana", 14),
        ).pack(anchor="w", pady=(10, 14))

        middle = ctk.CTkFrame(inner, fg_color="transparent")
        middle.pack(fill="x")
        middle.grid_columnconfigure(0, weight=1)

        self.url_var = tk.StringVar()

        left = ctk.CTkFrame(middle, fg_color="transparent")
        left.grid(row=0, column=0, sticky="ew", padx=(0, 18))

        right = ctk.CTkFrame(middle, fg_color="transparent")
        right.grid(row=0, column=1, sticky="ns")

        self.url_entry = ctk.CTkEntry(
            left,
            textvariable=self.url_var,
            height=52,
            corner_radius=14,
            fg_color=self.colors["panel_3"],
            border_width=1,
            border_color=self.colors["accent"],
            text_color=self.colors["text"],
            font=self._font("Verdana", 14),
            placeholder_text="Cole aqui o link do produto da B&H",
            placeholder_text_color="#7f8793",
        )
        self.url_entry.pack(fill="x", pady=(8, 0))

        self.generate_btn = ctk.CTkButton(
            right,
            text="PROCESSAR IMAGENS",
            height=52,
            corner_radius=14,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color="#000000",
            font=self._font("Inter", 12, "bold"),
            command=self.start_process,
        )
        self.generate_btn.pack(fill="x", pady=(8, 12))

        self.open_btn = ctk.CTkButton(
            right,
            text="ABRIR PASTA FINAL",
            height=52,
            corner_radius=14,
            fg_color=self.colors["button_dark"],
            hover_color=self.colors["button_dark_hover"],
            text_color=self.colors["text"],
            font=self._font("Inter", 12, "bold"),
            command=self.open_output_folder,
        )
        self.open_btn.pack(fill="x")

    def _build_local_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors["panel"],
            corner_radius=20,
            border_width=1,
            border_color=self.colors["border"],
        )
        card.grid(row=1, column=0, sticky="ew", pady=(14, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=18)

        ctk.CTkLabel(
            inner,
            text="IMAGENS LOCAIS",
            text_color=self.colors["accent"],
            font=self._font("Inter", 12, "bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text="Selecione imagens do computador para processar sem usar link",
            text_color=self.colors["muted"],
            font=self._font("Verdana", 14),
        ).pack(anchor="w", pady=(10, 14))

        self.local_images_count_label = ctk.CTkLabel(
            inner,
            text="Nenhuma imagem selecionada",
            text_color=self.colors["text"],
            font=self._font("Inter", 12),
        )
        self.local_images_count_label.pack(anchor="w", pady=(0, 12))

        self.local_folder_entry = ctk.CTkEntry(
            inner,
            textvariable=self.local_folder_name_var,
            height=48,
            corner_radius=14,
            fg_color=self.colors["panel_3"],
            border_width=1,
            border_color=self.colors["border"],
            text_color=self.colors["text"],
            font=self._font("Verdana", 13),
            placeholder_text="Nome da pasta final (opcional)",
            placeholder_text_color="#7f8793",
        )
        self.local_folder_entry.pack(fill="x", pady=(0, 12))

        buttons = ctk.CTkFrame(inner, fg_color="transparent")
        buttons.pack(fill="x")
        buttons.grid_columnconfigure((0, 1, 2), weight=1)

        select_btn = ctk.CTkButton(
            buttons,
            text="SELECIONAR IMAGENS",
            height=48,
            corner_radius=14,
            fg_color=self.colors["button_dark"],
            hover_color=self.colors["button_dark_hover"],
            text_color=self.colors["text"],
            font=self._font("Inter", 12, "bold"),
            command=self.select_local_images,
        )
        select_btn.pack(side="left", padx=(0, 12))

        open_local_output_btn = ctk.CTkButton(
            buttons,
            text="ABRIR PASTA FINAL",
            height=48,
            corner_radius=14,
            fg_color=self.colors["button_dark"],
            hover_color=self.colors["button_dark_hover"],
            text_color=self.colors["text"],
            font=self._font("Inter", 12, "bold"),
            command=self.open_output_folder,
        )
        open_local_output_btn.pack(side="left", padx=(0, 12))

        self.generate_local_btn = ctk.CTkButton(
            buttons,
            text="PROCESSAR IMAGENS LOCAIS",
            height=48,
            corner_radius=14,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color="#000000",
            font=self._font("Inter", 12, "bold"),
            command=self.start_local_process,
        )
        self.generate_local_btn.pack(side="left")

    def _build_log_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors["panel"],
            corner_radius=20,
            border_width=1,
            border_color=self.colors["border"],
        )
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card,
            text="STATUS DO PROCESSAMENTO",
            text_color=self.colors["accent"],
            font=self._font("Inter", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(18, 12))

        log_container = ctk.CTkFrame(card, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=18)

        log_wrap = ctk.CTkFrame(
            log_container,
            fg_color=self.colors["log_bg"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"],
        )
        log_wrap.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_wrap,
            bg=self.colors["log_bg"],
            fg=self.colors["accent"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=0,
            font=("Consolas", 11),
            wrap="word",
            padx=16,
            pady=16,
        )
        self.log_text.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)

        scrollbar = tk.Scrollbar(
            log_wrap,
            command=self.log_text.yview,
            bg=self.colors["panel_2"],
            troughcolor=self.colors["panel_3"],
            activebackground=self.colors["accent"],
            relief="flat",
            bd=0,
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.log_text.config(yscrollcommand=scrollbar.set)

        progress_wrap = ctk.CTkFrame(card, fg_color="transparent")
        progress_wrap.pack(fill="x", padx=18, pady=(14, 18))

        self.progress_label = ctk.CTkLabel(
            progress_wrap,
            text="Progresso geral",
            text_color=self.colors["text"],
            font=self._font("Verdana", 14),
        )
        self.progress_label.pack(anchor="w", pady=(0, 8))

        progress_row = ctk.CTkFrame(progress_wrap, fg_color="transparent")
        progress_row.pack(fill="x")

        self.progress = ctk.CTkProgressBar(
            progress_row,
            height=20,
            corner_radius=20,
            fg_color="#1e2430",
            progress_color="#b7ef07",
        )
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress.set(0)

        self.progress_value_label = ctk.CTkLabel(
            progress_row,
            text="0%",
            text_color=self.colors["text"],
            font=self._font("Verdana", 14),
        )
        self.progress_value_label.pack(side="left", padx=(12, 0))

    def _build_summary_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors["panel"],
            corner_radius=20,
            border_width=1,
            border_color=self.colors["border"],
        )
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card,
            text="RESUMO",
            text_color=self.colors["accent"],
            font=self._font("Inter", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(18, 14))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18)

        self.metric_found = self._create_metric_row(content, "Encontradas", "0")
        self.metric_downloaded = self._create_metric_row(content, "Baixadas", "0")
        self.metric_processed = self._create_metric_row(content, "Processadas", "0")
        self.metric_status = self._create_metric_row(
            content,
            "Status",
            "Aguardando",
            value_color=self.colors["text"],
        )

        bottom = ctk.CTkFrame(
            card,
            fg_color=self.colors["panel_2"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"],
        )
        bottom.pack(fill="x", side="bottom", padx=18, pady=(18, 18))

        ctk.CTkLabel(
            bottom,
            text="PASTA FINAL",
            text_color=self.colors["text"],
            font=self._font("Inter", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(14, 8))

        self.final_folder_label = ctk.CTkLabel(
            bottom,
            text="Ainda não processado",
            text_color=self.colors["accent"],
            font=self._font("Inter", 10),
            justify="left",
            wraplength=320,
        )
        self.final_folder_label.pack(anchor="w", padx=18, pady=(0, 14))

    def _create_metric_row(self, parent, label_text, value_text, value_color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left,
            text=label_text,
            text_color=self.colors["text"],
            font=self._font("Inter", 11),
        ).pack(anchor="w")

        value_label = ctk.CTkLabel(
            row,
            text=value_text,
            text_color=value_color or self.colors["accent"],
            font=self._font("Inter", 22, "bold"),
        )
        value_label.pack(side="right")

        separator = ctk.CTkFrame(parent, fg_color=self.colors["border"], height=1, corner_radius=0)
        separator.pack(fill="x", pady=(0, 10))

        return value_label

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(
            parent,
            fg_color=self.colors["footer_bg"],
            corner_radius=0,
            height=52,
        )
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 0))
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(footer, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=20)

        ctk.CTkLabel(
            left,
            text="Powered by Viddium",
            text_color=self.colors["muted"],
            font=self._font("Inter", 10),
        ).pack(side="left", pady=14)

        self.footer_status = ctk.CTkLabel(
            footer,
            text="Pronto para uso",
            text_color=self.colors["accent"],
            font=self._font("Verdana", 14),
        )
        self.footer_status.grid(row=0, column=1, sticky="e", padx=20, pady=14)

    def log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def set_status(self, message: str):
        self.log(message)
        self.footer_status.configure(text=message)

    def _set_progress(self, value: int):
        value = max(0, min(100, value))
        self.progress.set(value / 100)
        self.progress_value_label.configure(text=f"{value}%")

    def _reset_summary(self):
        self.metric_found.configure(text="0", text_color=self.colors["accent"])
        self.metric_downloaded.configure(text="0", text_color=self.colors["accent"])
        self.metric_processed.configure(text="0", text_color=self.colors["accent"])
        self.metric_status.configure(text="Aguardando", text_color=self.colors["text"])
        self.final_folder_label.configure(text="Ainda não processado")
        self.header_status_title.configure(text="Pronto para uso")
        self.header_status_subtitle.configure(text="Tudo pronto para começar")
        self._set_progress(0)

    def start_process(self):
        url = clean_text(self.url_var.get())
        if not url:
            messagebox.showwarning(APP_NAME, "Cole o link do produto antes de continuar.")
            return

        if "bhphotovideo.com" not in url:
            messagebox.showwarning(APP_NAME, "Use um link válido da B&H.")
            return

        self.generate_btn.configure(state="disabled")
        self.log_text.delete("1.0", "end")
        self._reset_summary()
        self.set_status("Iniciando processamento...")
        self.header_status_title.configure(text="Processando")
        self.header_status_subtitle.configure(text="Aguarde enquanto as imagens são preparadas")
        self.metric_status.configure(text="Em andamento", text_color=self.colors["text"])
        self._set_progress(5)

        threading.Thread(target=self._run_process, args=(url,), daemon=True).start()

    def _run_process(self, url: str):
        try:
            self.status_queue.put(("status", "Lendo página do produto..."))
            scraped = self.scraper.scrape(url)
            self.status_queue.put(("progress", 20))

            self.status_queue.put(("log", f"TÍTULO CAPTURADO: {scraped.get('title')}"))
            self.status_queue.put(("log", f"IMAGENS CAPTURADAS: {scraped.get('images')}"))
            self.status_queue.put(("metric_found", len(scraped.get("images", []))))

            slug = slugify(scraped["title"])

            self.status_queue.put(("status", "Baixando imagens..."))
            raw_images = self.downloader.download_images(scraped["images"], slug)
            self.status_queue.put(("log", f"IMAGENS BAIXADAS: {len(raw_images)}"))
            self.status_queue.put(("metric_downloaded", len(raw_images)))
            self.status_queue.put(("progress", 65))

            self.status_queue.put(("status", "Processando imagens..."))
            processed_images = self.processor.process_images(raw_images, slug)
            self.status_queue.put(("log", f"IMAGENS PROCESSADAS: {len(processed_images)}"))
            self.status_queue.put(("metric_processed", len(processed_images)))
            self.status_queue.put(("progress", 90))

            self.status_queue.put((
                "result",
                {
                    "title": scraped["title"],
                    "slug": slug,
                    "raw_count": len(raw_images),
                    "processed_count": len(processed_images),
                }
            ))

        except Exception as exc:
            self.status_queue.put(("error", str(exc)))

    def _poll_status_queue(self):
        try:
            while True:
                kind, payload = self.status_queue.get_nowait()

                if kind == "status":
                    self.set_status(payload)

                elif kind == "log":
                    self.log(payload)

                elif kind == "progress":
                    self._set_progress(payload)

                elif kind == "metric_found":
                    self.metric_found.configure(text=str(payload))

                elif kind == "metric_downloaded":
                    self.metric_downloaded.configure(text=str(payload))

                elif kind == "metric_processed":
                    self.metric_processed.configure(text=str(payload))

                elif kind == "error":
                    self.generate_btn.configure(state="normal")
                    self.metric_status.configure(text="Erro", text_color=self.colors["error"])
                    self.header_status_title.configure(text="Erro no processamento")
                    self.header_status_subtitle.configure(text="Revise o link e tente novamente")
                    self.set_status("Erro no processamento")
                    self._set_progress(0)
                    messagebox.showerror(APP_NAME, payload)

                elif kind == "result":
                    self.generate_btn.configure(state="normal")
                    self.populate_result(payload)
                
                elif kind == "local_done":
                     self.generate_local_btn.configure(state="normal")

        except queue.Empty:
            pass
        finally:
            self.after(200, self._poll_status_queue)

    def populate_result(self, result: dict):
        final_folder = PROCESSED_DIR / result["slug"]
        self.last_output_folder = final_folder

        self.metric_status.configure(text="Concluído", text_color=self.colors["success"])
        self.final_folder_label.configure(text=str(final_folder))
        self.header_status_title.configure(text="Pronto para uso")
        self.header_status_subtitle.configure(text="Processamento finalizado com sucesso")
        self._set_progress(100)

        self.set_status(
            f"Concluído. {result['processed_count']} imagem(ns) pronta(s)."
        )

        messagebox.showinfo(
            APP_NAME,
            f"Processo finalizado.\n\n"
            f"Produto: {result['title']}\n"
            f"Baixadas: {result['raw_count']}\n"
            f"Processadas: {result['processed_count']}\n\n"
            f"Pasta final:\n{final_folder}"
        )

    def open_output_folder(self):
        try:
            if self.last_output_folder and self.last_output_folder.exists():
                os.startfile(self.last_output_folder)
            else:
                os.startfile(PROCESSED_DIR)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Não foi possível abrir a pasta.\n\n{exc}")


    def select_local_images(self):
        files = filedialog.askopenfilenames(
            title="Selecione as imagens",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"),
            ],
        )

        if files:
            self.selected_local_images = list(files)
            self.local_images_count_label.configure(
                text=f"{len(self.selected_local_images)} imagem(ns) selecionada(s)",
                text_color=self.colors["accent"]
            )
        else:
            self.selected_local_images = []
            self.local_images_count_label.configure(
                text="Nenhuma imagem selecionada",
                text_color=self.colors["text"]
            )

    def start_local_process(self):
        if not self.selected_local_images:
            messagebox.showwarning(APP_NAME, "Selecione pelo menos uma imagem.")
            return

        folder_name = clean_text(self.local_folder_name_var.get())
        if not folder_name:
            folder_name = "imagens-locais"

        slug = slugify(folder_name)

        self.generate_local_btn.configure(state="disabled")
        self.log_text.delete("1.0", "end")
        self._reset_summary()
        self.set_status("Processando imagens locais...")
        self.header_status_title.configure(text="Processando")
        self.header_status_subtitle.configure(text="Aguarde enquanto as imagens são preparadas")
        self.metric_status.configure(text="Em andamento", text_color=self.colors["text"])
        self._set_progress(10)

        threading.Thread(target=self._run_local_process, args=(slug,), daemon=True).start()      

    def _run_local_process(self, slug: str):
        try:
            self.status_queue.put(("metric_found", len(self.selected_local_images)))
            self.status_queue.put(("metric_downloaded", len(self.selected_local_images)))
            self.status_queue.put(("progress", 35))
            self.status_queue.put(("status", "Processando imagens locais..."))

            processed_images = self.processor.process_images(self.selected_local_images, slug)

            self.status_queue.put(("log", f"IMAGENS PROCESSADAS: {len(processed_images)}"))
            self.status_queue.put(("metric_processed", len(processed_images)))
            self.status_queue.put(("progress", 100))

            self.status_queue.put((
                "result",
                {
                    "title": "Imagens locais",
                    "slug": slug,
                    "raw_count": len(self.selected_local_images),
                    "processed_count": len(processed_images),
                }
            ))

        except Exception as exc:
            self.status_queue.put(("error", str(exc)))
        finally:
            self.status_queue.put(("local_done", None))    


"""r-check main application window — single-window frame switching."""
import customtkinter as ctk
from app.gui.theme import BG_PRIMARY
from app.gui.widgets.header_bar import HeaderBar

ctk.set_appearance_mode("dark")


class RCheckApp:
    """Root application window. Screens register as CTkFrame subclasses."""

    def __init__(self) -> None:
        self.root = ctk.CTk()
        self.root.title("r-check")
        self.root.geometry("1100x780")
        self.root.configure(fg_color=BG_PRIMARY)
        self.root.minsize(900, 640)

        # Header bar (fixed at top, shared across all screens)
        self._header = HeaderBar(self.root)
        self._header.pack(fill="x", side="top")

        # Content area for screen frames
        self._content = ctk.CTkFrame(self.root, fg_color=BG_PRIMARY)
        self._content.pack(fill="both", expand=True)

        self._screens: dict[str, ctk.CTkFrame] = {}
        self._active_screen: ctk.CTkFrame | None = None

        # Global Tooltip (prevent multiple ghost windows)
        self._tooltip_window = None
        self._tooltip_hide_id = None

    def register_screen(self, name: str, screen: ctk.CTkFrame) -> None:
        """Register a screen frame. Screen must already be created with _content as master."""
        self._screens[name] = screen

    def show_tooltip(self, text_tool: str, text_desc: str, x: int, y: int) -> None:
        """Cria ou atualiza uma única janela de tooltip global."""
        # Se um hide estava agendado, cancela
        if self._tooltip_hide_id:
            self.root.after_cancel(self._tooltip_hide_id)
            self._tooltip_hide_id = None

        # Se a janela não existe ou foi destruída, cria
        if not self._tooltip_window or not self._tooltip_window.winfo_exists():
            tip = ctk.CTkToplevel(self.root)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            
            frame = ctk.CTkFrame(
                tip, fg_color="#1A1A1A", corner_radius=12,
                border_width=1, border_color="#333333",
            )
            frame.pack(fill="both", expand=True, padx=1, pady=1)

            self._tooltip_title = ctk.CTkLabel(
                frame, text="", font=("Outfit", 14, "bold"), text_color="#FFFFFF"
            )
            self._tooltip_title.pack(anchor="w", padx=14, pady=(12, 4))

            self._tooltip_body = ctk.CTkLabel(
                frame, text="", font=("Inter", 12), text_color="#A0A0A0",
                wraplength=300, justify="left",
            )
            self._tooltip_body.pack(anchor="w", padx=14, pady=(0, 12))
            self._tooltip_window = tip

        # Atualiza conteúdo e posição
        self._tooltip_title.configure(text=text_tool.capitalize())
        self._tooltip_body.configure(text=text_desc)
        self._tooltip_window.deiconify()
        self._tooltip_window.geometry(f"+{x+15}+{y+15}")

    def hide_tooltip(self, delay: int = 120) -> None:
        """Agenda o ocultamento do tooltip global."""
        if self._tooltip_hide_id:
            self.root.after_cancel(self._tooltip_hide_id)
        
        def _do_hide():
            if self._tooltip_window and self._tooltip_window.winfo_exists():
                self._tooltip_window.withdraw()
            self._tooltip_hide_id = None

        self._tooltip_hide_id = self.root.after(delay, _do_hide)

    def show_screen(self, name: str, **kwargs) -> None:
        """Switch to named screen. Calls on_show(kwargs) if screen has it."""
        if self._active_screen:
            self._active_screen.pack_forget()
        screen = self._screens[name]
        screen.pack(in_=self._content, fill="both", expand=True)
        self._active_screen = screen
        if hasattr(screen, "on_show"):
            screen.on_show(**kwargs)

    @property
    def content_frame(self) -> ctk.CTkFrame:
        """Parent frame for all screens."""
        return self._content

    def run(self) -> None:
        """Start the application main loop."""
        self.show_screen("home")
        self.root.mainloop()

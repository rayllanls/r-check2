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

    def register_screen(self, name: str, screen: ctk.CTkFrame) -> None:
        """Register a screen frame. Screen must already be created with _content as master."""
        self._screens[name] = screen

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

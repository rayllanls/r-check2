"""Janela principal do r-check — backward compat redirect."""
from app.gui.app import RCheckApp


class MainWindow:
    """Legacy wrapper. Use RCheckApp directly."""

    def __init__(self):
        self._app = RCheckApp()

    def run(self) -> None:
        self._app.run()

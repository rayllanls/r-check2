"""ProgressScreen — real-time scan progress with queue polling and cancellation."""
from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from app.core.scanner import ScanOrchestrator, EventType, ProgressEvent
from app.core.ingestion import resolve_local_path, clone_repository, cleanup_temp_dir
from app.gui.theme import (
    BG_PRIMARY,
    BG_CARD,
    BG_BORDER,
    BG_INPUT,
    ACCENT_RED,
    ACCENT_RED_HOVER,
    ACCENT_TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font_heading,
    font_body,
    font_mono,
)
from app.gui.widgets.scanner_row import ScannerRow
from app.config import PLAN_TOOLS, load_github_token


class ProgressScreen(ctk.CTkFrame):
    """Progress screen: runs scans off main thread, polls queue, shows per-scanner status."""

    def __init__(self, master: ctk.CTkBaseClass, nav_callback: Callable, **kwargs) -> None:
        super().__init__(master, fg_color=BG_PRIMARY, **kwargs)
        self._navigate = nav_callback
        self._q: queue.Queue = queue.Queue()
        self._orchestrator: Optional[ScanOrchestrator] = None
        self._scan_thread: Optional[threading.Thread] = None
        self._scan_result = None
        self._cloned_path: Optional[Path] = None
        self._scanner_rows: dict[str, ScannerRow] = {}
        self._build()

    def _build(self) -> None:
        """Create static layout elements."""
        # 1. Title
        self._title_label = ctk.CTkLabel(
            self,
            text="Scan em andamento...",
            font=font_heading(20),
            text_color=TEXT_PRIMARY,
        )
        self._title_label.pack(pady=(20, 4))

        # 1b. Clone status (visível só durante clone)
        self._clone_label = ctk.CTkLabel(
            self,
            text="",
            font=font_body(13),
            text_color=ACCENT_TEAL,
        )
        self._clone_label.pack(pady=(0, 8))

        # 2. Scanner status rows container
        self._rows_frame = ctk.CTkFrame(self, fg_color=BG_PRIMARY)
        self._rows_frame.pack(fill="x", padx=24, pady=(0, 8))

        # 3. Log area
        self._log_box = ctk.CTkTextbox(
            self,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            font=font_mono(11),
            state="disabled",
            height=280,
            border_width=1,
            border_color=BG_BORDER,
            corner_radius=6,
        )
        self._log_box.pack(fill="both", expand=True, padx=24, pady=(12, 8))

        # 4. Cancel button
        self._cancel_btn = ctk.CTkButton(
            self,
            text="Cancelar",
            fg_color=ACCENT_RED,
            hover_color=ACCENT_RED_HOVER,
            text_color="#ffffff",
            width=140,
            height=38,
            corner_radius=6,
            command=self._cancel_scan,
        )
        self._cancel_btn.pack(pady=(8, 20))

    def on_show(self, target: str = "", plan: str = "team", **kwargs) -> None:
        """Called by RCheckApp.show_screen — starts the scan for target."""
        # Clear previous state
        for widget in self._rows_frame.winfo_children():
            widget.destroy()
        self._scanner_rows = {}
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
        self._scan_result = None
        self._cancel_btn.configure(state="normal", text="Cancelar")

        # Create scanner rows for this plan
        for tool in PLAN_TOOLS.get(plan, []):
            row = ScannerRow(self._rows_frame, tool_name=tool)
            row.pack(fill="x", padx=0, pady=2)
            self._scanner_rows[tool] = row

        self._orchestrator = ScanOrchestrator(plan=plan)

        if target.startswith("http"):
            # Clone em background — nunca bloqueia a GUI
            self._title_label.configure(text="Clonando repositório...")
            self._clone_label.configure(text=target)
            self._scan_thread = threading.Thread(
                target=self._clone_then_scan, args=(target,), daemon=True
            )
        else:
            try:
                project_path = resolve_local_path(target)
            except ValueError as e:
                self._append_log(f"Erro: {e}")
                return
            self._cloned_path = None
            self._scan_thread = threading.Thread(
                target=self._run_scan, args=(project_path,), daemon=True
            )

        self._scan_thread.start()
        self.after(100, self._poll_queue)

    def _clone_then_scan(self, url: str) -> None:
        """Clona repositório e inicia scan — tudo fora da thread principal."""
        try:
            token = load_github_token()
            self._q.put(ProgressEvent(EventType.TOOL_START, "", "Clonando repositório..."))
            self._cloned_path = clone_repository(url, github_token=token)
            self.after(0, lambda: self._clone_label.configure(text=""))
            self.after(0, lambda: self._title_label.configure(text="Scan em andamento..."))
            self._run_scan(self._cloned_path)
        except (PermissionError, RuntimeError, ValueError) as e:
            self._q.put(ProgressEvent(EventType.TOOL_ERROR, "", str(e)))

    def _run_scan(self, project_path: Path) -> None:
        """Run scan in background thread and push events to queue."""
        try:
            self._scan_result = self._orchestrator.scan(project_path, progress_queue=self._q)
        except Exception as e:
            self._q.put(ProgressEvent(EventType.TOOL_ERROR, "", str(e)))
        finally:
            if self._cloned_path:
                cleanup_temp_dir(self._cloned_path)

    def _poll_queue(self) -> None:
        """Poll the event queue every 100ms — never blocks main thread."""
        try:
            while True:
                event = self._q.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        # Continue polling if scan thread is alive
        if self._scan_thread and self._scan_thread.is_alive():
            self.after(100, self._poll_queue)
        else:
            # Thread finished — drain remaining events
            try:
                while True:
                    event = self._q.get_nowait()
                    self._handle_event(event)
            except queue.Empty:
                pass

    def _handle_event(self, event: ProgressEvent) -> None:
        """Route progress event to appropriate row update and log."""
        self._append_log(f"[{event.tool}] {event.message}" if event.tool else event.message)

        if event.event_type == EventType.TOOL_START:
            if event.tool in self._scanner_rows:
                self._scanner_rows[event.tool].set_status("running")
        elif event.event_type == EventType.TOOL_DONE:
            if event.tool in self._scanner_rows:
                self._scanner_rows[event.tool].set_status("done", event.findings_count)
        elif event.event_type == EventType.TOOL_ERROR:
            if event.tool in self._scanner_rows:
                self._scanner_rows[event.tool].set_status("error")
        elif event.event_type == EventType.SCAN_COMPLETE:
            self._on_scan_complete()

    def _append_log(self, text: str) -> None:
        """Append a line to the log textbox."""
        self._log_box.configure(state="normal")
        self._log_box.insert("end", text + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _cancel_scan(self) -> None:
        """Cancel the running scan and navigate back to home."""
        if self._orchestrator:
            self._orchestrator.cancel()
        self._cancel_btn.configure(state="disabled", text="Cancelando...")
        self._append_log("Scan cancelado pelo usuario.")
        self.after(1500, lambda: self._navigate("home"))

    def _on_scan_complete(self) -> None:
        """Handle scan completion — navigate to results screen."""
        self._cancel_btn.configure(state="disabled")
        self._append_log("Scan concluido!")
        self.after(800, lambda: self._navigate("results", scan_result=self._scan_result))

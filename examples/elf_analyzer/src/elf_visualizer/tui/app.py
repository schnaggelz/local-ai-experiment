from __future__ import annotations

import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding

from elf_visualizer.exceptions import ELFParseError
from elf_visualizer.parser import parse_elf
from elf_visualizer.tui.screens import MainScreen


class ElfTuiApp(App):
    """Interactive TUI application for ELF binary inspection."""

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, elf_path: str) -> None:
        super().__init__()
        self.elf_path = elf_path
        self.elf_data = None
        self.main_screen: MainScreen | None = None

    def on_mount(self) -> None:
        """Parse the ELF file when the app mounts."""
        try:
            base_data = parse_elf(self.elf_path)

            # Pre-load enhanced metadata for TUI responsiveness
            from elf_visualizer.parser import (
                _parse_symbol_table,
                _parse_relocation_section,_parse_dynamic_section,
                _parse_version_definitions,
            )
            from elftools.elf.elffile import ELFFile

            symbols = base_data.symbols or []
            relocs_raw = base_data.relocations or []
            dyn_raw = base_data.dynamic_entries
            vers_raw = base_data.version_definitions

            with open(self.elf_path, "rb") as f:
                elf = ELFFile(f)
                symbols = _parse_symbol_table(elf) or []

                relocs = []
                for sec in elf.iter_sections():
                    relocs.extend(_parse_relocation_section(sec))
                relocs_raw = relocs if relocs else None

                dyn_raw = _parse_dynamic_section(elf) or dyn_raw
                vers_raw = _parse_version_definitions(elf) or vers_raw

            # InputFile is frozen; create an updated copy.
            self.elf_data = base_data.model_copy(update={
                "symbols": symbols,
                "relocations": relocs_raw,
                "dynamic_entries": dyn_raw,
                "version_definitions": vers_raw,
            })

            # Store reference to the main screen so we can programmatically switch views without stack issues.
            self.main_screen = MainScreen(self.elf_data)
            self.push_screen(self.main_screen)
        except ELFParseError as err:
            self.notify(f"Failed to parse ELF: {err}", severity="error")
            self.exit()
        except FileNotFoundError:
            self.notify(f"File not found: {self.elf_path}", severity="error")
            self.exit()

    def compose(self) -> ComposeResult:
        """Initially yield a loading screen."""
        yield from ()

    # -- Screen Navigation Actions -------------------------------------------

    def _switch_view(self, view_id: str) -> None:
        """Helper to update the currently mounted screen's view state directly."""
        if self.main_screen:
            clean_key = view_id.split("?")[0]
            self.notify(f"Switched to {clean_key.replace('_', ' ').title()} View")
            self.main_screen.action_switch(clean_key)


def run_tui(elf_path: str) -> None:
    """Entry point for the Textual TUI."""
    if not Path(elf_path).is_file():
        print(f"Error: File '{elf_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    app = ElfTuiApp(elf_path)
    app.run()

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
        Binding("s", "screen_sections", "Sections"),
        Binding("y", "screen_symbols", "Symbols"),
        Binding("r", "screen_relocations", "Relocations"),
        Binding("/", "focus_search", "Search"),
    ]

    def __init__(self, elf_path: str) -> None:
        super().__init__()
        self.elf_path = elf_path
        self.elf_data = None

    def on_mount(self) -> None:
        """Parse the ELF file when the app mounts."""
        try:
            self.elf_data = parse_elf(self.elf_path)
            # Pre-load enhanced metadata for TUI responsiveness
            from elf_visualizer.parser import (
                _parse_symbol_table,
                _parse_relocation_section,
                _parse_dynamic_section,
                _parse_version_definitions,
            )
            from elftools.elf.elffile import ELFFile

            with open(self.elf_path, "rb") as f:
                elf = ELFFile(f)
                self.elf_data.symbols = _parse_symbol_table(elf) or []
                
                relocs = []
                for sec in elf.iter_sections():
                    relocs.extend(_parse_relocation_section(sec))
                self.elf_data.relocations = relocs if relocs else None

                dyn = _parse_dynamic_section(elf)
                self.elf_data.dynamic_entries = dyn or None

                vers = _parse_version_definitions(elf)
                self.elf_data.version_definitions = vers or None

            self.push_screen(MainScreen(self.elf_data))
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

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_screen_sections(self) -> None:
        self.push_screen("main")

    def action_screen_symbols(self) -> None:
        self.push_screen("main?view=symbols")

    def action_screen_relocations(self) -> None:
        self.push_screen("main?view=relocs")


def run_tui(elf_path: str) -> None:
    """Entry point for the Textual TUI."""
    if not Path(elf_path).is_file():
        print(f"Error: File '{elf_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    app = ElfTuiApp(elf_path)
    app.run()

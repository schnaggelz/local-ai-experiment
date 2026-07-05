from __future__ import annotations

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Select, Static

from elf_visualizer.models import InputFile
from elf_visualizer.tui.widgets import RelocationTable, HexViewerWidget, IconSidebar, MetadataPanel, SectionTable, SymbolTable


class MainScreen(Screen[InputFile]):
    """Main TUI screen providing navigation and ELF metadata display."""

    BINDINGS = [
        Binding("1", "switch('sections')", "Sections"),
        Binding("2", "switch('symbols')", "Symbols"),
        Binding("3", "switch('relocs')", "Relocations"),
        Binding("4", "switch('dynamic')", "Dynamic"),
    ]

    CSS_PATH = "styles.tcss"

    def __init__(self, elf_data: InputFile) -> None:
        super().__init__()
        self.elf_data = elf_data
        self.current_view = "sections"
        self.selected_section_index = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-layout"):
            yield IconSidebar(
                id="sidebar",
                items=(
                    ("Sections", "sections"),
                    ("Symbols", "symbols"),
                    ("Relocations", "relocs"),
                    ("Dynamic Info", "dynamic"),
                ),
            )
            with Vertical(id="content-area"):
                yield Label(self.elf_data.path, id="file-title")
                yield Static(id="view-panels")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(IconSidebar).set_reactive("selected", "sections")
        self.update_view_panel()

    # -- View Switching Logic --------------------------------------------------

    def action_switch(self, view_id: str) -> None:
        self.current_view = view_id
        self.query_one(IconSidebar).set_reactive("selected", view_id)
        self.update_view_panel()

    def update_view_panel(self) -> None:
        """Clear current content and mount the appropriate widget for the active view."""
        container = self.query_one("#view-panels")
        container.remove_children()

        if self.current_view == "sections":
            container.mount(SectionTable(self.elf_data.sections))
        elif self.current_view == "symbols":
            container.mount(SymbolTable(self.elf_data.symbols or []))
        elif self.current_view == "relocs":
            container.mount(RelocationTable(self.elf_data.relocations or []))
        elif self.current_view == "dynamic":
            container.mount(MetadataPanel(self.elf_data.dynamic_entries or {}))

    # -- Sidebar Interactions --------------------------------------------------

    def on_icon_sidebar_changed(self, event: IconSidebar.Changed) -> None:
        self.action_switch(event.value)

    def on_section_table_selected(self, event: SectionTable.Selected) -> None:
        """When a section is selected, show its hex dump in the bottom panel."""
        # Optional: split view or modal to show hex dump. For now, we just log.
        self.notify(f"Selected section: {event.section.name}")

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual.containers import ScrollableContainer
from textual.events import Click
from textual.widgets import DataTable, Footer, Header, Input, Label, Static


@dataclass(frozen=True)
class SidebarItem:
    title: str
    action_id: str


# -- Sidebar Widget ------------------------------------------------------------

class IconSidebar(Static):
    """A sidebar widget for switching TUI views."""

    def __init__(self, items: tuple[tuple[str, str], ...], **kwargs) -> None:
        super().__init__(**kwargs)
        self.items = dict(items)
        self.selected_key = "sections"

    class Changed:
        """Emitted when the sidebar selection changes."""
        value: str

    def compose(self) -> ComposeResult:
        for title, action_id in self.items.items():
            is_selected = action_id == self.selected_key
            yield Label(
                f"[{'bold' if is_selected else ''}]{title}[/]",
                id=f"nav-{action_id}",
                classes="sidebar-item",
            )

    def on_mount(self) -> None:
        self.prevent(Click, "#sidebar")  # prevent weird focus issues

    def set_reactive(self, name: str, value: str) -> None:
        """Update visual highlighting for active sidebar item."""
        if name == "selected":
            self.selected_key = value
            for label in self.query("Label"):
                label.styles.bold = False
            try:
                self.query_one(f"#nav-{value}").styles.bold = True
            except Exception:
                pass

    def on_click(self, event: Click) -> None:
        """Handle clicks on sidebar items."""
        target_id = event.node.id or ""
        if target_id.startswith("nav-"):
            action_id = target_id.split("-", 1)[1]
            self.post_message(self.Changed(action_id))


# -- Section Table Widget ------------------------------------------------------

class SectionTable(DataTable[str]):
    """Displays parsed ELF section headers in an interactive table."""

    class Selected:
        """Emitted when a row is double-clicked."""
        section: Any

    CSS = """
    DataTable {
        width: 100%;
        height: 1fr;
    }
    """

    def __init__(self, sections: list[Any]) -> None:
        super().__init__()
        self.sections = sections
        self.show_header = True
        self.show_cursor = True
        self.zombie_rows = True
        self.fixed_zrows = 1

    def on_mount(self) -> None:
        self.add_columns("Idx", "Name", "Type", "VADDR", "Size", "Flags")
        for idx, sec in enumerate(self.sections):
            self.add_row(
                str(idx),
                sec.name,
                sec.type,
                f"0x{sec.address:x}",
                f"{sec.size} B",
                sec.flags,
                key=sec.name,
            )

    def on_data_table_column_resize(self, event: DataTable.ColumnResize) -> None:
        pass  # allow native resize

    def on_double_click(self, event: DataTable.CellClicked) -> None:
        """Dispatch selection event for hex dump loading."""
        try:
            sec = self.sections[int(event.cell.row)]
            self.post_message(self.Selected(sec))
        except (IndexError, ValueError):
            pass


# -- Symbol Table Widget -------------------------------------------------------

class SymbolTable(DataTable[str]):
    """Displays parsed ELF symbols in an interactive table."""

    CSS = """
    DataTable {
        width: 100%;
        height: 1fr;
    }
    """

    def __init__(self, symbols: list[Any]) -> None:
        super().__init__()
        self.symbols = symbols

    def on_mount(self) -> None:
        if not self.symbols:
            return
        self.add_columns("Idx", "Name", "Value", "Size", "Binding", "Visibility")
        for idx, sym in enumerate(self.symbols):
            if not sym.name:
                continue
            self.add_row(
                str(idx),
                sym.name,
                f"0x{sym.value:x}",
                f"{sym.size} B",
                sym.binding,
                sym.visibility,
                key=sym.name,
            )


# -- Metadata Panel Widget -----------------------------------------------------

class MetadataPanel(Static):
    """Renders dynamic tags or version definitions as a simple list."""

    def __init__(self, data: dict[str, Any] | list[Any]) -> None:
        super().__init__()
        self.data = data

    def render(self) -> Text:
        if not self.data:
            return Text("No metadata available.", style="dim")
        
        lines: list[str] = []
        if isinstance(self.data, dict):
            for sec_name, entries in self.data.items():
                lines.append(f"Section: {sec_name}")
                for entry in entries:
                    lines.append(f"  Tag: {entry.get('tag')} | Value: {entry.get('value')}")
        elif isinstance(self.data, list):
            for item in self.data:
                if hasattr(item, 'version_name'):
                    lines.append(f"Version: {item.version_name} [0x{item.hash_value:x}]")
        
        return Text("\n".join(lines) or "(empty)", style="not dim")


# -- Hex Viewer Widget ---------------------------------------------------------

class HexViewerWidget(Static):
    """Renders binary content of a section as a hex dump."""

    def __init__(self, data: bytes) -> None:
        super().__init__()
        self.data = data

    def render(self) -> Text:
        if not self.data:
            return Text("No content to display.", style="dim")

        # Format 16 bytes per row with ASCII preview
        hex_lines: list[str] = []
        for i in range(0, len(self.data), 16):
            chunk = self.data[i:i+16]
            hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(47)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            hex_lines.append(f"0x{i:06x}  {hex_part} |{ascii_part}|")

        return Text("\n".join(hex_lines), style="dim green not bold")

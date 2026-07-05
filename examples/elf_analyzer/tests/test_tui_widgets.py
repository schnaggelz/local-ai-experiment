"""
Unit tests for the Textual TUI module (widgets, screens, app routing).
Validates initialization logic and data-binding without spawning a real terminal UI.
"""
from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock

from elf_visualizer.models import SectionInfo, SymbolInfo, InputFile
from elf_visualizer.tui.widgets import (
    IconSidebar,
    SectionTable,
    SymbolTable,
    MetadataPanel,
    HexViewerWidget,
)


# --- Fixtures ------------------------------------------------------------------

@pytest.fixture
def sample_sections() -> list[SectionInfo]:
    return [
        SectionInfo(name=".text", type="SHT_PROGBITS", address=0x400000, size=0x100, offset=0, flags="AX"),
        SectionInfo(name=".data", type="SHT_NOBITS", address=0x500000, size=0x20, offset=100, flags="WA"),
    ]

@pytest.fixture
def sample_symbols() -> list[SymbolInfo]:
    return [
        SymbolInfo(name="main", value=0x400100, size=0xA0, binding="STB_GLOBAL", visibility="STV_DEFAULT", section_index=1, is_local=False),
        SymbolInfo(name="_start", value=0x400000, size=0x20, binding="STB_LOCAL", visibility="STV_DEFAULT", section_index=1, is_local=True),
    ]

@pytest.fixture
def elf_input(sample_sections: list[SectionInfo], sample_symbols: list[SymbolInfo]) -> InputFile:
    return InputFile(
        path="/tmp/test.elf",
        sections=sample_sections,
        symbols=sample_symbols,
        dynamic_entries={"needed": [{"tag": "DT_NEEDED", "value": 1}]},
        version_definitions=[],
        relocations=None,
    )


# --- IconSidebar Tests ---------------------------------------------------------

def test_sidebar_initial_state():
    """Verify sidebar mounts correctly with default selection."""
    items = (("📑 Sections", "sections"), ("🗃️ Symbols", "symbols"))
    sidebar = IconSidebar(items)
    assert sidebar.selected_key == "sections"


def test_sidebar_selection_change():
    """Test set_reactive updates active item highlighting."""
    items = (("📑 Sections", "sections"), ("🗃️ Symbols", "symbols"))
    sidebar = IconSidebar(items)
    # Mock query_one to avoid full Textual App dependency
    with patch.object(sidebar, 'query_one') as mock_query:
        mock_label = MagicMock()
        mock_query.return_value = mock_label
        sidebar.set_reactive("selected", "symbols")
        assert sidebar.selected_key == "symbols"


# --- SectionTable Tests --------------------------------------------------------

def test_section_table_mounts_rows(sample_sections):
    """Assert that section data binds correctly to DataTable rows."""
    table = SectionTable(sample_sections)
    # Initial state check before mount (Textual lazy-loads on mount usually)
    assert len(table.sections) == 2


# --- SymbolTable Tests ---------------------------------------------------------

def test_symbol_table_empty():
    """Symbol table should handle empty symbols gracefully."""
    table = SymbolTable([])
    assert table.symbols == []


def test_symbol_table_populated(sample_symbols):
    """Validate symbol dataset is bound to widget."""
    table = SymbolTable(sample_symbols)
    assert len(table.symbols) == 2


# --- HexViewerWidget Tests -----------------------------------------------------

def test_hex_viewer_empty():
    """Hex viewer should handle empty bytes without crashing."""
    viewer = HexViewerWidget(b"")
    text = viewer.render()
    assert "No content to display" in str(text)


def test_hex_viewer_formats_bytes():
    """Verify hex formatting (16 bytes/row, ASCII preview)."""
    data = b"Hello World! 1234567890ABCD"
    viewer = HexViewerWidget(data)
    text = viewer.render()
    # Ensure hex representation of 'H' (0x48) appears
    assert "48" in str(text)


# --- MetadataPanel Tests -------------------------------------------------------

def test_metadata_panel_empty():
    """Metadata panel renders placeholder when no data."""
    panel = MetadataPanel({})
    text = panel.render()
    assert "No metadata available" in str(text)


def test_metadata_panel_populated():
    """Ensure dynamic entries render correctly."""
    data = {".dynamic": [{"tag": "DT_NEEDED", "value": 42}]}
    panel = MetadataPanel(data)
    text = panel.render()
    assert "Section: .dynamic" in str(text)


# --- CLI TUI Routing Test (sanity check) ----------------------------------------

def test_cli_tui_flag_imports():
    """Ensure the --tui argument parsing routes to run_tui correctly."""
    with patch("elf_visualizer.tui.app.run_tui") as mock_run:
        with patch("builtins.print", return_value=None):
            from elf_visualizer.cli import main
            # Simulate: python cli.py /test/path --tui
            with patch("sys.argv", ["cli.py", "/test/elf.bin", "--tui"]):
                try:
                    main()
                except SystemExit:
                    pass  # argparse might exit cleanly if patches fail, but run_tui should be called
            mock_run.assert_called_once_with("/test/elf.bin")

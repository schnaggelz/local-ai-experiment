"""
Unit tests for the visualizer module.
Tests render_section_table, render_hex_dump, and render_section_content functions.
"""
import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from elf_visualizer.models import SectionInfo
from elf_visualizer.visualizer import (
    render_section_table,
    render_hex_dump,
    render_section_content,
)

def test_render_section_table_basic():
    """Test that render_section_table creates a proper table."""
    # Create mock data
    sections = [
        SectionInfo(
            name=".text",
            type="SHT_PROGBITS", 
            address=0x400000,
            size=0x1000,
            offset=0x400000,
            flags="AX"
        ),
        SectionInfo(
            name=".data",
            type="SHT_PROGBITS",
            address=0x401000, 
            size=0x200,
            offset=0x401000,
            flags="WA"
        )
    ]
    elf_file = Mock(path="/test/binary.elf", sections=sections)
    console = Console()

    # Capture output by patching console.print
    with patch.object(console, 'print') as mock_print:
        render_section_table(elf_file, console)
        
        # Verify print was called (table rendering)
        assert mock_print.called

def test_render_hex_dump_with_content():
    """Test hex dump rendering when content is available."""
    section = SectionInfo(
        name=".text",
        type="SHT_PROGBITS",
        address=0x400000,
        size=12,
        offset=0x400000,
        flags="AX",
        content=b"Hello World!"
    )
    console = Console()

    with patch.object(console, 'print') as mock_print:
        render_hex_dump(section, console)
        
        # Should print hex dump header and syntax
        assert any("Hex Dump:" in str(call) for call in mock_print.call_args_list)

def test_render_hex_dump_no_content():
    """Test that render_hex_dump does nothing when no content."""
    section = SectionInfo(
        name=".text",
        type="SHT_PROGBITS", 
        address=0x400000,
        size=12,
        offset=0x400000,
        flags="AX",
        content=None
    )
    console = Console()

    with patch.object(console, 'print') as mock_print:
        render_hex_dump(section, console)
        
        # Should not print anything when no content
        assert not any("Hex Dump:" in str(call) for call in mock_print.call_args_list)

def test_render_section_content_small_with_content():
    """Test rendering small section with content."""
    section = SectionInfo(
        name=".text",
        type="SHT_PROGBITS",
        address=0x400000,
        size=100,  # <= 256
        offset=0x400000,
        flags="AX", 
        content=b"Small content"
    )
    console = Console()

    with patch.object(console, 'print') as mock_print:
        render_section_content(section, console)
        
        # Should call render_hex_dump for small section with content
        assert any("Hex Dump:" in str(call) for call in mock_print.call_args_list)

def test_render_section_content_small_no_content():
    """Test rendering small section without content."""
    section = SectionInfo(
        name=".text",
        type="SHT_PROGBITS",
        address=0x400000,
        size=100,  # <= 256
        offset=0x400000,
        flags="AX",
        content=None
    )
    console = Console()

    with patch.object(console, 'print') as mock_print:
        render_section_content(section, console)
        
        # Should not print anything when no content
        assert not any("Hex Dump:" in str(call) for call in mock_print.call_args_list)

def test_render_section_content_large_with_content():
    """Test rendering large section with content (should skip dump)."""
    section = SectionInfo(
        name=".bss",
        type="SHT_NOBITS",
        address=0x402000,
        size=1024,  # > 256
        offset=0x402000,
        flags="WA",
        content=b"Large content"
    )
    console = Console()

    with patch.object(console, 'print') as mock_print:
        render_section_content(section, console)
        
        # Should print message about section being too large
        assert any("too large to dump" in str(call).lower() for call in mock_print.call_args_list)

def test_render_section_content_large_no_content():
    """Test rendering large section without content."""
    section = SectionInfo(
        name=".bss",
        type="SHT_NOBITS",
        address=0x402000,
        size=1024,  # > 256
        offset=0x402000,
        flags="WA",
        content=None
    )
    console = Console()

    with patch.object(console, 'print') as mock_print:
        render_section_content(section, console)
        
        # Should not print anything when no content and large size
        assert not any("too large to dump" in str(call).lower() for call in mock_print.call_args_list)
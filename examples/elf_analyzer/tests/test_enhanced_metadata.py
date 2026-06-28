"""
Unit tests for enhanced metadata extraction (symbols, relocations, dynamic sections, version definitions).
Tests the new functionality added in Phase 8 of the implementation.
"""
import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from elf_visualizer.models import SectionInfo, SymbolInfo, RelocationEntry, VersionDefinition, InputFile
from elf_visualizer.visualizer import (
    render_symbol_table,
    render_relocation_entries,
    render_dynamic_sections,
    render_version_definitions
)

def test_render_dynamic_sections_empty():
    """Test dynamic sections rendering with empty dict."""
    console = Console()
    
    with patch.object(console, 'print') as mock_print:
        render_dynamic_sections({}, console)
        
        # Should print "No dynamic sections found" message
        assert any("No dynamic sections found" in str(call) for call in mock_print.call_args_list)

def test_render_version_definitions_empty():
    """Test version definitions rendering with empty list."""
    console = Console()
    
    with patch.object(console, 'print') as mock_print:
        render_version_definitions([], console)
        
        # Should print "No version definitions found" message
        assert any("No version definitions found" in str(call) for call in mock_print.call_args_list)

def test_symbol_info_creation():
    """Test SymbolInfo model creation."""
    symbol = SymbolInfo(
        name=".text",
        value=0x400000,
        size=0x1000,
        binding="STB_GLOBAL",
        visibility="STV_DEFAULT",
        section_index=1,
        is_local=False
    )
    
    assert symbol.name == ".text"
    assert symbol.value == 0x400000
    assert symbol.size == 0x1000
    assert symbol.binding == "STB_GLOBAL"
    assert symbol.visibility == "STV_DEFAULT"
    assert symbol.section_index == 1
    assert symbol.is_local == False

def test_relocation_entry_creation():
    """Test RelocationEntry model creation."""
    reloc = RelocationEntry(
        offset=0x400000,
        info=0x1234,
        addend=0x5678,
        symbol_index=2,
        section_type="rela"
    )
    
    assert reloc.offset == 0x400000
    assert reloc.info == 0x1234
    assert reloc.addend == 0x5678
    assert reloc.symbol_index == 2
    assert reloc.section_type == "rela"

def test_version_definition_creation():
    """Test VersionDefinition model creation."""
    version = VersionDefinition(
        version_name="v1",
        hash_value=0x12345678,
        auxiliary_vector=[1, 2, 3],
        timestamp=1234567890
    )
    
    assert version.version_name == "v1"
    assert version.hash_value == 0x12345678
    assert version.auxiliary_vector == [1, 2, 3]
    assert version.timestamp == 1234567890

def test_input_file_with_enhanced_metadata():
    """Test InputFile model with enhanced metadata fields."""
    sections = [
        SectionInfo(
            name=".text",
            type="SHT_PROGBITS",
            address=0x400000,
            size=0x1000,
            offset=0x400000,
            flags="AX"
        )
    ]
    
    symbols = [
        SymbolInfo(
            name=".text",
            value=0x400000,
            size=0x1000,
            binding="STB_GLOBAL",
            visibility="STV_DEFAULT",
            section_index=0,
            is_local=False
        )
    ]
    
    relocations = [
        RelocationEntry(
            offset=0x400000,
            info=0x1234,
            addend=None,
            symbol_index=0,
            section_type="rel"
        )
    ]
    
    version_definitions = [
        VersionDefinition(
            version_name="v1",
            hash_value=0x12345678,
            auxiliary_vector=[],
            timestamp=1234567890
        )
    ]
    
    input_file = InputFile(
        path="/test/binary.elf",
        sections=sections,
        symbols=symbols,
        relocations=relocations,
        dynamic_entries=None,
        version_definitions=version_definitions
    )
    
    assert input_file.path == "/test/binary.elf"
    assert len(input_file.sections) == 1
    assert len(input_file.symbols) == 1
    assert len(input_file.relocations) == 1
    assert len(input_file.version_definitions) == 1
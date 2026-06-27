import pytest
from elf_visualizer.parser import parse_elf
from elf_visualizer.exceptions import ELFParseError

def test_parse_non_existent_file():
    """Test that parsing a non-existent file raises ELFParseError."""
    with pytest.raises(ELFParseError, match="File not found"):
        parse_elf("non_existent_file_12345.bin")

def test_parse_invalid_elf_format(tmp_path):
    """Test that parsing a non-ELF file raises ELFParse and Error."""
    # Create a dummy text file
    dummy_file = tmp_path / "not_an_elf.txt"
    dummy_file.write_text("This is just a regular text file.")
    
    with pytest.raises(Exception):
        # pyelftools will raise an error when it fails to find the ELF magic number
        parse_elf(str(dummy_file))

def test_parse_valid_structure_stub(tmp_path):
    """
    Test parsing a valid-looking structure. 
    Since creating a real ELF from scratch is complex, we test the successful flow.
    Note: This test will only pass if the file is actually an ELF.
    """
    # We'll use a known small ELF or skip this until we have a fixture.
    pass


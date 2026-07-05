import pytest
from elf_visualizer.parser import parse_elf
from elf_visualizer.exceptions import ELFParseError


def test_parse_non_existent_file():
    """Test that parsing a non-existent file raises ELFParseError."""
    with pytest.raises(ELFParseError, match="File not found"):
        parse_elf("non_existent_file_12345.bin")


def test_parse_invalid_elf_format(tmp_path):
    """Test that parsing a non-ELF file raises ELFParseError."""
    dummy_file = tmp_path / "not_an_elf.txt"
    dummy_file.write_text("This is just a regular text file.")

    with pytest.raises(ELFParseError):
        parse_elf(str(dummy_file))


# ---------- real-binary structure tests ------------------------------------------


def test_parse_dynamic_elf_structure(dynamic_elf):  # noqa: F811 - fixture from conftest
    """Parse the dynamically-linked binary and assert well-known section names."""
    data = parse_elf(dynamic_elf)
    assert len(data.sections) > 5, "Dynamic binary should have multiple sections"

    names = {s.name for s in data.sections}
    for expected in (".text", ".data", ".bss", ".rodata", ".interp"):
        assert expected in names, f"Missing expected section: {expected}"


def test_parse_static_elf_structure(static_elf):  # noqa: F811 - fixture from conftest
    """Parse the static binary and verify no dynamic-linker artefacts."""
    data = parse_elf(static_elf)
    names = {s.name for s in data.sections}

    assert ".interp" not in names, "Static build must not have .interp"
    assert ".dynamic" not in names, "Static build must not have .dynamic"


def test_static_vs_dynamic_section_count(static_elf, dynamic_elf):  # noqa: F811 - fixture from conftest
    """Dynamic binary should carry at least as many sections (usually more) due to linker needs."""
    static_data = parse_elf(static_elf)
    dynamic_data = parse_elf(dynamic_elf)

    assert len(dynamic_data.sections) >= len(static_data.sections), (
        "Dynamic binary typically has equal or more sections than static"
    )

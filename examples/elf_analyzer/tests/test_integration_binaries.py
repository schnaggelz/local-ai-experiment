import subprocess
import os
from elf_visualizer.parser import parse_elf

def test_dynamic_bin_has_sections(dynamic_elf):
    """Verify that the dynamic binary has sections and common ones like .text."""
    elf_file = parse_supp_elf(dynamic_elf)
    assert len(elf_file.sections) > 0
    section_names = [s.name for s in elf_file.sections]
    assert any(".text" in name for name in section_names)
    assert any(".dynsym" in name for name in section_names)

def test_static_bin_has_no_dynamic_relocations(static_elf):
    """Verify that the static binary correctly reflects its nature."""
    elf_file = parse_supp_elf(static_elf)
    section_names = [s.name for s in elf_file.sections]
    assert ".dynamic" not in section_names

def test_shared_library_can_be_parsed(shared_lib_elf):
    """Verify that a shared library (.so) can be parsed."""
    elf_file = parse_supp_elf(shared_lib_elf)
    assert len(elf_file.sections) > 0

def parse_supp_elf(path):
    """Helper to parse an ELF file and return InputFile object."""
    return parse_elf(path)

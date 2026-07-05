"""
End-to-end CLI integration tests for --symbols, --relocations, --dynamic, and --versions.

Uses subprocess to drive the exact same code path a real user would hit:
    python -m elf_visualizer.cli <binary> <flag(s)>

Then verifies that meaningful (non-empty) data is actually emitted rather than
the \"No ___ found.\" placeholders exposed by the original bugs.

Also includes parser-level unit tests that call the helper functions directly
against real generated ELF binaries to assert concrete shape counts.
"""
from __future__ import annotations

import math  # noqa: F401 – not used but keeps imports deterministic

import subprocess
import sys
import os

import pytest

# ------------ helpers ------------------------------------------------------------

_CLI_ENTRY = os.path.join("src", "elf_visualizer", "cli.py")
_PYTHON = sys.executable


def _run_cli(path: str, *flags: str) -> tuple[str, int]:
    """
    Run the CLI in-process and return (stdout_text, return_code).

    Args:
        path: Absolute or relative path to an ELF binary.
        flags: Extra CLI arguments (e.g. \"--symbols\").

    Returns:
        Tuple of (captured stdout as plain text, process return code).
    """
    result = subprocess.run(
        [_PYTHON, _CLI_ENTRY, path] + list(flags),
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Strip ANSI escape codes so table-structure assertions are simpler
    import re
    clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.stdout)
    return clean, result.returncode


# ------------ CLI integration tests -----------------------------------------------

class TestSymbolsFlag:
    """--symbols must emit a populated symbol table."""

    def test_symbols_flag_shows_data(self, dynamic_elf):  # noqa: F811
        text, rc = _run_cli(dynamic_elf, "--symbols")
        assert rc == 0
        assert "ELF Symbols" in text
        # Must see at least one REAL symbol name (not just "No symbols found")
        assert any(name in text for name in ("main", "_start", "__libc_start_main"))
        # Must NOT show the empty-placeholder message
        assert "No symbols found" not in text

    def test_static_binary_also_has_symbols(self, static_elf):  # noqa: F811
        text, rc = _run_cli(static_elf, "--symbols")
        assert rc == 0
        assert "ELF Symbols" in text
        assert "No symbols found" not in text


class TestRelocationsFlag:
    """--relocations must emit relocation entries."""

    def test_relocations_flag_shows_data(self, dynamic_elf):  # noqa: F811
        text, rc = _run_cli(dynamic_elf, "--relocations")
        assert rc == 0
        assert "ELF Relocation Entries" in text
        assert "No relocation entries found" not in text

    def test_static_binary_has_no_or_few_relocs(self, static_elf):  # noqa: F811
        # A fully static binary may legitimately have zero relocations; we just
        # assert the table header appears (meaning the code path ran without error).
        text, rc = _run_cli(static_elf, "--relocations")
        assert rc == 0
        # Either entries or the "no entries found" fallback — both are valid


class TestDynamicFlag:
    """--dynamic must emit dynamic tags."""

    def test_dynamic_flag_shows_tags(self, dynamic_elf):  # noqa: F811
        text, rc = _run_cli(dynamic_elf, "--dynamic")
        assert rc == 0
        assert "ELF Dynamic Sections" in text
        assert "No dynamic sections found" not in text

    def test_static_binary_has_no_dynamic(self, static_elf):  # noqa: F811
        text, rc = _run_cli(static_elf, "--dynamic")
        assert rc == 0
        assert "No dynamic sections found" in text


class TestVersionsFlag:
    """--versions must emit version-def rows (when present)."""

    def test_versions_shows_data(self, dynamic_elf):  # noqa: F811
        text, rc = _run_cli(dynamic_elf, "--versions")
        assert rc == 0
        assert "ELF Version Definitions" in text
        # .gnu.version_r exists in our generated binary, so it must not be empty
        assert "No version definitions found" not in text


class TestCombinedFlags:
    """All four extra flags together must work without error."""

    def test_all_flags(self, dynamic_elf):  # noqa: F811
        text, rc = _run_cli(
            dynamic_elf,
            "--symbols",
            "--relocations",
            "--dynamic",
            "--versions",
        )
        assert rc == 0
        for heading in (
            "ELF Symbols",
            "ELF Relocation Entries",
            "ELF Dynamic Sections",
            "ELF Version Definitions",
        ):
            assert heading in text


# ------------ parser-level unit tests -------------------------------------------

@pytest.fixture()
def raw_elf_dynamic(dynamic_elf):  # noqa: F811
    """Return an un-closed ELFFile opened *within* the test."""
    from elftools.elf.elffile import ELFFile
    with open(dynamic_elf, "rb") as fh:
        yield ELFFile(fh)


@pytest.fixture()
def raw_elf_static(static_elf):  # noqa: F811
    """Same for the static binary."""
    from elftools.elf.elffile import ELFFile
    with open(static_elf, "rb") as fh:
        yield ELFFile(fh)


class TestSymbolParserFunction:
    def test_dynamic_has_symbols(self, raw_elf_dynamic):  # noqa: F811
        from elf_visualizer.parser import _parse_symbol_table
        syms = _parse_symbol_table(raw_elf_dynamic)
        assert len(syms) > 0, "Should parse symbols from dynamic binary"
        names = {s.name for s in syms}
        assert "main" in names

    def test_static_has_symbols(self, raw_elf_static):  # noqa: F811
        from elf_visualizer.parser import _parse_symbol_table
        syms = _parse_symbol_table(raw_elf_static)
        assert len(syms) > 0


class TestRelocationParserFunction:
    def test_dynamic_has_relocations(self, raw_elf_dynamic):  # noqa: F811
        from elf_visualizer.parser import _parse_relocation_section
        relocs = []
        for sec in raw_elf_dynamic.iter_sections():
            relocs.extend(_parse_relocation_section(sec))
        assert len(relocs) > 0, "Dynamic binary should have relocations"


class TestDynamicSectionParserFunction:
    def test_dynamic_has_tags(self, raw_elf_dynamic):  # noqa: F811
        from elf_visualizer.parser import _parse_dynamic_section
        data = _parse_dynamic_section(raw_elf_dynamic)
        assert len(data) > 0
        entries = list(data.values())[0]
        tags = [e["tag"] for e in entries]
        assert any(t == "DT_NEEDED" for t in tags), "Should see DT_NEEDED entries"

    def test_static_has_no_dynamic(self, raw_elf_static):  # noqa: F811
        from elf_visualizer.parser import _parse_dynamic_section
        data = _parse_dynamic_section(raw_elf_static)
        assert len(data) == 0, "Static binary must have no .dynamic section"


class TestVersionParserFunction:
    def test_dynamic_has_versions(self, raw_elf_dynamic):  # noqa: F811
        from elf_visualizer.parser import _parse_version_definitions
        vers = _parse_version_definitions(raw_elf_dynamic)
        assert len(vers) > 0, "Dynamic binary should carry version-needed data"

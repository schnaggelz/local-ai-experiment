# ELF Visualizer

A command-line tool for inspecting and visualizing ELF (Executable and Linkable Format) binaries.

## Overview

The ELF Visualizer is a Python-based CLI application that parses ELF files and presents their section information in an easy-to-read format. It uses `pyelftools` for parsing, `rich` for beautiful console output, and `pydantic v2` for data validation. It features an interactive TUI mode powered by `textual` for deep, navigable inspection of complex binaries.

## Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package installer)

### Quick Install
```bash
pip install elf-visualizer
```

Or install from the local directory:
```bash
cd /path/to/elf-analyzer/examples/elf_analyzer
pip install -e .
```

## Usage

The ELF Visualizer operates in two modes: **Batch Mode** (standard CLI output) and **Interactive TUI Mode** (reactive terminal UI).

### 1. Interactive TUI Mode (Recommended)
Launch a fully interactive, navigable interface using the `--tui` flag. Built with `textual`, it allows live search, table sorting, and view switching without restarting the tool.

```bash
elf_visualizer /path/to/binary.elf --tui
```

**Key Bindings:**
| Key | Action |
|-----|--------|
| `q` | Quit application |
| `d` | Toggle Dark/Light mode |
| `1`/`2`/`3`/`4` | Switch between Sections, Symbols, Relocations, and Dynamic Info views |
| `↑`/`↓` | Navigate within tables (Sections/Symbols) |
| Double-click | Inspect raw hex data for a specific section |

### 2. Batch Mode (Standard Output)
For script integration or quick lookups, run without flags or use the enhanced metadata arguments.

```bash
# Display section table for an ELF binary
elf_visualizer /path/to/binary.elf
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `path` | Path to the ELF binary file to analyze (required) |
| `--tui` | Launch the interactive Textual TUI interface |
| `--dump` | Display hex dump for small sections (≤256 bytes) in batch mode |
| `--symbols` | Parse and display `.symtab` / `.dynsym` tables |
| `--relocations` | Extract and list static/dynamic relocation entries |
| `--dynamic` | Show dynamic linker tags and dependencies (`.dynamic`) |
| `--versions` | Display version definitions (`.gnu.version_r`) |

## Example TUI Interface

```shell
 $ elf_visualizer /sys/bin/ls --tui ╭──── Header: ls ────────────╮
┏━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━┓ ┃  🔍 Search...              │
┣━━━━━━━━━╇━━━━━━━━━━━━━━━╇───────┫ ┃                            │
┃ Sections┃ .text         ┃ ...   ┃ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┃ Symbols ┃ .data         ┃ ...   ┃ 
┃ Relocs  ┃ .bss          ┃ ...   ┃   ┌────────── Section Info ──────┐
┃ Dynamic ┃ .rodata       ┃ ...   ┃   │ Name: .text                  │
┗━━━━━━━━━┻━━━━━━━━━━━━━━━┻━━━━━━─┛   │ Type: SHT_PROGBITS [AX]      │
                                      └──────────────────────────────┘
╰── Footer: 1 Sections | q Quit ─────────────────────────────────────╯
```

## Example Batch Output

### Basic Table View (Batch Mode)
```
┌─────────────┬──────────────────┬──────────────┬─────────────┬────────┬─────────────┐
│ Index       │ Section Name     │ Type         │ VADDR       │ Size   │ Flags       │
├─────────────┼──────────────────┼──────────────┼─────────────┼────────┼─────────────┤
│ 0           │ .text            │ SHT_PROGBITS │ 0x400000    │ 0x1000 │ AX          │
│ 1           │ .data            │ SHT_PROGBITS │ 0x401000    │ 0x200  │ WA          │
│ 2           │ .bss             │ SHT_NOBITS   │ 0x402000    │ 0x100  │ WA          │
└─────────────┴──────────────────┴──────────────┴─────────────┴────────┴─────────────┘
```

### With Hex Dump (for small sections)
```section: .text (SHT_PROGBITS)
vaddr: 0x400000, Size: 0x1000 bytes
hex dump:
00400000: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21 90 90 90 90  Hello World!....
00400010: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21 90 90 90 90  Hello World!....
```

## Features

- **Interactive TUI Mode**: Native terminal UI powered by `textual` for intuitive navigation, searching, and live inspection of ELF structures.
- **Deep Metadata Extraction**: Analyze symbol tables (`.symtab`, `.dynsym`), relocations (`.rela`, `.rel`), dynamic tags (`.dynamic`), and version definitions (`.gnu.version_r`).
- **Robust Parsing**: Uses `pyelftools` to gracefully handle various ELF formats, architectures, and malformed binaries.
- **Beautiful Output**: Rich console tables with color-coded metadata for easy skimming.
- **Type Safety & Performance**: Pydantic v2 models ensure data integrity; heavy sections are lazily loaded until viewed.

## Development Setup

### Clone the Repository
```bash
git clone <repository-url>
cd elf-analyzer/examples/elf_analyzer
```

### Install in Development Mode
```bash
pip install -e .
```

### Running Tests
```bash
pytest
```

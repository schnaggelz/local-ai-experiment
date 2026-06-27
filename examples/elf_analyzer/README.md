# ELF Visualizer

A command-line tool for inspecting and visualizing ELF (Executable and Linkable Format) binaries.

## Overview

The ELF Visualizer is a Python-based CLI application that parses ELF files and presents their section information in an easy-to-read format. It uses `pyelftools` for parsing, `rich` for beautiful console output, and `pydantic` for data validation.

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

## Basic Usage

### Simple Inspection
```bash
# Display section table for an ELF binary
elf_visualizer /path/to/binary.elf
```

### With Hex Dump
```bash
# Show hex dump for small sections (≤256 bytes)
elf_visualizer /path/to/binary.elf --dump
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `path` | Path to the ELF binary file to analyze |
| `--dump` | Display hex dump for small sections (≤256 bytes) |

## Example Output

### Basic Table View
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
```
Section: .text (SHT_PROGBITS)
VADDR: 0x400000, Size: 0x1000 bytes
Hex dump:
00400000: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21 90 90 90 90  Hello World!....
00400010: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21 90 90 90 90  Hello World!....
```

## Features

- **Robust Parsing**: Uses `pyelftools` to handle various ELF formats and architectures
- **Beautiful Output**: Rich console tables with color support
- **Error Handling**: Graceful error messages for invalid files or parsing issues
- **Type Safety**: Pydantic models ensure data integrity
- **Extensible**: Easy to add new visualization features

## Development Setup

### Clone the Repository
```bash
git clone <repository-url>
cd elf-analyzer/examples/elf_analyzer
```

### Install in Development Mode
```bash
pip install -e .
```\n
### Running Tests
```bash
pytest
```

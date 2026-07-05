import argparse
import sys
import os

# Add src directory to sys.path to allow package imports when running from any location
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rich.console import Console

from elf_visualizer.parser import parse_elf, _parse_symbol_table, _parse_relocation_section, _parse_dynamic_section, _parse_version_definitions
from elftools.elf.elffile import ELFFile
from elf_visualizer.visualizer import render_section_table, render_section_content, render_symbol_table, render_relocation_entries, render_dynamic_sections, render_version_definitions
from elf_visualizer.exceptions import ELFParseError

def main() -> None:
    """Main entry point for the ELF visualizer CLI."""
    parser = argparse.ArgumentParser(
        description="ELF Visualizer: A tool to inspect ELF binaries."
    )
    parser.add_argument(
        "path", 
        help="Path to the ELF binary file to analyze"
    )
    parser.add_argument(
        "--dump", 
        action="store_true", 
        help="Display hex dump for small sections (<= 256 bytes)"
    )
    parser.add_argument(
        "--symbols",
        action="store_true",
        help="Extract and display symbol table information"
    )
    parser.add_argument(
        "--relocations", 
        action="store_true",
        help="Extract and display relocation entries"
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Extract and display dynamic section information"
    )
    parser.add_argument(
        "--versions",
        action="store_true",
        help="Extract and display version definitions"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch the interactive Textual TUI mode"
    )

    args = parser.parse_args()

    # Fast-path for interactive TUI mode
    if args.tui:
        from elf_visualizer.tui.app import run_tui
        run_tui(args.path)
        return

    console = Console()

    try:
        # 1. Parse the ELF file
        elf_file = parse_elf(args.path)

        # 2. Render the main table
        render_section_table(elf_file, console)

        # 3. Handle content dumping if requested
        if args.dump:
            for section in elf_file.sections:
                render_section_content(section, console)

        # 4. Enhanced metadata extraction based on flags
        if args.symbols or args.relocations or args.dynamic or args.versions:
            # Re-open the file to parse enhanced metadata
            with open(args.path, 'rb') as f:
                elf = ELFFile(f)

                symbols: list | None = None
                if args.symbols:
                    symbols = _parse_symbol_table(elf)
                    render_symbol_table(symbols, console)

                if args.relocations:
                    relocations = []
                    for section in elf.iter_sections():
                        relocations.extend(_parse_relocation_section(section))
                    # Share symbols for reference resolution when already parsed,
                    # otherwise parse them just for this purpose
                    render_relocation_entries(
                        relocations,
                        console,
                        symbols if symbols is not None else _parse_symbol_table(elf),
                    )

                if args.dynamic:
                    dynamic_data = _parse_dynamic_section(elf)
                    render_dynamic_sections(dynamic_data, console)

                if args.versions:
                    versions = _parse_version_definitions(elf)
                    render_version_definitions(versions, console)

    except ELFParseError as e:
        console.print(f"[bold red]Parsing Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    main()

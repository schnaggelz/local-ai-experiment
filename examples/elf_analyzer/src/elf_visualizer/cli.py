import argparse
import sys
import os

# Add src directory to sys.path to allow package imports when running from any location
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rich.console import Console
from elf_visualizer.parser import parse_elf
from elf_visualizer.visualizer import render_section_table, render_section_content
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

    args = parser.parse_args()
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

    except ELFParseError as e:
        console.print(f"[bold red]Parsing Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    main()

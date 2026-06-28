from rich.table import Table
from rich.console import Console
from rich.syntax import Syntax
from elf_visualizer.models import InputFile, SectionInfo

def render_section_table(elf_file: InputFile, console: Console) -> None:
    """Renders the ELF sections in a formatted table."""
    table = Table(title=f"Sections for {elf_file.path}", show_header=True, header_style="bold cyan")
    
    table.add_column("Idx", justify="right", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Type", style="magenta")
    table.add_column("VADDR", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Flags", justify="center")

    for idx, section in enumerate(elf_file.sections):
        table.add_row(
            str(idx),
            section.name,
            section.type,
            f"0x{section.address:x}",
            f"{section.size} B",
            section.flags
        )

    console.print(table)

def render_hex_dump(section: SectionInfo, console: Console) -> None:
    """Renders a hex dump for a section if content is available."""
    if not section.content or section.size == 0:
        return

    hex_data = section.content.hex(' ', 16)
    syntax = Syntax(hex_data, "text", theme="monokapi")
    
    console.print(f"\n[bold]Hex Dump: {section.name}[/bold]")
    console.print(syntax)

def render_section_content(section: SectionInfo, console: Console) -> None:
    """Logic to decide whether to show hex dump based on size."""
    if section.size <= 256 and section.content:
        render_hex_dump(section, console)
    elif section.size > 256:
        console.print(f"[dim]Section {section.name} too large to dump ({section.size} bytes).[/dim]")

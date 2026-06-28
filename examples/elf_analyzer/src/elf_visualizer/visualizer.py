from rich.table import Table
from rich.console import Console
from rich.syntax import Syntax
from elf_visualizer.models import InputFile, SectionInfo, SymbolInfo, RelocationEntry, VersionDefinition

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
    elif section.size > 256 and section.content:
        console.print(f"[dim]Section {section.name} too large to dump ({section.size} bytes).[/dim]")


def render_symbol_table(symbols: list[SymbolInfo], console: Console) -> None:
    """
    Renders the ELF symbol table in a formatted table.
    
    Args:
        symbols: List of SymbolInfo objects to display
        console: Rich console instance for output
    """
    if not symbols:
        console.print("[dim]No symbols found.[/dim]")
        return
    
    table = Table(title="ELF Symbols", show_header=True, header_style="bold cyan")
    
    table.add_column("Idx", justify="right", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Value", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Binding", style="magenta")
    table.add_column("Visibility", style="yellow")
    table.add_column("Section", justify="center")

    for idx, symbol in enumerate(symbols):
        # Color-code based on binding type
        binding_color = "green" if symbol.binding == "STB_GLOBAL" else "blue"
        visibility_color = "red" if symbol.visibility == "STV_HIDDEN" else "white"
        
        table.add_row(
            str(idx),
            symbol.name,
            f"0x{symbol.value:x}",
            f"{symbol.size} B",
            f"[{binding_color}]{symbol.binding}[/{binding_color}]",
            f"[{visibility_color}]{symbol.visibility}[/{visibility_color}]",
            str(symbol.section_index) if symbol.section_index > 0 else ""
        )

    console.print(table)

def render_relocation_entries(relocations: list[RelocationEntry], console: Console, symbols: Optional[list[SymbolInfo]] = None) -> None:
    """
    Renders ELF relocation entries in a formatted table.
    
    Args:
        relocations: List of RelocationEntry objects to display
        console: Rich console instance for output
        symbols: Optional list of SymbolInfo for reference resolution
    """
    if not relocations:
        console.print("[dim]No relocation entries found.[/dim]")
        return
    
    table = Table(title="ELF Relocation Entries", show_header=True, header_style="bold cyan")
    
    table.add_column("Idx", justify="right", style="dim")
    table.add_column("Offset", justify="right")
    table.add_column("Info", justify="right")
    table.add_column("Addend", justify="right")
    table.add_column("Symbol Ref", style="green")

    for idx, reloc in enumerate(relocations):
        # Try to resolve symbol reference if symbols are available
        symbol_ref = ""
        if symbols and reloc.symbol_index is not None:
            for symbol in symbols:
                if symbol.section_index == reloc.symbol_index:
                    symbol_ref = symbol.name
                    break
        
        table.add_row(
            str(idx),
            f"0x{reloc.offset:x}",
            f"0x{reloc.info:x}",
            str(reloc.addend) if reloc.addend is not None else "-",
            symbol_ref
        )

    console.print(table)

def render_dynamic_sections(dynamic_data: dict[str, Any], console: Console) -> None:
    """
    Renders ELF dynamic section entries in a formatted table.
    
    Args:
        dynamic_data: Dictionary containing parsed dynamic section data
        console: Rich console instance for output
    """
    if not dynamic_data:
        console.print("[dim]No dynamic sections found.[/dim]")
        return
    
    table = Table(title="ELF Dynamic Sections", show_header=True, header_style="bold cyan")
    
    table.add_column("Section Name", style="green")
    table.add_column("Tag", justify="center")
    table.add_column("Value", justify="right")

    for section_name, entries in dynamic_data.items():
        for entry in entries:
            tag_str = str(entry['tag'])
            value_str = str(entry['value']) if isinstance(entry['value'], int) else str(entry['value'])
            
            table.add_row(
                section_name,
                tag_str,
                value_str
            )

    console.print(table)

def render_version_definitions(versions: list[VersionDefinition], console: Console) -> None:
    """
    Renders ELF version definitions in a formatted table.
    
    Args:
        versions: List of VersionDefinition objects to display
        console: Rich console instance for output
    """
    if not versions:
        console.print("[dim]No version definitions found.[/dim]")
        return
    
    table = Table(title="ELF Version Definitions", show_header=True, header_style="bold cyan")
    
    table.add_column("Idx", justify="right", style="dim")
    table.add_column("Version Name", style="green")
    table.add_column("Hash", justify="right")
    table.add_column("Timestamp", justify="right")

    for idx, version in enumerate(versions):
        table.add_row(
            str(idx),
            version.version_name,
            f"0x{version.hash_value:x}",
            str(version.timestamp)
        )

    console.print(table)

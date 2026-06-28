from __future__ import annotations

import os
from elftools.elf.elffile import ELFFile
from .models import SectionInfo, InputFile, SymbolInfo, RelocationEntry, VersionDefinition
from .exceptions import ELFParseError

def parse_elf(file_path: str) -> InputFile:
    """
    Parses an ELF file and extracts section information safely.
    
    Args:
        file_path: Path to the ELF binary file to analyze
        
    Returns:
        InputFile instance containing parsed sections and metadata
        
    Raises:
        ELFParseError: If the file cannot be parsed or doesn't exist
    """
    if not os.path.exists(file_path):
        raise ELFParseError(f"File not found: {file_path}")

    try:
        sections_data: list[SectionInfo] = []
        with open(file_path, 'rb') as f:
            elf = ELFFile(f)
            for section in elf.iter_sections():
                name = section.name if section.name else "<unknown>"

                # Helper to safely format integers as hex strings
                def safe_hex(val) -> str:
                    try:
                        if isinstance(val, int):
                            return f"0x{val:x}"
                        return str(val)
                    except (TypeError, ValueError):
                        return str(val)

                # Extracting using standard sh_ (section header) keys
                s_type = section['sh_type']
                s_flags = section['sh_flags']
                addr = section['sh_addr']
                size = section['sh_size']
                offset = section['sh_offset']

                info = SectionInfo(
                    name=name,
                    type=safe_hex(s_type),
                    address=int(addr) if isinstance(addr, (int, float)) else 0,
                    size=int(size) if isinstance(size, (int, float)) else 0,
                    offset=int(offset) if isinstance(offset, (int, float)) else 0,
                    flags=safe_hex(s_flags)
                )
                sections_data.append(info)

            return InputFile(path=file_path, sections=sections_data)
    except Exception as e:
        raise ELFParseError(f"Failed to parse ELF file: {str(e)}")

def _parse_symbol_table(elf_file) -> list[SymbolInfo]:
    """
    Parse symbol table from an ELF file.
    
    Args:
        elf_file: ELFFile instance
        
    Returns:
        List of SymbolInfo objects
    """
    symbols = []
    for section in elf_file.iter_sections():
        if section['sh_type'] == 'SHT_SYMTAB' or section['sh_type'] == 'SHT_DYNSYM':
            try:
                symtab_section = section
                strtab_section = None
                
                # Find string table section (usually .strtab or .dynsym)
                for s in elf_file.iter_sections():
                    if s['sh_type'] == 'SHT_STRTAB' and (
                        '.strtab' in s.name.lower() or '.dynstr' in s.name.lower()
                    ):
                        strtab_section = s
                        break
                
                # Parse symbols from symbol table section
                for symbol in symtab_section.iter_symbols():
                    name = symbol.name if hasattr(symbol, 'name') else "<unnamed>"
                    value = symbol['st_value']
                    size = symbol['st_size']
                    binding = _get_symbol_binding_name(symbol.get('st_info', 0))
                    visibility = _get_symbol_visibility_name(symbol.get('st_other', 0))
                    section_index = symbol['st_shndx']
                    is_local = (symbol.get('st_info', 0) & 0xF) == 0  # STB_LOCAL
                    
                    symbols.append(SymbolInfo(
                        name=name,
                        value=value,
                        size=size,
                        binding=binding,
                        visibility=visibility,
                        section_index=section_index,
                        is_local=is_local
                    ))
            except Exception as e:
                # Skip problematic symbol tables but continue parsing
                continue
    
    return symbols

def _get_symbol_binding_name(st_info: int) -> str:
    """
    Convert ELF symbol binding info to human-readable name.
    
    Args:
        st_info: Symbol information byte from ELF header
        
    Returns:
        Human-readable binding name
    """
    if not isinstance(st_info, int):
        return "<unknown>"
    
    binding = (st_info >> 4) & 0xF
    bindings = {
        0: "STB_LOCAL",
        1: "STB_GLOBAL", 
        2: "STB_WEAK",
        10: "STB_GNU_UNIQUE"
    }
    return bindings.get(binding, f"<unknown:{binding}>")


def _get_symbol_visibility_name(st_other: int) -> str:
    """
    Convert ELF symbol visibility info to human-readable name.
    
    Args:
        st_other: Symbol other byte from ELF header
        
    Returns:
        Human-readable visibility name
    """
    if not isinstance(st_other, int):
        return "<unknown>"
    
    visibility = (st_other >> 5) & 0x3
    visibilities = {
        0: "STV_DEFAULT",
        1: "STV_INTERNAL",
        2: "STV_HIDDEN", 
        3: "STV_PROTECTED"
    }
    return visibilities.get(visibility, f"<unknown:{visibility}>")


def _parse_relocation_section(section) -> list[RelocationEntry]:
    """
    Parse relocation entries from a section.
    
    Args:
        section: ELF section containing relocations
        
    Returns:
        List of RelocationEntry objects
    """
    relocations = []
    try:
        if section['sh_type'] == 'SHT_RELA':
            # RELA format: offset, info, addend
            for rel in section.iter_relas():
                relocations.append(RelocationEntry(
                    offset=rel['r_offset'],
                    info=rel['r_info'],
                    addend=rel.get('r_addend'),
                    symbol_index=_get_symbol_index_from_r_info(rel['r_info']),
                    section_type="rela"
                ))
        elif section['sh_type'] == 'SHT_REL':
            # REL format: offset, info (no addend)
            for rel in section.iter_relocs():
                relocations.append(RelocationEntry(
                    offset=rel['r_offset'],
                    info=rel['r_info'],
                    addend=None,
                    symbol_index=_get_symbol_index_from_r_info(rel['r_info']),
                    section_type="rel"
                ))
    except Exception as e:
        # Skip problematic relocation sections
        pass
    
    return relocations

def _get_symbol_index_from_r_info(r_info: int) -> Optional[int]:
    """
    Extract symbol index from r_info field.
    
    Args:
        r_info: Relocation info field from ELF header
        
    Returns:
        Symbol index or None if not available
    """
    try:
        # Symbol table index is in the lower bits of r_info
        return r_info & 0xFFFFFFFF
    except (TypeError, ValueError):
        return None


def _parse_dynamic_section(elf_file) -> dict[str, Any]:
    """
    Parse dynamic section entries from an ELF file.
    
    Args:
        elf_file: ELFFile instance
        
    Returns:
        Dictionary containing parsed dynamic section data
    """
    dynamic_data = {}
    try:
        for section in elf_file.iter_sections():
            if section['sh_type'] == 'SHT_DYNAMIC':
                entries = []
                for dyn in section.iter_dicts():
                    entries.append({
                        'tag': dyn.d_tag,
                        'value': dyn.d_val
                    })
                dynamic_data[section.name] = entries
    except Exception as e:
        # Skip problematic dynamic sections
        pass
    
    return dynamic_data


def _parse_version_definitions(elf_file) -> list[VersionDefinition]:
    """
    Parse version definitions from an ELF file.
    
    Args:
        elf_file: ELFFile instance
        
    Returns:
        List of VersionDefinition objects
    """
    versions = []
    try:
        for section in elf_file.iter_sections():
            if section['sh_type'] == 'SHT_GNU_VERSION':
                # Parse version definitions from .gnu_version or .gnu_version_r
                for ver in section.iter_versions():
                    versions.append(VersionDefinition(
                        version_name=f"v{ver.vda_minor}",
                        hash_value=ver.vda_hash,
                        auxiliary_vector=list(ver.vda_aux),
                        timestamp=ver.vda_timestamp
                    ))
    except Exception as e:
        # Skip problematic version sections
        pass
    
    return versions


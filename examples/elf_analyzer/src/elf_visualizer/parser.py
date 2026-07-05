from __future__ import annotations

import os
from typing import Any, Optional
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
                # Parse symbols from symbol table section
                for symbol_obj in section.iter_symbols():
                    entry = symbol_obj.entry
                    name = symbol_obj.name or ''
                    value = entry.get('st_value', 0)
                    size = entry.get('st_size', 0)

                    # pyelftools wraps st_info/st_other as container dicts
                    st_info = entry['st_info']
                    st_other = entry.get('st_other', {})

                    if hasattr(st_info, 'get') and callable(getattr(st_info, 'get')):
                        binding = st_info.get('bind', 'unknown')
                    else:
                        binding = _get_symbol_binding_name_from_raw(int(st_info))

                    if hasattr(st_other, 'get') and callable(getattr(st_other, 'get')):
                        visibility = st_other.get('visibility', 'unknown')
                    else:
                        visibility = _get_symbol_visibility_name_from_raw(
                            int(st_other) if st_other else 0,
                        )

                    # Resolve section index (may be string like SHN_UNDEF)
                    sec_idx = entry.get('st_shndx', 0)
                    if isinstance(sec_idx, str):
                        sec_idx = 0

                    is_local = binding == 'STB_LOCAL'

                    symbols.append(SymbolInfo(
                        name=name,
                        value=value,
                        size=size,
                        binding=binding,
                        visibility=visibility,
                        section_index=sec_idx,
                        is_local=is_local
                    ))
            except Exception:
                # Skip problematic symbol tables but continue parsing
                continue
    
    return symbols

def _get_symbol_binding_name_from_raw(st_info: int) -> str:
    """
    Convert raw ELF symbol st_info byte to binding name (fallback path).

    Args:
        st_info: Raw st_info integer from section header.

    Returns:
        Human-readable binding name string.
    """
    if not isinstance(st_info, int):
        return "<unknown>"

    binding = (st_info >> 4) & 0xF
    bindings = {
        0: "STB_LOCAL",
        1: "STB_GLOBAL",
        2: "STB_WEAK",
        10: "STB_GNU_UNIQUE",
    }
    return bindings.get(binding, f"<unknown:{binding}>")


def _get_symbol_visibility_name_from_raw(st_other: int) -> str:
    """
    Convert raw ELF symbol st_other byte to visibility name (fallback path).

    Args:
        st_other: Raw st_other integer from section header.

    Returns:
        Human-readable visibility name string.
    """
    if not isinstance(st_other, int):
        return "<unknown>"

    visibility = (st_other >> 5) & 0x3
    visibilities = {
        0: "STV_DEFAULT",
        1: "STV_INTERNAL",
        2: "STV_HIDDEN",
        3: "STV_PROTECTED",
    }
    return visibilities.get(visibility, f"<unknown:{visibility}>")


def _parse_relocation_section(section) -> list[RelocationEntry]:
    """
    Parse relocation entries from a section.

    Args:
        section: ELF section containing relocations (SHT_REL or SHT_RELA)

    Returns:
        List of RelocationEntry objects
    """
    relocations = []
    try:
        is_rela = section['sh_type'] == 'SHT_RELA'
        # pyelftools uses a unified iter_relocations() for REL and RELA
        for rel_entry in section.iter_relocations():
            entry = rel_entry.entry
            relocations.append(RelocationEntry(
                offset=entry.get('r_offset', 0),
                info=entry.get('r_info', 0),
                addend=entry.get('r_addend') if is_rela else None,
                symbol_index=_get_symbol_index_from_r_info(
                    entry.get('r_info', 0)
                ),
                section_type="rela" if is_rela else "rel",
            ))
    except Exception:
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
    dynamic_data: dict[str, list[dict[str, Any]]] = {}
    try:
        for section in elf_file.iter_sections():
            if section['sh_type'] == 'SHT_DYNAMIC':
                entries: list[dict[str, Any]] = []
                for tag in section.iter_tags():
                    te = tag.entry
                    entries.append({
                        'tag': te.get('d_tag', 'unknown'),
                        'value': te.get('d_val', 0),
                    })
                dynamic_data[section.name] = entries
    except Exception:
        # Skip problematic dynamic sections
        pass

    return dynamic_data


def _parse_version_definitions(elf_file) -> list[VersionDefinition]:
    """
    Parse version definitions from an ELF file.

    Reads SHT_GNU_verneed (.gnu.version_r) sections which contain
    (Version_object, aux_generator) tuples returned by iter_versions().

    Args:
        elf_file: ELFFile instance

    Returns:
        List of VersionDefinition objects
    """
    versions = []
    try:
        for section in elf_file.iter_sections():
            if section['sh_type'] == 'SHT_GNU_verneed':
                # iter_versions() yields (Version, aux_generator) tuples
                for version_tuple in section.iter_versions():
                    ver_obj = version_tuple[0]
                    aux_gen = version_tuple[1]
                    ve = ver_obj.entry
                    # Extract hash values from auxiliary entries (Container dicts)
                    aux_values: list[int] = []
                    for aux_entry in aux_gen:
                        if hasattr(aux_entry, 'entry'):
                            val = aux_entry.entry.get('vna_hash', 0)
                        else:
                            val = int(aux_entry) if aux_entry else 0
                        aux_values.append(val)
                    versions.append(VersionDefinition(
                        version_name=str(ve.get('vn_version', 0)),
                        hash_value=ve.get('vn_cnt', 0),
                        auxiliary_vector=aux_values,
                        timestamp=0,  # not natively exposed by pyelftools
                    ))
    except Exception:
        # Skip problematic version sections
        pass

    return versions


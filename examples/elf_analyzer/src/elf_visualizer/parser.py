from __future__ import annotations

import os
from elftools.elf.elffile import ELFFile
from .models import SectionInfo, InputFile
from .exceptions import ELFParseError

def parse_elf(file_path: str) -> InputFile:
    """
    Parses an ELF file and extracts section information safely.
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
                # We use the safer attribute access provided by __pyelftools__
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


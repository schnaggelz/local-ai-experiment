from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum


class SectionType(str, Enum):
    """ELF section types."""
    SHT_PROGBITS = "SHT_PROGBITS"
    SHT_NOBITS = "SHT_NOBITS"
    SHT_SYMTAB = "SHT_SYMTAB"
    SHT_STRTAB = "SHT_STRTAB"
    SHT_RELA = "SHT_RELA"
    SHT_HASH = "SHT_HASH"
    SHT_DYNAMIC = "SHT_DYNAMIC"
    SHT_DYNSYM = "SHT_DYNSYM"
    UNKNOWN = "<unknown>"


class SymbolBinding(str, Enum):
    """Symbol binding types."""
    STB_LOCAL = "STB_LOCAL"
    STB_GLOBAL = "STB_GLOBAL"
    STB_WEAK = "STB_WEAK"
    UNKNOWN_BINDING = "<unknown>"


class SymbolVisibility(str, Enum):
    """Symbol visibility types."""
    STV_DEFAULT = "STV_DEFAULT"
    STV_INTERNAL = "STV_INTERNAL"
    STV_HIDDEN = "STV_HIDDEN"
    STV_PROTECTED = "STV_PROTECTED"
    UNKNOWN_VISIBILITY = "<unknown>"


class SectionInfo(BaseModel):
    """Represents metadata for a single ELF section."""
    model_config = ConfigDict(frozen=True)

    name: str
    type: str
    address: int
    size: int
    offset: int
    flags: str
    content: Optional[bytes] = None


class SymbolInfo(BaseModel):
    """Represents metadata for a single ELF symbol."""
    model_config = ConfigDict(frozen=True)

    name: str
    value: int
    size: int
    binding: str
    visibility: str
    section_index: int
    is_local: bool


class RelocationEntry(BaseModel):
    """Represents a single ELF relocation entry."""
    model_config = ConfigDict(frozen=True)

    offset: int
    info: int
    addend: Optional[int] = None
    symbol_index: Optional[int] = None
    section_type: str  # "rel" or "rela"


class VersionDefinition(BaseModel):
    """Represents a version definition in ELF."""
    model_config = ConfigDict(frozen=True)

    version_name: str
    hash_value: int
    auxiliary_vector: List[int]
    timestamp: int


class InputFile(BaseModel):
    """Represents the parsed ELF file containing multiple sections and metadata."""
    model_config = ConfigDict(frozen=True)

    path: str
    sections: list[SectionInfo]
    symbols: Optional[List[SymbolInfo]] = None
    relocations: Optional[List[RelocationEntry]] = None
    dynamic_entries: Optional[Dict[str, Any]] = None
    version_definitions: Optional[List[VersionDefinition]] = None

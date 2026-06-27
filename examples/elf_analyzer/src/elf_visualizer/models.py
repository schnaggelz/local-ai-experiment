from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


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


class ElfFile(BaseModel):
    """Represents the parsed ELF file containing multiple sections."""
    model_config = ConfigDict(frozen=True)

    path: str
    sections: list[SectionInfo]

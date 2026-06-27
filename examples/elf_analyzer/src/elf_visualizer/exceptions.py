class ELFError(Exception):
    """Base exception for all ELF visualizer errors."""

class ELFParseError(ELFError):
    """Raised when the ELF file cannot be parsed correctly."""

class ELFSectionError(ELFError):
    """Raised when an error occurs related to a specific section."""

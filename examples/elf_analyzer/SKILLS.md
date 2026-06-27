# Python Development Skills for ELF Visualizer

## Code Quality Standards

- **Type Hints**: Required in all public functions using `from __future__ import annotations`
- **Function Length**: Keep functions ≤ 5 lines where possible; extract complex logic to helper functions
- **Docstrings**: Every public function needs Args, Returns, and Raises sections
- **Error Handling**: Never use bare `except:` - always catch specific exceptions like `ELFParseError`

## Project Structure Conventions

```
src/
elf_visualizer/
    ├── __init__.py          # Package initialization (can remain empty)
    ├── models.py            # Pydantic data structures (SectionInfo, ElfFile)
    ├── parser.py            # ELF parsing logic using pyelftools
    ├── visualizer.py        # Console rendering with rich tables and hex dumps
    ├── cli.py               # Argument parsing and entry point
    └── exceptions.py        # Custom error hierarchy (ELFError, ELFParseError, ELFSectionError)

tests/
elf_visualizer/
    ├── __init__.py
    ├── test_parser.py       # Unit tests for parser module
    ├── test_visualizer.py   # UI rendering tests
    └── conftest.py          # Shared fixtures for sample ELF binaries
```

## Testing Requirements

- **Framework**: pytest with coverage tracking
- **Coverage Target**: ≥ 80% minimum threshold
- **Snapshot Tests**: Use for console output verification
- **Fixtures**: Include real ELF samples in `tests/data/` (e.g., `/bin/ls`, the tool itself)

## Development Setup

### Installation

```bash
# Install package in development mode
pip install -e .

# Install with all dependencies
pip install -e .[dev]
```

### Testing Commands

```bash
# Run tests with coverage
pytest --cov=src/elf_visualizer --cov-report=term-missing

# Run specific test module
pytest tests/test_parser.py -v
```

## Common Troubleshooting Guides

### "Tests failing due to missing dependencies"
1. Check `pyproject.toml` for required packages (pydantic, rich, pyelftools)
2. Verify lock files are up-to-date (`pip install -e .[dev]`)
3. Ensure virtual environment is activated

### "Console output not showing correctly"
1. Verify rich console initialization in cli.py
2. Check terminal capabilities and color support
3. Use `console.print()` instead of print() for formatted output

### "Pydantic validation errors"
1. Ensure all required fields have proper type hints
2. Check field constraints in model definitions (e.g., frozen models)
3. Validate data before creating model instances

## Best Practices
- **Lazy Loading**: Load section content only when `--dump` flag is used
- **Immutable Models**: Use `model_config = ConfigDict(frozen=True)` for Pydantic models
- **Error Messages**: Provide clear, actionable error messages with rich formatting
- **Hex Dump Limit**: Restrict `--dump` to sections ≤ 256 bytes for UI responsiveness

## Code Style Tools
- **Linting**: ruff for import sorting and basic syntax checks
- **Type Checking**: mypy for static type analysis  
- **Pre-commit**: Consider adding hooks for automated quality checks

## Performance Considerations
- Cache parsed ELF files when possible
- Use sets/dicts to deduplicate sections
- Implement lazy loading for expensive operations
- Limit hex dump output size to maintain responsive UI

## Future Enhancements (Track in Skills)
- Add `--json` flag for structured data export
- Integrate with disassembly tools like capstone
- Implement interactive TUI using textual or urwid
- Add symbol table lookup and cross-referencing
- Support for program header (segment) visualization

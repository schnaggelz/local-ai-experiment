# Elf Visualizer Plan

## 1. Overview
A command‑line **ELF visualizer** that reads an ELF binary and presents its sections (`SectionInfo`), including:
* Section name, type (`SHT_*`), virtual address (`sh_addr`), size, file offset, protection flags.
* Optional raw content dump (hex view) for small sections.

The tool should be **robust**, **well‑typed**, **tested**, and follow Python best practices (`pytest`, `Pydantic v2`, `rich` UI).

---

## 2. Project Layout
```
examples/elf_analyzer/
├─ pyproject.toml          # Dependency management & scripts entry points
├─ src/
│   └─ elf_visualizer/
│       ├─ __init__.py
│       ├─ models.py               # Pydantic data structures
│       ├─ parser.py               # ELF parsing logic (pyelftools)
│       ├─ visualizer.py           # Console rendering (rich tables, hex dumps)
│       ├─ cli.py                  # Argument parsing & entry point
│       └─ exceptions.py           # Custom error hierarchy
├─ tests/
│   ├─ __init__.py
│   ├─ test_parser.py            # Unit tests for parser module
│   ├─ test_visualizer.py        # UI rendering tests (snapshot / console capture)
│   └─ conftest.py               # Shared fixtures, e.g., sample ELF binaries
└─ README.md                  # User & developer documentation
```

---

## 3. Technical Requirements

| Requirement | Implementation Details |
|-------------|------------------------|
| **ELF parsing** | Use `pyelftools` (pure‑Python). Parse `/path/to/elf`. Handle invalid files gracefully with a custom `ELFParseError`. |
| **Data modelling** | Pydantic v2 models: <br> • `SectionInfo` – all header fields + optional lazy `content`. <br> • `InputFile` – holds path and list of sections. |
| **CLI** | Accept positional `path` argument; `--dump` flag for hex‑view (only for ≤256 B to keep UI tidy). Use `argparse`; expose entry point via `console_scripts`. |
| **Console output** | • Table: idx, Section Name, Type, VADDR (`hex()`), Size, Flags.<br>• Optional hex dump with 16‑byte rows using `rich.syntax` for colour‑blind safety. |
| **Error handling** | Custom exceptions (`ELFParseError`, `ELFSectionError`) and descriptive messages printed via `rich.Console`. Never use bare `except:`. |
| **Testing** | • Unit tests for parser (valid ELF, edge cases).<br>• Snapshot tests for visualizer output (via `pytest‑rich`).<br>• Integration test running the CLI on known binaries. |
| **Dependencies** | `Pydantic ~=2.7`, `rich >=13.0`, `pyelftools >=0.30`. All listed in `pyproject.toml` with appropriate dev‑deps (`pytest`, `pytest‑cov`). |
| **Code quality** | • Type hints throughout (`from __future__ import annotations`).<br>• Functions ≤ 5 lines where possible; helpers for complex logic.<br>• Every public function documented with `Args`, `Returns`, and `Raises`. |
| **Efficiency** | Lazy loading of section content (read only when `--dump` used or requested). Use sets / dicts to deduplicate sections if needed. |
| **Interactive TUI** | Use `textual` framework for a reactive terminal UI. Implement navigation screens: Sections, Symbols, Relocations, Hex Viewer. Support keyboard shortcuts. |

---

## 4. Implementation Phases

### Phase 1 – Foundation
- [ ] Create `pyproject.toml` with Poetry/uv, lock files.
- [ ] Scaffold `src/` and top‑level modules (`exceptions.py`, `models.py`).
- [ ] Write **basic Pydantic models** (`SectionInfo`, `InputFile`) with field validation.
- [ ] Add a simple CLI stub that prints help text.

### Phase 2 – ELF Parsing
- [ ] Install `pyelftools`.
- [ ] Implement `parse_elf()` in `parser.py`:
  * Iterate over section headers.<br>
  * Populate `SectionInfo` fields (name, type, sh_addr, sh_size, sh_offset, flags).<br>
  * Return an `InputFile` instance.
- [ ] Add custom exception `ELFParseError`.
- [ ] Write unit tests covering valid ELF and error paths.

### Phase 3 – Visualisation
- [ ] Build `render_section_table()` using `rich.Table`.<br>
  * Columns: Index, Section Name, Type, VADDR (hex), Size, Flags.<br>
  * Respect colour‑blind themes (`rich.theme`).<br>
- [ ] Implement lazy content loading and `dump_content()` for `--dump` flag:<br>
  * Show hex view only when size ≤ 256 B (or a configurable limit).<br>
  * Use `rich.syntax("hexdump", "hexdump")` or custom formatting.<br>
- [ ] Add helper functions (`format_flags`) to produce concise flag strings.

### Phase 4 – CLI Integration
- [ ] Create `cli.py`:
  * Parse arguments (`path`, `--dump`).<br>
  * Instantiate `console = Console()`.<br>
  * Call parser, catch `ELFParseError`, display with colour.<br>
  * Delegate rendering based on flags.<br>
- [ ] Register console script entry point in `pyproject.toml` → `elf_visualizer`.

### Phase 5 – Testing & Quality
- [ ] Write comprehensive test suite:
  * Fixtures for sample ELF files (`tests/data/`). Use real binaries (e.g., `/bin/ls`, the tool itself) and synthetic ELF if needed.<br>
  * Unit tests for parser, visualizer, and exception scenarios.<br>
  * Snapshot or record console output to avoid flaky UI tests.<br>
- [ ] Run `pytest` with coverage; enforce a minimum coverage threshold (≥ 80 %).
- [ ] Apply code‑style checks (`ruff`, `mypy`) via pre‑commit hooks if desired.

### Phase 6 – Documentation & Polish
- [ ] Populate `README.md`:
  * Installation instructions (poetry install, CLI usage).<br>
  * Example output screenshots.<br>
  * Contribution guidelines and testing instructions.<br>
- [ ] Add docstrings to every public function (`Args`, `Returns`, `Raises`).
- [ ] Consider optional enhancements:
  * Support for `--json` flag – emit parsed data as JSON.
  * Integration with disassembly tools (e.g., `capstone`) for symbolic views.
  * Interactive TUI using `textual` or `urwid`.

---

## 5. Milestones & Deliverables

| Milestone | Expected Outcome |
|-----------|-------------------|
| **M1 – Setup** | Complete project scaffolding, lock file generated, basic CLI runs and prints help. |
| **M2 – Parser Core** | `parse_elf()` correctly extracts all sections for a known ELF; unit tests pass. |
| **M3 – Visualizer** | Console table displays section metadata; `--dump` flag produces readable hex dumps (size‑limited). |
| **M4 – CLI & Errors** | Full CLI functionality, graceful error messages, registered entry point `elf_visualizer`. |
| **M5 – Tests & CI** | All tests pass (> 80 % coverage), test suite can be run with a single command (`pytest`). |
| **M6 – Docs** | Polished `README.md` with usage examples and developer notes; code documentation complete. |

---

## 6. Risk Mitigation
- **Parsing Failures**: Catch parsing exceptions early, provide clear messages, avoid crashes on malformed files.
- **Large Section Dumps**: Limit `--dump` to small sections (configurable) to keep UI responsive.
- **Dependency Availability**: Pin `pyelftools` version; ensure Poetry resolves transitive dependencies correctly.
- **Testing Environment**: Include pre‑built ELF samples in the repo to guarantee consistent test behavior across platforms.

---

## 7. Future Enhancements
1. **Enhanced metadata extraction** – Extract additional ELF metadata including symbol tables, relocation entries, dynamic section information, and version definitions for deeper analysis:
   * Implement `SymbolInfo` model with name, value, size, binding, visibility, and section index.
   * Add `RelocationEntry` model capturing offset, info, addend, and target symbol reference.
   * Parse `.dynsym` and `.symtab` sections using pyelftools' SymbolTableSection.
   * Extract dynamic section entries (`.dynsym`, `.dynstr`, `.hash`, `.gnu_version`, `.gnu_version_r`) for runtime linking analysis.
   * Implement `VersionDefinition` model for version symbols in ELF64.
   * Add lazy loading of symbol tables to maintain performance (load only when requested).
2. Add `--json` output for integration with other tools.
3. Support for program header (segment) visualization.
4. Interactive mode with navigation over sections (TUI).
5. Symbol table lookup and cross‑reference display.
6. Disassembly of `.text` sections using `capstone`.

---

## 8. Enhanced Metadata Extraction Implementation

### Overview
This section implements Future Enhancement #1 from the original plan, adding comprehensive ELF metadata extraction including symbol tables, relocation entries, dynamic sections, and version definitions while maintaining backward compatibility and performance through lazy loading.

### Technical Requirements

| Component | Details |
|-----------|---------|
| **Symbol Tables** | Parse `.symtab` (static symbols) and `.dynsym` (dynamic symbols) using pyelftools' SymbolTableSection. Extract name, value, size, binding, visibility, section index. Lazy loading - only parse when requested. |
| **Relocation Entries** | Parse relocation sections (`.rel`, `.rela`, `.plt_rel`) for both static and dynamic relocations. Capture offset, info, addend, target symbol reference. Support ELF32/ELF64 variants. |
| **Dynamic Sections** | Extract entries from `.dynsym` (symbol table), `.dynstr` (string table), `.hash` (hash table), `.gnu_version`, `.gnu_version_r` (version definitions). Parse runtime linking metadata. |
| **Version Definitions** | Implement `VersionDefinition` model for ELF64 version symbols in `.gnu_version` and `.gnu_version_r`. Extract version names, hash, and symbol references. |
| **CLI Integration** | Add new flags: `--symbols`, `--relocations`, `--dynamic` to selectively display enhanced metadata. Maintain existing `--dump` flag functionality. |

### Implementation Phases

#### Phase 8.1 - Data Model Extension
- [ ] Extend `models.py`:
  * Add `SymbolInfo` model with fields: name, value, size, binding, visibility, section_index, is_local
  * Add `RelocationEntry` model with fields: offset, info, addend, symbol_index, section_type
  * Add `VersionDefinition` model with fields: version_name, hash, auxiliary_vector, timestamp
  * Update `InputFile` to include optional fields: `symbols`, `relocations`, `dynamic_entries`, `version_definitions`
- [ ] Implement lazy loading patterns using `@property` decorators

#### Phase 8.2 - Parser Enhancement
- [ ] Extend `parser.py`:
  * Add `_parse_symbol_table()` method for `.symtab`/`.dynsym` sections
  * Add `_parse_relocation_section()` method for relocation entries
  * Add `_parse_dynamic_section()` method for dynamic linking metadata
  * Add `_parse_version_definitions()` method for version symbols
  * Implement lazy loading: only parse when corresponding CLI flags are used
- [ ] Add new custom exceptions:
  * `ELFSymbolError` - symbol table parsing errors
  * `ELFRelocationError` - relocation entry parsing errors
  * `ELFDynamicError` - dynamic section parsing errors

#### Phase 8.3 - Visualizer Enhancement
- [ ] Extend `visualizer.py`:
  * Add `render_symbol_table()` method for displaying parsed symbols in formatted table
  * Add `render_relocation_entries()` method for relocation information display
  * Add `render_dynamic_sections()` method for dynamic linking metadata
  * Add `render_version_definitions()` method for version symbol display
- [ ] Implement intelligent formatting:
  * Color-code symbol types (local/global/undefined)
  * Show relocation target references with section names
  * Display version definitions in hierarchical structure

#### Phase 8.4 - CLI Integration
- [ ] Update `cli.py`:
  * Add new command-line arguments: `--symbols`, `--relocations`, `--dynamic`
  * Implement argument validation and mutual exclusivity where appropriate
  * Integrate enhanced metadata rendering based on flags
  * Maintain backward compatibility with existing functionality
- [ ] Update help text and documentation

#### Phase 9 – Interactive TUI Mode
- [ ] Evaluate/framework choice: use `textual` (built on `rich`) for reactive UI components.
- [ ] Scaffold TUI module (`tui.py`, `tui_app.py`, `tui_widgets.py`):
  * Implement a main `TextualApp` with state management (`InputFile`, current navigation context).
  * Navigation sidebar or tabbed interface for Sections, Symbols, Dynamic Info, Versions.
  * `HexViewerWidget`: byte-wise rendering, cross-referencing symbols on hover. 
- [ ] Keyboard shortcuts & commands: 
  * Global keys (`q` quit).
  * Section context: toggle raw hex dump, scroll-through large sections.
  * Section context: toggle raw hex dump, scroll-through large sections.
- [ ] Integrate parser lazy-loading so that heavy metadata (e.g., full `.symtab`) is only populated upon TUI navigation to that specific view.
- [ ] Add styling/theme support (light/dark terminal themes).

### Phase 9.1 – Testing & Validation for TUI
- [ ] Mock-based unit tests for widget behavior and key bindings.
- [ ] End-to-end TUI integration test using `pytest-textual` to simulate user input paths (e.g., load binary, switch views, navigate tables).
- [ ] Ensure no memory leaks with large binaries (>50MB ELF files with massive symbol tables).

### Future Considerations
- [ ] Ensure no memory leaks with large binaries (>50MB ELF files with massive symbol tables).

### Phase 8.5 - Testing & Validation
- [ ] Extend test suite:
  * Add unit tests for symbol table parsing (valid ELF, edge cases)
  * Add unit tests for relocation entry parsing (ELF32/ELF64 variants)
  * Add integration tests for CLI with new flags
  * Add snapshot tests for enhanced visualizer output
- [ ] Create test fixtures:
  * Use `/bin/ls` for symbol table testing
  * Use the tool itself for relocation testing
  * Include synthetic ELF files for comprehensive coverage

### Code Quality Standards

| Requirement | Implementation |
|-------------|----------------|
| **Type Hints** | Add complete type annotations for all new models and methods |
| **Documentation** | Document every public function with Args, Returns, Raises |
| **Error Handling** | Implement specific exception handling for each metadata type |
| **Performance** | Ensure lazy loading prevents performance impact when not needed |
| **Code Organization** | Keep functions ≤5 lines where possible; use helper functions |

### Verification Steps

1. **Symbol Table Testing**:
   - Test with `/bin/ls` (contains static symbols)
   - Verify symbol name, value, size extraction
   - Test lazy loading behavior

2. **Relocation Entry Testing**:
   - Test with the tool itself (ELF binary with relocations)
   - Verify offset, info, addend parsing for both ELF32/ELF64
   - Test different relocation section types (`.rel`, `.rela`)

3. **Dynamic Section Testing**:
   - Parse dynamic linking metadata from known binaries
   - Verify hash table and version definition extraction

4. **CLI Integration Testing**:
   - Test `--symbols` flag with various ELF files
   - Test `--relocations` flag for relocation display
   - Test `--dynamic` flag for dynamic section information
   - Verify backward compatibility (existing CLI usage unchanged)

5. **Performance Validation**:
   - Measure parsing time without enhanced metadata
   - Measure parsing time with lazy loading enabled
   - Ensure no performance degradation in default mode

### Risk Mitigation

- **Parsing Failures**: Catch specific exceptions for each metadata type, provide clear error messages
- **Memory Usage**: Implement streaming parsing for large symbol tables
- **Compatibility**: Maintain existing API and CLI interface unchanged
- **Testing Coverage**: Include real-world ELF binaries in test fixtures

### Dependencies Update

Update `pyproject.toml`:
```toml
dependencies = [
    "pydantic ~=2.7",
    "rich >=13.0", 
    "pyelftools >=0.30",
]
dev-dependencies = [
    "pytest",
    "pytest-cov",
    # Additional testing tools as needed
]
```

### Milestones (Updated)

| Milestone | Expected Outcome |
|-----------|-----------------|
| **M1 – Setup** | Complete project scaffolding, lock file generated, basic CLI runs and prints help. |
| **M2 – Parser Core** | `parse_elf()` correctly extracts all sections for a known ELF; unit tests pass. |
| **M3 – Visualizer** | Console table displays section metadata; `--dump` flag produces readable hex dumps (size‑limited). |
| **M4 – CLI & Errors** | Full CLI functionality, graceful error messages, registered entry point `elf_visualizer`. |
| **M5 – Tests & CI** | All tests pass (> 80 % coverage), test suite can be run with a single command (`pytest`). |
| **M6 – Docs** | Polished `README.md` with usage examples and developer notes; code documentation complete. |
| **M7 – Enhanced Metadata** | Symbol table, relocation entry, and dynamic section parsing implemented; new CLI flags functional; comprehensive test coverage for enhanced features. |
| **M8 – Automated Testing** | C++ generator integrated; end-to-end testing of all ELF features automated via generated binaries. |
| **M9 – Interactive TUI** | Reactive terminal interface fully functional with keyboard navigation and lazy-loading enhanced metadata. Code coverage ">= 80%" maintained across the new module. |

### Future Considerations

1. **JSON Output**: Implement `--json` flag to emit parsed data (including enhanced metadata) as structured JSON
2. **Disassembly Integration**: Plan for capstone integration to disassemble `.text` sections using symbol information
3. **Remote Inspection**: Add an optional server mode or DAP (Debug Adapter Protocol) integration to inspect remotely mounted or streaming ELF binaries.
4. **Cross-references & Symbol Graphs**: Enable interactive graph visualization (using `anywidget` or ASCII/Unicode trees) for cross-reference display and call-graph analysis.

---

**End of Enhanced Metadata Extraction Implementation Plan.**
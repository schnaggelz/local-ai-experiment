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
| **Data modelling** | Pydantic v2 models: <br> • `SectionInfo` – all header fields + optional lazy `content`. <br> • `ElfFile` – holds path and list of sections. |
| **CLI** | Accept positional `path` argument; `--dump` flag for hex‑view (only for ≤256 B to keep UI tidy). Use `argparse`; expose entry point via `console_scripts`. |
| **Console output** | • Table: idx, Section Name, Type, VADDR (`hex()`), Size, Flags.<br>• Optional hex dump with 16‑byte rows using `rich.syntax` for colour‑blind safety. |
| **Error handling** | Custom exceptions (`ELFParseError`, `ELFSectionError`) and descriptive messages printed via `rich.Console`. Never use bare `except:`. |
| **Testing** | • Unit tests for parser (valid ELF, edge cases).<br>• Snapshot tests for visualizer output (via `pytest‑rich`).<br>• Integration test running the CLI on known binaries. |
| **Dependencies** | `Pydantic ~=2.7`, `rich >=13.0`, `pyelftools >=0.30`. All listed in `pyproject.toml` with appropriate dev‑deps (`pytest`, `pytest‑cov`). |
| **Code quality** | • Type hints throughout (`from __future__ import annotations`).<br>• Functions ≤ 5 lines where possible; helpers for complex logic.<br>• Every public function documented with `Args`, `Returns`, and `Raises`. |
| **Efficiency** | Lazy loading of section content (read only when `--dump` used or requested). Use sets / dicts to deduplicate sections if needed. |

---

## 4. Implementation Phases

### Phase 1 – Foundation
- [ ] Create `pyproject.toml` with Poetry/uv, lock files.
- [ ] Scaffold `src/` and top‑level modules (`exceptions.py`, `models.py`).
- [ ] Write **basic Pydantic models** (`SectionInfo`, `ElfFile`) with field validation.
- [ ] Add a simple CLI stub that prints help text.

### Phase 2 – ELF Parsing
- [ ] Install `pyelftools`.
- [ ] Implement `parse_elf()` in `parser.py`:
  * Iterate over section headers.<br>
  * Populate `SectionInfo` fields (name, type, sh_addr, sh_size, sh_offset, flags).<br>
  * Return an `ElfFile` instance.
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
1. Add `--json` output for integration with other tools.
2. Support for program header (segment) visualization.
3. Interactive mode with navigation over sections (TUI).
4. Symbol table lookup and cross‑reference display.
5. Disassembly of `.text` sections using `capstone`.

---

**End of Plan.**
This document can be kept in the repository as a living roadmap; each completed phase should update its status accordingly.
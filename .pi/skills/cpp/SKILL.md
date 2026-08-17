---
name: cpp
description: >
  C++17 dev rules. Bazel build, GTest/GMock testing, memory safety, tooling. 
  Use when writing, reviewing or debugging C++.
---

# C++ Development Skill

## Language Target

Default **C++17** enforced via `.bazelrc` (`--cxxopt=-std=c++17`).
Avoid legacy C casts, raw owning pointers, manual memory mgmt. Use modern STL wrappers only.

```cpp
// PREFER: smart pointers over raw owning memory
std::unique_ptr<T> own = std::make_unique<T>();
std::shared_ptr<T> shared = std::make_shared<T>();

// PREFER: const ref or view-like types for read-only params
void f(const std::vector<int>& data); // pre-C++20. works everywhere.
void g(std::string_view text);        // c++17 zero-copy string view.

// AVOID: naked new/delete
T* bad = new T;  // leak risk. delete it yourself? never again.
```

### C++17 Core Features Checklist

Feature | Use case
---|---
structured bindings | `auto [it, ok] = map.insert({k,v})` -- unpack pair/tuple
`std::optional` / `std::variant` / `std::any` | return value-or-nothing without magic codes or raw ptrs
`if constexpr` | compile-time branch. replaces heavy SFINAE in most cases
selection init | `if (auto it = m.find(k); it != m.end()) {}` -- scope-bounds var
`std::filesystem` | portably handle paths, dirs, file attrs no boost needed
`[[nodiscard]]` / `[[fallthrough]]` | silence compiler on purpose. mark unsafe discards
inline vars | define constexpr/static vars in headers w/o ODR violation

## Naming & Includes

```cpp
class PascalCase;              // types, structs
void snake_or_camel();         // functions/vars -- pick one per project. stick to it.
static constexpr int ALL_CAPS = 42; // constants
```

Include order: **self -> project -> third-party -> system**.

Guard every header using macros (`#ifndef` / `define`). Naming convention: ALL_CAPS. Format is COMPONENT_FILE_HPP.
Example:
```cpp
#ifndef MYCOMPONENT_UTILS_HPP  
#define MYCOMPONENT_UTILS_HPP 
#endif // MYCOMPONENT_UTILS_HPP
```

Forward-declare instead of `#include` when possible. Public headers self-contained only. No umbrella includes.

## Memory & RAII

Resources wrapped in owners. No manual cleanup.

- Files, locks, sockets -- RAII wrappers only
- Mutexes -> `std::lock_guard`, `std::unique_lock`
- Rule of Five: custom resource managers must define dtor + copy/move or delete copies manually
- Move-only types? delete copy ctor/assign explicitly

```cpp
class NoCopy
{
    NoCopy(const NoCopy&) = delete;
    NoCopy& operator=(const NoCopy&) = delete;
};
```

## Templates & Generics

C++17 means no concepts keyword. Use SFINAE (`std::enable_if_t`) or tag dispatch for constraints. Prefer `auto` return deduction when clear. Explicit CTAD guides where ambiguous.

```cpp
// constrain template without c++20 concepts:
template<typename T, typename = std::enable_if_t<std::is_move_assignable_v<T>>>
void sort(Container<T>& c);
```

## Architecture: DI + Interfacing

Inject dependencies via interface pointers. Heavy backends -- mock in test, real in prod. Never tight-couple implementation to production backend at compile time in library code.

```cpp
struct IFoo { virtual ~IFoo() = default; virtual int op(int) = 0; };
// production: RealFoo : public IFoo
// test      : MockFoo : public IFoo + MOCK_METHOD(...);
```

## Build System: Bazel

This repo uses **Bazel** exclusively. C++ targets via `rules_cc`. Deps managed in `MODULE.bazel` (bzlmod).

### Target Types

- `cc_library` -- reusable code block. set visibility explicit if narrow.
- `cc_binary` -- executable entry point. dep on libs only.
- `cc_test` -- unit tests. link against `@googletest//:gtest_main`.

One BUILD snippet covers patterns. Copy paste adapt names.

```starlark
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_binary", "cc_test")

cc_library(
    name = "libname",
    srcs = glob(["src/**/*.cpp"]),                # or explicit list if small
    hdrs = glob(["include/**/*.hpp"]),
    includes = ["include"],                       # search path for headers
    visibility = ["//visibility:public"],         # restrict when needed
)

cc_binary(
    name = "binaryname",
    srcs = ["src/main.cpp"],
    deps = [":libname"],
)

cc_test(
    name = "testname",
    srcs = glob(["test/test_*.cpp"]),
    deps = [":libname", "@googletest//:gtest_main"],
)
```

External deps: add via `bazel_dep()` in `MODULE.bazel`. Use `git_override` for non-BCR modules. Pin commit hash.

### Build Profiles (.bazelrc)

Profile | Flags | When  
---|---|---
*(default)* | opt mode, `-O2`, strict warnings (`-Wall -Wextra -Wpedantic -Werror`) | build + ship
`:debug` | `-O0 -g3` | step in debugger  
`test` | ASan + UBSan auto-injected via copts/linkopts | run tests

### Core Commands

```bash
bazel build //...:all                           # compile everything
bazel test //...:all                            # run all tests (sanitizers on)
bazel test //path/to:target --test_output=all   # verbose logs
bazel build --config=debug :t                   # debug build
```

### Source Layout Per Example

```
examples/<project>/
|-- BUILD.bazel          # cc_library, cc_test, cc_binary
|-- include/             # public headers
|   `-- <pkg>/*.hpp
|-- src/                 # implementation .cpp
`-- test/                # gtest sources
    `-- test_*.cpp
    `-- bench/           # optional microbench targets
    `-- bench_main.cpp
```

## Testing: GTest + GMock

GTest for unit assertions. GMock for dependency isolation.

### Assertions

Macro | Behavior  
---|---
`EXPECT_*` | non-fatal. test continues after fail.
`ASSERT_*` | fatal. aborts current test immediately.
`EXPECT_NEAR(a, b, eps)` | float compare w/ tolerance.

### Parameterized Tests

```cpp
TEST_P(IntTest, IsOdd) { EXPECT_TRUE(GetParam() % 2); }
INSTANTIATE_TEST_SUITE_P(GoodName, IntTest, testing::Values(1, 3, 5));
```

### GMock Patterns

Define interface. Derive mock with `MOCK_METHOD`. Set expectations via `EXPECT_CALL`.

```cpp
// interface
struct IFoo { virtual ~IFoo() = default; virtual int op(int) = 0; };

// mock
class MockFoo : public IFoo {
public:
    MOCK_METHOD(int, op, (int x), (override));
};

TEST(MyTest, UsesMock) {
    MockFoo m;
    EXPECT_CALL(m, op(testing::Eq(42)))          // expect one call with arg 42
        .WillOnce(testing::Return(-1));           // return -1 when called
}
```

Expectation quickref:
- `EXPECT_CALL(mock, method(matcher))` -- register expected invocation
- `.Times(at_least(1)), .Times(any_number())` -- cardinality control  
- `testing::Invoke(fn)` -- custom action on call

Mock policy:
- **NiceMock\<T\>** -- silent on unexpected calls (quiet)
- **NaggyMock\<T\>** -- warn loudly (default)
- **StrictMock\<T\>** -- fail immediately (tightest check)

## Error Handling Strategy

Custom exception hierarchy rooted at `std::runtime_error`. Mark truly non-throwing functions `noexcept`. Prefer strong guarantee: operation fully succeeds or leaves state untouched.

```cpp
struct AppError : std::runtime_error { using runtime_error::runtime_error; };
struct ParseError : AppError { using AppError::AppError; };
```

## Performance Rules

- Prefer `-O2` over `-O3`. Better I-cache behavior usually same wall clock time.
- `reserve()` containers before bulk push. Avoid reallocation loop.
- Pass views (`string_view`) or const refs not copies when read-only.
- CRTP or template polymorphism in hot path. Skip vtable overhead if type known at compile time.
- Profile first. Optimize hotspot only. Not assumptions.

## Platform Notes

Linux primary target. Use `#ifdef` sparingly. Abstract platform diffs behind interfaces, not preprocessor spaghetti. Stick POSIX over Linux-specific syscalls when possible. Endianness aware in binary protocols.

## Tooling Quick Ref

```bash
clang-format -i --style=file *.cpp *.hpp           # auto-format (uses .clang-format, 120 col)
bazel build //:refresh_compile_commands            # generate compile_commands.json for IDE/LSP
valgrind --leak-check=full bazel-bin/pkg/target    # requires debug profile (-O0 -g3)
```

## Checklist -- Before Commit

- [ ] no naked `new`/`delete`. RAII wraps everything.
- [ ] includes ordered: self -> project -> external -> system
- [ ] headers include only what used. forward-declare else.
- [ ] dependency injected via interface mockable for tests.
- [ ] GTest + GMock patterns matched above.
- [ ] `bazel build` passes clean. `bazel test` green.
- [ ] clang-format applied. no format drift.

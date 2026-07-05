# C++ Development Skills for Logging Framework

This document outlines the professional competencies, technical skills, and best practices required for software engineers working with modern **C++17**, the **GoogleTest (GTest) / GoogleMock** framework, and the **Bazel** build system. It serves as a benchmark for engineering excellence, self-assessment, and training.

## Engineering Best Practices

### Continuous Integration & Workflow Automation
* **Automated Testing Pipelines:** Writing declarative GitHub Actions, GitLab CI, or Jenkins steps mapping directly to `bazel test //...` execution targets.
* **Remote Build Caching:** Configuring shared remote cache layers to speed up execution feedback loops across distributed continuous integration nodes and developers' local environments.

### Quality Assurance & Runtime Diagnostics
* **Sanitizer Injection:** Injecting runtime diagnostic tools during test execution via `bazel test --copts=-fsanitize=address --linkopts=-fsanitize=address` to capture Memory Leaks, Buffer Overflows (ASan), and Undefined Behavior (UBSan) ahead of production releases.
* **Compilation Strictness:** Mandating highly-pedantic tracking flags (`-Wall -Wextra -Werror -Wpedantic`) at the `.bazelrc` root to catch anti-patterns before code review cycles.

### Clean Code & Refactoring Paradigms
* **Decoupled Architecture:** Using Dependency Injection patterns alongside GoogleMock interfaces to ensure codebases remain thoroughly decoupled, testable, and maintainable.
* **Modern Resource Ownership:** Rejecting explicit memory instructions (`new`, `delete`) in favor of RAII semantics (`std::unique_ptr`, `std::shared_ptr`) combined with C++17 library optimizations.

## Core C++17 Language & Standard Library

### Language Features & Syntax Extensions
* **Structured Bindings:** Ability to unpack tuples, pairs, arrays, or structs cleanly (`auto [x, y, z] = expr;`), improving readability and eliminating boilerplate.
* **Compile-Time Control Flow (`if constexpr`):** Utilizing compile-time conditional branching to simplify template metaprogramming, replacing complex SFINAE (`std::enable_if_t`) structures.
* **Fold Expressions:** Writing concise variadic templates using unary or binary fold expressions over operators (e.g., `return (... + args);`).
* **Selection Statements with Initializers:** Declaring variables within the scope of `if` and `switch` blocks (`if (auto it = map.find(key); it != map.end()) { ... }`) to restrict variable lifetime and improve safety.
* **Inline Variables:** Specifying `inline` for non-functional variables to define external linkable variables directly in header files without causing multiple-definition violations.
* **Attributes:** Explicit usage of `[[nodiscard]]` to prevent ignored return values, `[[fallthrough]]` for intentional switch case drops, and `[[maybe_unused]]` to suppress compiler warnings cleanly.

### Standard Library (STL) Additions & Enhancements
* **Vocabulary Types:**
    * `std::optional`: Managing optional return paths securely without null pointers or magic error values.
    * `std::variant`: Safe, type-efficient alternative to raw unions with compile-time type-safety visiting (`std::visit`).
    * `std::any`: Type-safe container capable of holding single values of any copy-constructible type.
* **String Performance Enhancements:** Broad adoption of `std::string_view` for zero-allocation, non-owning reference substrings to optimize read-only string APIs.
* **Filesystem Library (`std::filesystem`):** Platform-independent manipulation of paths, directories, and file metadata without external libraries (like Boost).
* **Parallel STL Algorithms:** Enhancing standard algorithms (`std::sort`, `std::transform`) by passing execution policies (`std::execution::par`, `std::execution::seq`) to leverage multi-core processors.
* **Utility & Utility Containers:** Working with smart pointer updates (`std::shared_ptr` support for arrays), `std::byte` for strongly-typed raw memory manipulation, and math enhancements (e.g., `std::clamp`, `std::gcd`).

## Unit Testing & Mocking via GoogleTest (GTest)

### Foundational Unit Testing
* **Assertions Hierarchy:** Differentiating between fatal failures (`ASSERT_EQ`, `ASSERT_TRUE`, `ASSERT_THROW`) which abort the execution of the current test function, and non-fatal failures (`EXPECT_EQ`, `EXPECT_NE`, `EXPECT_THAT`) which log failures but permit the test suite to proceed.
* **Test Fixtures (`testing::Test`):** Implementing reusable environments using `SetUp()` and `TearDown()` to manage heavy shared states or isolate environments per execution block.
* **Floating-Point Testing:** Applying `EXPECT_NEAR` and `EXPECT_FLOAT_EQ` to avoid false failures due to precision loss in floating-point mathematics.

### Advanced Testing Architectures
* **Value-Parameterized Tests (`testing::TestWithParam<T>`):** Running identical assertions across broad, distinct datasets via `INSTANTIATE_TEST_SUITE_P` to eliminate test code duplication.
* **Type-Parameterized Tests (`testing::Types<T>`):** Verifying API or algorithmic compliance across multiple underlying implementation types (e.g., ensuring a queue implementation functions identically for `int`, `std::string`, and custom structs).
* **Custom Matchers:** Leveraging `testing::Matcher` and macros like `MATCHER_P` to write readable, expressive assertions tailored to internal domain objects.

### Isolation and Mocking with GoogleMock (GMock)
* **Mock Generation:** Defining robust mock objects using `MOCK_METHOD` to simulate complex or concrete dependencies (e.g., Network Clients, Hardware Interfaces, Database Connections).
* **Expectation Framing (`EXPECT_CALL`):** Confidently declaring interactions:
    * **Cardinalities:** `Times(AtLeast(1))`, `Times(0)`, `Times(Exactly(n))`.
    * **Matchers:** `Eq`, `Ne`, `Field`, `Property`, `ElementsAre`, `UnorderedElementsAre`.
    * **Actions:** `Return(val)`, `Invoke(callable)`, `Assign(&var, val)`, `Throw(exception)`.
* **Mock Policy Management:** Distinguishing and managing strictness classes:
    * `testing::NiceMock`: Ignores uninteresting/unregistered calls silently.
    * `testing::NaggyMock` (Default): Warns loudly about unregistered calls.
    * `testing::StrictMock`: Fails immediately upon encountering an unregistered call, enabling tight control over implementation details.

## The Bazel Build System

### Workspace Architecture & Target Definitions
* **Structural Understanding:** Practical separation of concerns between workspace-level configurations (`WORKSPACE` or `MODULE.bazel`), packages (`BUILD` files), and labels (`//path/to/package:target_name`).
* **Native C++ Rules Engine:** Mastering basic rules to engineer predictable, sandboxed build graphs:
    * `cc_library`: Designing atomic, modular, and reusable blocks with clear visibility constraints (`visibility = ["//visibility:public"]`).
    * `cc_binary`: Producing standalone executable entry points.
    * `cc_test`: Combining source definitions directly with GTest dependencies (`deps = ["@com_google_googletest//:gtest_main"]`).

### Target Dependencies & Configuration Mechanics
* **Header Inclusion Controls:** Managing physical layouts via `hdrs` (public interfaces) and `srcs` (private implementation details), paired with strict structural directory control via `includes` attributes.
* **External Dependency Integration:** Consuming external libraries safely via HTTP archives (`http_archive`) within workspace configs or defining dependencies using Bazel Modules (`MODULE.bazel` for Bzlmod compatibility).
* **Conditional Configurations (`select`):** Injecting platform-specific compile flags, sources, or optimization tiers gracefully depending on user/architecture switches (`config_setting`).

### Enterprise-Scale Build Optimization
* **Sandboxing & Hermeticity:** Debugging build inputs/outputs strictly within virtual barriers to guarantee builds are deterministic and free from environment leaks.
* **Query & Graph Profiling:** Exercising `bazel query`, `cquery`, and `aquery` commands to troubleshoot graph performance bottlenecks, identify dependency inflation, or audit configurations.
* **Action Command Optimizations:** Mastering `copts`, `linkopts`, `defines`, and global flag management via custom, checked-in `.bazelrc` execution profiles.

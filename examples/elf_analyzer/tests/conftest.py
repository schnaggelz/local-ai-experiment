import pytest
import subprocess
import os

@pytest.fixture(scope="session", autouse=True)
def generate_test_binaries():
    """Ensures test binaries are built before running tests."""
    builder_path = os.path.join(os.path.dirname(__file__), "generator/build_binaries.py")
    if os.path.exists(builder_path):
        subprocess.run(["python3", builder_path], check=True)
    else:
        pytest.fail(f"Binary generator script not found at {builder_path}")

@pytest.fixture
def dynamic_elf():
    """Fixture for a standard dynamic ELF binary."""
    return os.path.abspath("tests/generator/binaries/dynamic_bin")

@pytest.fixture
def static_elf():
    """Fixture for a statically linked ELF binary."""
    return os.path.abspath("tests/generator/binaries/static_bin")

@pytest.fixture
def shared_lib_elf():
    """Fixture for a shared library (.so) file."""
    return os.path.abspath("tests/generator/binaries/libtest.so")

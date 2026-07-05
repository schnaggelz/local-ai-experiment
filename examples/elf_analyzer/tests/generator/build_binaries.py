import subprocess
import os
import sys

def build(source_file, output_name, extra_flags=None):
    if extra_flags is None:
        extra_flags = []
    
    cmd = ["g++", source_file, "-o", output_name] + extra_flags
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully built {output_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build {output_name}: {e}")
        sys.exit(1)

def main():
    binaries_dir = os.path.join(os.path.dirname(__file__), "binaries")
    os.makedirs(binaries_dir, exist_ok=True)
    
    source_file = os.path.join(os.path.dirname(__file__), "gen_elf.cpp")
    
    # 1. Simple dynamic binary
    build(source_file, os.path.join(binaries_dir, "dynamic_bin"))
    
    # 2. Static binary
    build(source_file, os.path.join(binaries_dir, "static_bin"), ["-static"])

    # 3. Shared library
    build(source_file, os.path.join(binaries_dir, "libtest.so"), ["-shared", "-fPIC"])

if __name__ == "__main__":
    main()

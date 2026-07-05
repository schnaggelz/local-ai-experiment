#include <iostream>
#include <vector>

// A simple C++ function that will be present in the symbol table.
void target_function() {
    std::cout << "Executing target function..." << std::endl;
}

int main(int argc, char** argv) {
    // This binary can be extended with more complex logic if needed.
    std::cout << "ELF Generator test binary running." << std::endl;
    target_function();
    return 0;
}

#include <pybind11/pybind11.h>

namespace py = pybind11;

// function to test the connection
int add(int a, int b) {
    return a + b;
}

// Expose C++ functions to Python
PYBIND11_MODULE(diff_core, m) {
    m.doc() = "C++ core for Diff Tool";
    m.def("add", &add, "Add two integers");
}

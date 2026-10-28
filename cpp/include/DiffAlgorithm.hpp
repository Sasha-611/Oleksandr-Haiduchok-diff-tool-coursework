#pragma once

#include <string>
#include <vector>

// Абстрактний клас для алгоритмів порівняння
class DiffAlgorithm {
public:
    virtual ~DiffAlgorithm() = default;

    // Метод порівняння двох послідовностей рядків
    virtual std::vector<std::string> compare(
        const std::vector<std::string>& original,
        const std::vector<std::string>& modified
    ) const = 0;
}; #pragma once

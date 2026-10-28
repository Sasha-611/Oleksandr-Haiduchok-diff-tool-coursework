
#pragma once

#include <string>
#include <vector>

// Base class for comparison algorithms
class DiffAlgorithm {
public:
    virtual ~DiffAlgorithm() = default;

    // Compares two sets of lines
    virtual std::vector<std::string> compare(
        const std::vector<std::string>& original,
        const std::vector<std::string>& modified
    ) const = 0;
};

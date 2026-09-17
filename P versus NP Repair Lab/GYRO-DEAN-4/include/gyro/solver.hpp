#pragma once
#include "gyro/state.hpp"
#include "gyro/certificate.hpp"
#include <cstddef>
#include <unordered_map>
#include <vector>

namespace gyro {

class Solver {
public:
    explicit Solver(const BitGraph& graph);

    SolveResult find_one(std::size_t q);
    std::vector<std::vector<std::size_t>> find_up_to_four(std::size_t q, std::size_t capacity);
    bool verify(const std::vector<std::size_t>& cohort, std::size_t q, std::size_t capacity) const;

    const CertificateLedger& ledger() const { return ledger_; }

private:
    const BitGraph& graph_;
    std::unordered_map<std::string, SolveResult> memo_;
    CertificateLedger ledger_;

    SolveResult gyro(State state);
    bool max_repair(State& state);
    bool q_core_repair(State& state);
    std::size_t choose_pivot(const State& state) const;
    SolveResult branch(State state, std::size_t pivot);
    SolveResult find_with_forbidden(std::size_t q, const std::vector<std::size_t>& forbidden);
};

}

from functools import lru_cache
import json


def parity(w: int) -> int:
    return w.bit_count() & 1


def min_coordinate_depth(k: int) -> int:
    worlds = tuple(range(1 << k))

    @lru_cache(None)
    def solve(ws: tuple[int, ...], remaining: tuple[int, ...]) -> int:
        if len({parity(w) for w in ws}) <= 1:
            return 0
        best = 10**9
        for pos, i in enumerate(remaining):
            rem = remaining[:pos] + remaining[pos + 1:]
            parts = (tuple(w for w in ws if ((w >> i) & 1) == 0),
                     tuple(w for w in ws if ((w >> i) & 1) == 1))
            worst = max(solve(part, rem) for part in parts if part)
            best = min(best, 1 + worst)
        return best

    return solve(worlds, tuple(range(k)))


def main() -> None:
    rows = []
    for k in range(1, 9):
        rows.append({
            "support_size": k,
            "basis_coordinate_min_worst_case_depth": min_coordinate_depth(k),
            "affine_predicate_depth": 1,
        })

    print(json.dumps({
        "experiment": "DF-PNP-01",
        "rows": rows,
        "interpretation": "For parity-aligned protected decisions, basis-only query depth equals affine support size, while admitting the exact affine predicate gives depth one.",
        "claim_ceiling": "Finite exhaustive calibration through support size 8; the general statement is proved separately. No SAT runtime or P-vs-NP conclusion follows."
    }, indent=2))


if __name__ == "__main__":
    main()

"""Run the stored explicit-table example without network access."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from stabilizer_adaptive import adaptive_stabilizers
from stabilizer_matched import anchor_control


def main():
    points = dict(zip([0, 1, 6, 7, 8, 10, 11, 12, 13, 15],
                      [0, 1, 1, 0, 1, 0, 0, 0, 0, 1]))
    result = adaptive_stabilizers(points, 4)
    if result != anchor_control(points, 4):
        raise RuntimeError("The adaptive result disagrees with the control.")
    print(json.dumps({"project": "ChatGPT and Conscience",
                      "input_points": points, "result": result}, indent=2))


if __name__ == "__main__":
    main()

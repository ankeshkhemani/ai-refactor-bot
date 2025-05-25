import asyncio
import sys
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
sys.path.append(src_path)

from core.integrated_scanner import analyze_code_quality


async def test_scanner():
    # Read the test file
    with open("test_file.py", "r") as f:
        code = f.read()

    # Configuration with thresholds
    config = {
        "complexity_threshold": 5,  # Will flag functions with complexity > 5
        "maintainability_threshold": 50,  # Will flag functions with MI < 50
    }

    # Run analysis
    results = analyze_code_quality(code=code, file_path="test_file.py", config=config)

    # Print results
    print("\n=== Analysis Results ===")
    print(f"\nFile: {results['file']}")

    print("\nComplexity Analysis:")
    for func, metrics_list in results["complexity"].items():
        for metrics in metrics_list:
            print(
                f"- {func}: complexity {metrics['complexity']}, rank {metrics['rank']}"
            )

    print("\nMaintainability Analysis:")
    for func, metrics_list in results["maintainability"].items():
        for metrics in metrics_list:
            if isinstance(metrics, dict) and "mi" in metrics and "rank" in metrics:
                print(f"- {func}: score {metrics['mi']:.2f}, rank {metrics['rank']}")

    print("\nStyle Issues:")
    for issue in results["style"]:
        print(f"- {issue}")

    print("\nSuggestions:")
    for suggestion in results["suggestions"]:
        print(f"- {suggestion}")


if __name__ == "__main__":
    asyncio.run(test_scanner())

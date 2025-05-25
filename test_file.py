import os
import sys
import time
from typing import Dict, List


def complex_function(data: List[Dict]) -> None:
    """A function with high complexity."""
    result = []
    for item in data:
        if item.get("type") == "A":
            for sub_item in item.get("items", []):
                if sub_item.get("status") == "active":
                    for value in sub_item.get("values", []):
                        if value > 100:
                            result.append(
                                {"id": item.get("id"), "value": value, "status": "high"}
                            )
    return result


def unused_variable():
    """Function with unused variables."""
    x = 10
    y = 20
    print("Hello")
    return x


if __name__ == "__main__":
    complex_function([])
    unused_variable()

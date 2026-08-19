#!/usr/bin/env python3
"""Verify the runtime dependencies needed to render diagrams: the `diagrams`
Python package and the Graphviz `dot` binary. Prints a plain-text OK or a
specific remediation command and exits non-zero so the calling skill can act
on the failure without parsing prose.
"""
import platform
import shutil
import sys


def main() -> int:
    problems = []

    try:
        import diagrams  # noqa: F401
    except ImportError:
        problems.append("Missing Python package `diagrams`. Fix: pip3 install diagrams")

    try:
        import PIL  # noqa: F401
    except ImportError:
        problems.append(
            "Missing Python package `Pillow` (needed for diagrams with a legend). "
            "Fix: pip3 install Pillow"
        )

    if shutil.which("dot") is None:
        system = platform.system()
        if system == "Darwin":
            problems.append("Missing Graphviz `dot` binary. Fix: brew install graphviz")
        elif system == "Linux":
            problems.append(
                "Missing Graphviz `dot` binary. Fix: sudo apt install graphviz "
                "(Debian/Ubuntu) or sudo dnf install graphviz (Fedora/RHEL)"
            )
        else:
            problems.append(
                "Missing Graphviz `dot` binary. Install Graphviz for your platform: "
                "https://graphviz.org/download/"
            )

    if problems:
        print("ENVIRONMENT NOT READY")
        for p in problems:
            print(f"- {p}")
        return 1

    print("OK: diagrams + graphviz available")
    return 0


if __name__ == "__main__":
    sys.exit(main())

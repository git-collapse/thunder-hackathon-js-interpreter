#!/usr/bin/env python3
"""Main entry point for the PyJS JavaScript interpreter."""

import argparse
import sys
from pathlib import Path

# Allow running as script or module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project.errors import JSError
from project.interpreter import interpret


def main():
    parser = argparse.ArgumentParser(
        description="PyJS - Run JavaScript source code using a Python interpreter"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="JavaScript file to execute",
    )
    parser.add_argument(
        "-e", "--eval",
        dest="code",
        help="Execute JavaScript code string",
    )
    parser.add_argument(
        "-c", "--code",
        dest="code_alt",
        help="Execute JavaScript code string (alias)",
    )
    args = parser.parse_args()

    source = None
    if args.code:
        source = args.code
    elif args.code_alt:
        source = args.code_alt
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        source = path.read_text(encoding="utf-8")
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            source = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)

    try:
        output = interpret(source)
        for line in output:
            print(line)
    except JSError as e:
        print(e.format(), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Internal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

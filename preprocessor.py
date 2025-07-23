"""
Simple Preprocessor for the Simulated CPU Assembler

Features:
- #define NAME VALUE   : define simple text macros
- #include "FILE"     : include other source files

Designed to be minimal, easy to extend, and independent of project internals.
"""
import os
import re

class Preprocessor:
    def __init__(self, include_paths=None):
        # Macro table: name -> replacement text
        self.macros = {}
        # Directories to search for include files (relative or absolute)
        self.include_paths = include_paths or []
        # Internal state for preventing recursive includes
        self._processed_files = set()
        self._output_lines = []

    def preprocess(self, filepath):
        """
        Process the given file, handling #define and #include directives,
        and return the resulting text.
        """
        # Reset state for each top-level run
        self._processed_files.clear()
        self._output_lines.clear()

        abs_path = os.path.abspath(filepath)
        self._process_file(abs_path)
        return ''.join(self._output_lines)

    def _process_file(self, abs_path):
        # Avoid including the same file twice
        if abs_path in self._processed_files:
            return
        self._processed_files.add(abs_path)

        base_dir = os.path.dirname(abs_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.rstrip('\n')
                    stripped = line.lstrip()

                    # Handle #define
                    if stripped.startswith('#define '):
                        parts = stripped[len('#define '):].split(maxsplit=1)
                        name = parts[0]
                        value = parts[1] if len(parts) > 1 else ''
                        self.macros[name] = value

                    # Handle #include
                    elif stripped.startswith('#include '):
                        match = re.match(r'#include\s+"([^"]+)"', stripped)
                        if not match:
                            raise SyntaxError(f"Invalid include directive: {line}")
                        include_name = match.group(1)
                        # Search in base directory first, then other include_paths
                        search_dirs = [base_dir] + self.include_paths
                        for inc_dir in search_dirs:
                            candidate = os.path.join(inc_dir, include_name)
                            if os.path.isfile(candidate):
                                self._process_file(os.path.abspath(candidate))
                                break
                        else:
                            raise FileNotFoundError(f"Included file not found: {include_name}")

                    # Normal line: perform macro expansion
                    else:
                        output = self._expand_macros(line)
                        self._output_lines.append(output + '\n')
        except IOError as e:
            raise IOError(f"Error reading file {abs_path}: {e}")

    def _expand_macros(self, line):
        # Split on non-word characters to avoid accidental substrings
        tokens = re.split(r'(\W+)', line)
        for i, tok in enumerate(tokens):
            if tok in self.macros:
                tokens[i] = self.macros[tok]
        return ''.join(tokens)

# Example CLI usage
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python preprocessor.py <source-file>")
        sys.exit(1)
    src = sys.argv[1]
    # Add any additional include directories here
    pre = Preprocessor(include_paths=[os.getcwd()])
    result = pre.preprocess(src)
    sys.stdout.write(result)

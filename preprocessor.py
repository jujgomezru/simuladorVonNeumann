import re
from pathlib import Path

class Preprocessor:
    macro_pattern  = re.compile(r'^#define\s+([A-Za-z_]\w*)\s+(.+)$')
    include_pattern = re.compile(r'^#include\s+"([^"]+)"')

    def __init__(self, include_dir='includes'):
        self.macros = {}
        self.include_dir = Path(include_dir)

    def process_file(self, filepath: str) -> str:
        lines = []
        data = Path(filepath).read_bytes()
        if data.startswith(b'\xef\xbb\xbf'):
            content = data.decode('utf-8-sig')
        elif data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
            content = data.decode('utf-16')
        else:
            try:
                content = data.decode('utf-8')
            except UnicodeDecodeError:
                content = data.decode('cp1252')
        for raw in content.splitlines():
            if m := self.macro_pattern.match(raw):
                name, val = m.groups()
                self.macros[name] = val
            elif m := self.include_pattern.match(raw):
                inc = self.include_dir / m.group(1)
                lines.append(self.process_file(str(inc)))
            else:
                lines.append(self.expand_macros(raw))
        return '\n'.join(lines)

    def expand_macros(self, line: str) -> str:
        for name, val in self.macros.items():
            line = re.sub(rf"\b{name}\b", val, line)
        return line

if __name__ == '__main__':
    import sys
    text = Preprocessor().process_file(sys.argv[1])
    sys.stdout.buffer.write(text.encode('utf-8'))

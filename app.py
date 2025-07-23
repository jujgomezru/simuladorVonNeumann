import tkinter as tk
from tkinter import scrolledtext
from main import run_source_code  # ahora importa correctamente

class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Simulador de CPU con Compilador")

        # Configuración superior
        config_frame = tk.Frame(root)
        config_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(config_frame, text="Consultar Registros (0-15):").grid(row=0, column=0, sticky="w")
        self.reg_entry = tk.Entry(config_frame, width=20)
        self.reg_entry.grid(row=0, column=1, padx=5)

        tk.Label(config_frame, text="Consultar Memorias (hex):").grid(row=0, column=2, sticky="w")
        self.mem_entry = tk.Entry(config_frame, width=20)
        self.mem_entry.grid(row=0, column=3, padx=5)

        # Entrada de código fuente
        instr_label = tk.Label(root, text="Código fuente (alto nivel, ensamblador o binario):")
        instr_label.pack(anchor="w", padx=10)
        self.instr_text = scrolledtext.ScrolledText(root, width=90, height=15)
        self.instr_text.pack(padx=10, pady=5)

        # Botón ejecutar
        run_btn = tk.Button(root, text="Compilar y Ejecutar", command=self.run)
        run_btn.pack(pady=5)

        # Área de salida
        output_label = tk.Label(root, text="Salida:")
        output_label.pack(anchor="w", padx=10)
        self.output_text = scrolledtext.ScrolledText(root, width=90, height=12, state="disabled")
        self.output_text.pack(padx=10, pady=5)

    def parse_list(self, text, is_mem=False):
        items = []
        text = text.replace(' ', '')
        if not text:
            return items
        for part in text.split(','):
            if '-' in part:
                start_str, end_str = part.split('-', 1)
                try:
                    start = int(start_str, 0) if is_mem else int(start_str)
                    end = int(end_str, 0) if is_mem else int(end_str)
                    for v in range(start, end + 1):
                        items.append(v)
                except ValueError:
                    continue
            else:
                try:
                    items.append(int(part, 0) if is_mem else int(part))
                except ValueError:
                    continue
        return items

    def run(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)

        reg_q = self.reg_entry.get()
        mem_q = self.mem_entry.get()
        raw_lines = self.instr_text.get("1.0", tk.END).strip().splitlines()
        source_code = "\n".join(raw_lines)

        try:
            # Ejecutar compilador y simulador
            from io import StringIO
            import sys

            # Redirigir stdout para capturar la salida
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            run_source_code(source_code)

            # Restaurar stdout
            sys.stdout = old_stdout
            output = mystdout.getvalue()
            self.output_text.insert(tk.END, output)

        except Exception as e:
            self.output_text.insert(tk.END, f"❌ Error: {e}\n")

        self.output_text.configure(state="disabled")

if __name__ == '__main__':
    root = tk.Tk()
    app = SimulatorGUI(root)
    root.mainloop()

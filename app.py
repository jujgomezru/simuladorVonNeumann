import tkinter as tk
from tkinter import scrolledtext
from main import run_instructions

class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Simulador CPU")

        # Frame para configuración de base y consultas
        query_frame = tk.Frame(root)
        query_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(query_frame, text="Dirección Base (hex):").grid(row=0, column=0, sticky="w")
        self.base_entry = tk.Entry(query_frame, width=12)
        self.base_entry.insert(0, "0x0")
        self.base_entry.grid(row=0, column=1, padx=5)

        tk.Label(query_frame, text="Consultar Registros (0-15):").grid(row=0, column=2, sticky="w")
        self.reg_entry = tk.Entry(query_frame, width=20)
        self.reg_entry.grid(row=0, column=3, padx=5)

        tk.Label(query_frame, text="Consultar Memorias (hex):").grid(row=0, column=4, sticky="w")
        self.mem_entry = tk.Entry(query_frame, width=20)
        self.mem_entry.grid(row=0, column=5, padx=5)

        # Área de texto para instrucciones
        instr_label = tk.Label(root, text="Instrucciones (binario o tupla, una por línea):")
        instr_label.pack(anchor="w", padx=10)
        self.instr_text = scrolledtext.ScrolledText(root, width=80, height=15)
        self.instr_text.pack(padx=10, pady=5)

        # Botón Ejecutar
        run_btn = tk.Button(root, text="Ejecutar", command=self.run)
        run_btn.pack(pady=5)

        # Área de texto para salida
        out_label = tk.Label(root, text="Salida:")
        out_label.pack(anchor="w", padx=10)
        self.output_text = scrolledtext.ScrolledText(root, width=80, height=10, state="disabled")
        self.output_text.pack(padx=10, pady=5)

    def parse_list(self, text, is_mem=False):
        """Parses comma/dash-separated ranges. Returns list of ints."""
        items = []
        text = text.replace(' ', '')
        if not text:
            return items
        for part in text.split(','):
            if '-' in part:
                start_str, end_str = part.split('-', 1)
                try:
                    if is_mem:
                        start = int(start_str, 0)
                        end = int(end_str, 0)
                    else:
                        start = int(start_str)
                        end = int(end_str)
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
        # Limpiar y habilitar salida
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)

        base_q = self.base_entry.get().strip()
        reg_q = self.reg_entry.get()
        mem_q = self.mem_entry.get()

        # Leer instrucciones
        raw = self.instr_text.get("1.0", tk.END).strip().splitlines()
        instrs = [line.strip() for line in raw if line.strip()]

        # Parsear base
        try:
            base = int(base_q, 0)
        except ValueError:
            self.output_text.insert(tk.END, f"Dirección base inválida: {base_q}\n")
            self.output_text.configure(state="disabled")
            return

        try:
            cpu, mem = run_instructions(instrs, base=base)

            # Registros
            regs = self.parse_list(reg_q, is_mem=False)
            for r in regs:
                if 0 <= r < len(cpu.reg):
                    self.output_text.insert(tk.END, f"R{r} = {cpu.reg[r]}\n")
                else:
                    self.output_text.insert(tk.END, f"Registro inválido: {r}\n")

            # Memorias
            mems = self.parse_list(mem_q, is_mem=True)
            for addr in mems:
                try:
                    raw_val = mem.leer(addr)
                    val = raw_val[0] if isinstance(raw_val, tuple) else raw_val
                    self.output_text.insert(tk.END, f"Mem[{hex(addr)}] = {val}\n")
                except AssertionError as e:
                    self.output_text.insert(tk.END, f"Error al leer memoria en {hex(addr)}: {e}\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"Error durante ejecución: {e}\n")

        # Deshabilitar salida
        self.output_text.configure(state="disabled")

if __name__ == '__main__':
    root = tk.Tk()
    SimulatorGUI(root)
    root.mainloop()

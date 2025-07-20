import tkinter as tk
from tkinter import scrolledtext, ttk
import tempfile
import os

from main import run_instructions, run_assembly

class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Simulador CPU")

        # -----------------------
        # Selección de modo
        # -----------------------
        mode_frame = tk.Frame(root)
        mode_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(mode_frame, text="Modo de entrada:").pack(side="left")

        self.mode_var = tk.StringVar(value="asm")
        asm_rb = tk.Radiobutton(mode_frame, text="Ensamblador", variable=self.mode_var, value="asm")
        bin_rb = tk.Radiobutton(mode_frame, text="Binario/Tuplas", variable=self.mode_var, value="bin")
        asm_rb.pack(side="left", padx=5)
        bin_rb.pack(side="left", padx=5)

        # -----------------------
        # Frame para configuración de base y consultas
        # -----------------------
        query_frame = tk.Frame(root)
        query_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(query_frame, text="Dirección Base (hex):").grid(row=0, column=0, sticky="w")
        self.base_entry = tk.Entry(query_frame, width=12)
        self.base_entry.insert(0, "0x100")
        self.base_entry.grid(row=0, column=1, padx=5)

        tk.Label(query_frame, text="Consultar Registros (0-15):").grid(row=0, column=2, sticky="w")
        self.reg_entry = tk.Entry(query_frame, width=20)
        self.reg_entry.grid(row=0, column=3, padx=5)

        tk.Label(query_frame, text="Consultar Memorias (hex):").grid(row=0, column=4, sticky="w")
        self.mem_entry = tk.Entry(query_frame, width=20)
        self.mem_entry.grid(row=0, column=5, padx=5)

        # -----------------------
        # Área de texto para instrucciones
        # -----------------------
        instr_label = tk.Label(root, text="Instrucciones:")
        instr_label.pack(anchor="w", padx=10)
        self.instr_text = scrolledtext.ScrolledText(root, width=80, height=15)
        self.instr_text.pack(padx=10, pady=5)

        # -----------------------
        # Botón Ejecutar
        # -----------------------
        run_btn = tk.Button(root, text="Ejecutar", command=self.run)
        run_btn.pack(pady=5)

        # -----------------------
        # Área de texto para salida
        # -----------------------
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
                a, b = part.split('-', 1)
                try:
                    start = int(a, 0) if is_mem else int(a)
                    end   = int(b, 0) if is_mem else int(b)
                    items.extend(range(start, end+1))
                except ValueError:
                    continue
            else:
                try:
                    items.append(int(part, 0) if is_mem else int(part))
                except ValueError:
                    continue
        return items


    def run(self):
        # Habilitar salida
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)

        # Base, regs y mem queries
        try:
            base = int(self.base_entry.get().strip(), 0)
        except ValueError:
            self.output_text.insert(tk.END, "Dirección base inválida.\n")
            self.output_text.configure(state="disabled")
            return
        regs = self.parse_list(self.reg_entry.get(), is_mem=False)
        mems = self.parse_list(self.mem_entry.get(), is_mem=True)

        # Leer líneas de entrada
        raw_lines = [l.strip() for l in self.instr_text.get("1.0", tk.END).splitlines() if l.strip()]

        try:
            if self.mode_var.get() == "asm":
                # Modo ensamblador: escribo a un temporario y luego run_assembly
                with tempfile.NamedTemporaryFile('w', delete=False, suffix=".asm") as tmp:
                    tmp.write("\n".join(raw_lines))
                    tmp_path = tmp.name
                cpu, mem = run_assembly(tmp_path, base=base)
                os.unlink(tmp_path)

            else:
                # Modo binario/tuplas:
                cpu, mem = run_instructions(raw_lines, base=base)

            # Mostrar registros pedidos
            for r in regs:
                if 0 <= r < len(cpu.reg):
                    self.output_text.insert(tk.END, f"R{r} = {cpu.reg[r]}\n")
                else:
                    self.output_text.insert(tk.END, f"Registro inválido: {r}\n")

            # Mostrar memorias pedidas
            for addr in mems:
                try:
                    val = mem.leer(addr)
                    if isinstance(val, tuple):
                        val = val[0]
                    self.output_text.insert(tk.END, f"Mem[{hex(addr)}] = {val}\n")
                except AssertionError as e:
                    self.output_text.insert(tk.END, f"Error al leer Mem[{hex(addr)}]: {e}\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"Error durante ejecución: {e}\n")

        # Deshabilitar salida
        self.output_text.configure(state="disabled")


if __name__ == '__main__':
    root = tk.Tk()
    SimulatorGUI(root)
    root.mainloop()

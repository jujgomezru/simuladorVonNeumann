import tkinter as tk
from tkinter import scrolledtext
from main import Memoria, CPU, Cargador

class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Simulador CPU")

        # Frame para registros iniciales
        top = tk.Frame(root)
        top.pack(padx=10, pady=5, fill="x")

        tk.Label(top, text="Inicio PC:").grid(row=0, column=0, sticky="w")
        self.base_entry = tk.Entry(top, width=10)
        self.base_entry.insert(0, "0xC8")
        self.base_entry.grid(row=0, column=1, padx=5)

        tk.Label(top, text="R1 inicial:").grid(row=0, column=2, sticky="w")
        self.r1_entry = tk.Entry(top, width=10)
        self.r1_entry.insert(0, "36")
        self.r1_entry.grid(row=0, column=3, padx=5)

        tk.Label(top, text="R2 inicial:").grid(row=0, column=4, sticky="w")
        self.r2_entry = tk.Entry(top, width=10)
        self.r2_entry.insert(0, "24")
        self.r2_entry.grid(row=0, column=5, padx=5)

        # Text area para instrucciones
        instr_label = tk.Label(root, text="Instrucciones (una por línea):")
        instr_label.pack(anchor="w", padx=10)
        self.instr_text = scrolledtext.ScrolledText(root, width=80, height=15)
        self.instr_text.pack(padx=10, pady=5)

        # Botón Ejecutar
        run_btn = tk.Button(root, text="Ejecutar", command=self.run)
        run_btn.pack(pady=5)

        # Text area para salida
        out_label = tk.Label(root, text="Salida:")
        out_label.pack(anchor="w", padx=10)
        self.output_text = scrolledtext.ScrolledText(root, width=80, height=8, state="disabled")
        self.output_text.pack(padx=10, pady=5)

    def run(self):
        # Limpiar salida
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)

        # Obtener valores iniciales
        try:
            base = int(self.base_entry.get(), 0)
        except ValueError:
            base = 0
        try:
            r1_init = int(self.r1_entry.get(), 0)
        except ValueError:
            r1_init = 0
        try:
            r2_init = int(self.r2_entry.get(), 0)
        except ValueError:
            r2_init = 0

        # Leer instrucciones
        raw = self.instr_text.get("1.0", tk.END).strip().splitlines()
        instrs = [line.strip() for line in raw if line.strip()]
       
        # Inicializar memoria y CPU
        mem = Memoria()
        cpu = CPU(mem, debug=False)
        cpu.reg[1] = r1_init
        cpu.reg[2] = r2_init

        # Cargar y ejecutar
        try:
            Cargador.cargar(mem, instrs, base_addr=base)
            cpu.PC = base
            cpu.ejecutar()
            # Mostrar resultado en R1
            res = cpu.reg[1]
            self.output_text.insert(tk.END, f"Resultado en R1: {res}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")

        self.output_text.configure(state="disabled")

if __name__ == '__main__':
    root = tk.Tk()
    SimulatorGUI(root)
    root.mainloop()

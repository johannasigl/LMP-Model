import tkinter as tk
import customtkinter as ctk 
import os
import sys

# macOS Sequoia/Sonoma Fix for Anaconda/Tkinter crash
if sys.platform == "darwin":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'
from data import NetworkData
from func import DCPowerFlow
from plot import NetworkPlot

# Appearance Settings
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

param = {
    'nodes': ['A', 'B', 'C'],
    'lines': [
        {'from': 'A', 'to': 'B', 'reactance': 0.1, 'capacity': 100, 'length': 100},
        {'from': 'B', 'to': 'C', 'reactance': 0.1, 'capacity': 100, 'length': 100},
        {'from': 'A', 'to': 'C', 'reactance': 0.2, 'capacity': 50, 'length': 200},
    ],
    'generation': {
        'A': {'capacity': 100, 'cost': 20},
        'B': {'capacity': 50, 'cost': 40},
        'C': {'capacity': 0, 'cost': 0},
    },
    'consumption': {'A': 0, 'B': 0, 'C': 500},
    'window_size': '1200x800',
}

class LMPApp(ctk.CTk):
    def __init__(self, param):
        super().__init__()
        
        self.param = param
        self.title("⚡ LMP Market Simulator")
        self.geometry(param['window_size'])
        
        # Main Layout: Sidebar (Left) and Plot (Right)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.network_data = NetworkData(param)
        self.dc_flow = DCPowerFlow(self.network_data)
        self.network_plot = NetworkPlot(self.network_data)
        
        self._build_gui()
        # Schedule the first update after the window has had a chance to render
        self.after(200, self._update_model)

    def _build_gui(self):
        self.sidebar = ctk.CTkFrame(self, width=400, corner_radius=0, fg_color="#242424")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) # Keep fixed width
        
        # Header
        ctk.CTkLabel(self.sidebar, text="SYSTEM PARAMETERS", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # Container for scrollable sections
        self.scroll_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=10)

        # --- SECTION: LINES ---
        self.line_frame = ctk.CTkScrollableFrame(self.scroll_container, label_text="Line Capacities (MW)", height=200)
        self.line_frame.pack(fill="x", pady=5)
        self._build_line_entries()

        # --- SECTION: GENERATION ---
        self.gen_frame = ctk.CTkScrollableFrame(self.scroll_container, label_text="Generation (Cap | Cost)", height=200)
        self.gen_frame.pack(fill="x", pady=5)
        self._build_gen_entries()

        # --- SECTION: DEMAND ---
        self.dem_frame = ctk.CTkScrollableFrame(self.scroll_container, label_text="Demand (MW)", height=150)
        self.dem_frame.pack(fill="x", pady=5)
        self._build_demand_entries()

        # --- RESULTS & UPDATE BUTTON ---
        self.res_frame = ctk.CTkFrame(self.sidebar, corner_radius=10, fg_color="#1e1e1e")
        self.res_frame.pack(fill="x", padx=10, pady=10)
        
        self.results_label = ctk.CTkLabel(self.res_frame, text="Results...", font=("Courier", 12), justify="left")
        self.results_label.pack(padx=10, pady=10)

        self.update_btn = ctk.CTkButton(self.sidebar, text="UPDATE MODEL", 
                                       command=self._update_model, 
                                       height=45, fg_color="#27ae60", hover_color="#219150",
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self.update_btn.pack(fill="x", padx=20, pady=10)

        # --- SECTION: PRICE CALCULATION EXPLANATION ---
        self.explain_frame = ctk.CTkFrame(self.sidebar, corner_radius=10, fg_color="#2c3e50")
        self.explain_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.explain_frame, text="PRICE CALCULATION EXPLAINED", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#ecf0f1").pack(pady=(10, 5))
        
        self.explanation_text = ctk.CTkLabel(self.explain_frame, 
                                             text="LMP = Marginal Cost + Congestion\n\n"
                                                  "• Marginal Cost: Cost of next MW\n"
                                                  "• Congestion: Price diff due to\n"
                                                  "  limited line capacities.",
                                             font=("Arial", 11), justify="left", text_color="#bdc3c7")
        self.explanation_text.pack(padx=10, pady=5)

        # 2. RIGHT SIDE (PLOT & CALCULATIONS)
        self.right_container = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.right_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.right_container.grid_rowconfigure(0, weight=3) # Plot takes more space
        self.right_container.grid_rowconfigure(1, weight=1) # Calculations at bottom
        self.right_container.grid_columnconfigure(0, weight=1)

        # Plot Area
        self.plot_frame = ctk.CTkFrame(self.right_container, corner_radius=15, fg_color="white")
        self.plot_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.network_plot.embed_in_frame(self.plot_frame)

        # Calculation Panels at Bottom
        self.calc_container = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.calc_container.grid(row=1, column=0, sticky="nsew")
        self.calc_container.grid_columnconfigure(0, weight=1)
        self.calc_container.grid_columnconfigure(1, weight=1)
        self.calc_container.grid_rowconfigure(0, weight=1)

        # Node Calculations Panel
        self.node_calc_frame = ctk.CTkScrollableFrame(self.calc_container, label_text="Node Calculations (LMP = Energy + Congestion)")
        self.node_calc_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.node_calc_label = ctk.CTkLabel(self.node_calc_frame, text="", font=("Courier", 11), justify="left")
        self.node_calc_label.pack(fill="both", expand=True, padx=10, pady=5)

        # Line Calculations Panel
        self.line_calc_frame = ctk.CTkScrollableFrame(self.calc_container, label_text="Line Calculations (Flow = PTDF * Net Injection)")
        self.line_calc_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.line_calc_label = ctk.CTkLabel(self.line_calc_frame, text="", font=("Courier", 11), justify="left")
        self.line_calc_label.pack(fill="both", expand=True, padx=10, pady=5)

    def _build_line_entries(self):
        self.line_vars = {}
        self.line_len_vars = {}
        # Grid Headers
        ctk.CTkLabel(self.line_frame, text="Line", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5)
        ctk.CTkLabel(self.line_frame, text="Cap (MW)", font=("Arial", 11, "bold")).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.line_frame, text="Len (km)", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=5)

        for i, line in enumerate(self.param['lines']):
            name = f"{line['from']}→{line['to']}"
            ctk.CTkLabel(self.line_frame, text=name).grid(row=i+1, column=0, padx=5, sticky="w")
            
            cap_var = tk.DoubleVar(value=line['capacity'])
            self.line_vars[i] = cap_var
            cap_e = ctk.CTkEntry(self.line_frame, textvariable=cap_var, width=60)
            cap_e.grid(row=i+1, column=1, padx=2, pady=2)
            cap_e.bind("<Return>", lambda e: self._update_model())

            len_var = tk.DoubleVar(value=line.get('length', 100))
            self.line_len_vars[i] = len_var
            len_e = ctk.CTkEntry(self.line_frame, textvariable=len_var, width=60)
            len_e.grid(row=i+1, column=2, padx=2, pady=2)
            len_e.bind("<Return>", lambda e: self._update_model())

    def _build_gen_entries(self):
        self.gen_cap_vars = {}
        self.gen_cost_vars = {}
        
        ctk.CTkLabel(self.gen_frame, text="Node", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5)
        ctk.CTkLabel(self.gen_frame, text="Max MW", font=("Arial", 11, "bold")).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.gen_frame, text="€/MWh", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=5)

        for i, node in enumerate(self.param['nodes']):
            ctk.CTkLabel(self.gen_frame, text=node).grid(row=i+1, column=0, padx=5)
            
            cap_v = tk.DoubleVar(value=self.param['generation'][node]['capacity'])
            cost_v = tk.DoubleVar(value=self.param['generation'][node]['cost'])
            
            self.gen_cap_vars[node] = cap_v
            self.gen_cost_vars[node] = cost_v
            
            cap_e = ctk.CTkEntry(self.gen_frame, textvariable=cap_v, width=70)
            cap_e.grid(row=i+1, column=1, padx=2, pady=2)
            cap_e.bind("<Return>", lambda e: self._update_model())
            
            cost_e = ctk.CTkEntry(self.gen_frame, textvariable=cost_v, width=70)
            cost_e.grid(row=i+1, column=2, padx=2, pady=2)
            cost_e.bind("<Return>", lambda e: self._update_model())

    def _build_demand_entries(self):
        self.demand_vars = {}
        for i, node in enumerate(self.param['nodes']):
            ctk.CTkLabel(self.dem_frame, text=f"Node {node}:").grid(row=i, column=0, padx=10, sticky="w")
            
            var = tk.DoubleVar(value=self.param['consumption'][node])
            self.demand_vars[node] = var
            
            e = ctk.CTkEntry(self.dem_frame, textvariable=var, width=100)
            e.grid(row=i, column=1, padx=5, pady=2)
            e.bind("<Return>", lambda e: self._update_model())

    def _update_model(self, event=None):
        try:
            # Sync GUI variables to NetworkData
            for node in self.param['nodes']:
                self.network_data.update_consumption(node, float(self.demand_vars[node].get()))
                self.network_data.update_generation(node, float(self.gen_cap_vars[node].get()), float(self.gen_cost_vars[node].get()))
            
            for i in range(len(self.param['lines'])):
                self.network_data.update_line_capacity(i, float(self.line_vars[i].get()))
                self.network_data.update_line_length(i, float(self.line_len_vars[i].get()))

            results = self.dc_flow.solve()
            self._display_results(results)
            self.network_plot.update(results)
        except Exception as e:
            self.results_label.configure(text=f"Error: Invalid Input", text_color="orange")

    def _display_results(self, results):
        if not results['feasible']:
            self.results_label.configure(text="⚠ INFEASIBLE SOLUTION\nCheck line capacities.", text_color="#e74c3c")
            self.node_calc_label.configure(text="N/A")
            self.line_calc_label.configure(text="N/A")
            return
        
        # 1. SIDEBAR RESULTS (Summary only)
        total_cost = results['total_cost']
        total_shed = sum(results.get('shedding', {}).values())
        
        txt = f"SYSTEM SUMMARY\n"
        txt += f"Total Cost: {total_cost:.2f} €/h\n"
        
        if total_shed > 0.1:
            txt += f"⚠ SHORTFALL: {total_shed:.1f} MW\n"
            self.results_label.configure(text=txt, text_color="#f1c40f")
        else:
            txt += f"Status: Healthy\n"
            self.results_label.configure(text=txt, text_color="#2ecc71")

        # 2. NODE CALCULATIONS
        node_txt = ""
        energy_price = results['energy_price']
        for node, lmp in results['lmp'].items():
            node_txt += f"NODE {node}:\n"
            node_txt += f"  Energy:     {energy_price:>6.2f}\n"
            
            details = results['lmp_details'].get(node, {})
            line_details = details.get('line_details', [])
            congestion = 0
            if not line_details:
                node_txt += f"  Congestion:  0.00 (No bottlenecks)\n"
            else:
                for line_id, contrib in line_details:
                    node_txt += f"  - {line_id}: {contrib:>+6.2f}\n"
                    congestion += contrib
                node_txt += f"  Total Cong: {congestion:>6.2f}\n"
            node_txt += f"  LMP Result: {lmp:>6.2f} €/MWh\n"
            node_txt += "-" * 30 + "\n"
        self.node_calc_label.configure(text=node_txt)

        # 3. LINE CALCULATIONS
        line_txt = ""
        gen_flows = results.get('generator_flows', {})
        for i, line in enumerate(self.param['lines']):
            line_id = f"{line['from']}→{line['to']}"
            total_flow = results['flows'][line_id]
            cap = results['capacities'][line_id]
            util = (abs(total_flow) / cap * 100) if cap > 0 else 0
            
            line_txt += f"LINE {line_id}:\n"
            overload_msg = " ⚠ OVERLOAD ⚠" if abs(total_flow) > (cap + 0.1) else ""
            line_txt += f"  Total Flow: {total_flow:>7.2f} MW ({util:>5.1f}%){overload_msg}\n"
            
            # Breakdown by node
            contributions = gen_flows.get(line_id, {})
            if contributions:
                line_txt += "  Breakdown by Gen Node:\n"
                for gen_node, val in contributions.items():
                    line_txt += f"    - Node {gen_node}: {val:>+7.2f} MW\n"
            
            # Show top PTDFs for this line
            ptdf_row = results['ptdf'][i]
            line_txt += "  PTDFs: "
            for j, node in enumerate(self.param['nodes']):
                line_txt += f"{node}:{ptdf_row[j]:.2f} "
            line_txt += "\n" + "-" * 35 + "\n"
        self.line_calc_label.configure(text=line_txt)

if __name__ == "__main__":
    app = LMPApp(param)
    app.mainloop()
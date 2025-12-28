import tkinter as tk
import customtkinter as ctk
import os
import sys

# macOS Fix
if sys.platform == "darwin":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

from data import NetworkData
from func import DCPowerFlow
from plot import NetworkPlot

# --- THEME CONSTANTS ---
COLORS = {
    "bg_dark": "#0f172a",      # Deep Slate Blue
    "bg_card": "#1e293b",      # Lighter Slate
    "accent": "#10b981",       # Emerald Green
    "accent_hover": "#059669",
    "text_main": "#f8fafc",    # Ghost White
    "text_dim": "#94a3b8",     # Muted Blue/Gray
    "border": "#334155",
    "danger": "#ef4444",
    "warning": "#f59e0b"
}

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
    'window_size': '1400x900',
}

class LMPApp(ctk.CTk):
    def __init__(self, param):
        super().__init__()
        
        self.param = param
        self.title("⚡ LMP Market Simulator")
        self.geometry(param['window_size'])
        
        # Set Global Appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg_dark"])

        # Initialize Logic
        self.network_data = NetworkData(param)
        self.dc_flow = DCPowerFlow(self.network_data)
        self.network_plot = NetworkPlot(self.network_data)
        
        self._build_gui()
        self.after(200, self._update_model)

    def _build_gui(self):
        # 1. Main Grid Configuration
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content
        self.grid_rowconfigure(0, weight=1)

        # 2. SIDEBAR (Left)
        self.sidebar = ctk.CTkFrame(self, width=340, corner_radius=0, fg_color=COLORS["bg_card"], border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Sidebar Header
        header_label = ctk.CTkLabel(self.sidebar, text="⚡ MARKET CONTROL", 
                                    font=ctk.CTkFont(size=20, weight="bold"), 
                                    text_color=COLORS["text_main"])
        header_label.pack(pady=(25, 20), padx=20, anchor="w")

        # Scrollable area for inputs
        self.scroll_container = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", 
                                                       scrollbar_button_color=COLORS["border"])
        self.scroll_container.pack(fill="both", expand=True, padx=10)

        # --- SECTION: INPUTS ---
        self._create_section_label(self.scroll_container, "⛓ LINE CAPACITIES")
        self.line_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.line_frame.pack(fill="x", pady=(0, 15))
        self._build_line_entries()

        self._create_section_label(self.scroll_container, "🏭 GENERATION")
        self.gen_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.gen_frame.pack(fill="x", pady=(0, 15))
        self._build_gen_entries()

        self._create_section_label(self.scroll_container, "📉 NODE DEMAND")
        self.dem_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.dem_frame.pack(fill="x", pady=(0, 15))
        self._build_demand_entries()

        # Results Summary
        self._create_section_label(self.scroll_container, "📊 SYSTEM STATUS")
        self.results_label = ctk.CTkLabel(self.scroll_container, text="Calculating...", 
                                         font=ctk.CTkFont(size=11), 
                                         text_color=COLORS["text_main"], justify="left")
        self.results_label.pack(anchor="w", padx=10, pady=5)

        # Update Button
        self.update_btn = ctk.CTkButton(self.sidebar, text="🔄 RECALCULATE MARKET", 
                                       command=self._update_model, 
                                       height=45, corner_radius=8,
                                       fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.update_btn.pack(fill="x", padx=20, pady=20)

        # 3. MAIN CONTENT (Right) - Two columns: Plot (left) and Analysis Panels (right)
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=5)  # Plot - larger
        self.main_content.grid_columnconfigure(1, weight=2)  # Analysis panels - smaller

        # --- PLOT CARD (Left) ---
        self.plot_container = ctk.CTkFrame(self.main_content, fg_color=COLORS["bg_card"], 
                                           corner_radius=12, border_color=COLORS["border"], border_width=1)
        self.plot_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Status indicator overlay
        self.status_pill = ctk.CTkLabel(self.plot_container, text="● SYSTEM STABLE", 
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       fg_color="#065f46", text_color="#34d399", 
                                       corner_radius=10, height=24, padx=15)
        self.status_pill.place(relx=0.98, rely=0.03, anchor="ne")
        
        # Embed the network plot
        self.network_plot.embed_in_frame(self.plot_container)

        # --- RIGHT SIDE DATA PANELS (Vertical Stack) ---
        self.data_grid = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.data_grid.grid(row=0, column=1, sticky="nsew")
        self.data_grid.grid_columnconfigure(0, weight=1, minsize=350)  # Minimum width for text
        self.data_grid.grid_rowconfigure(0, weight=1)  # Node Economics
        self.data_grid.grid_rowconfigure(1, weight=1)  # Flow Analysis
        self.data_grid.grid_rowconfigure(2, weight=1)  # System Diagnostics

        # Styled Calculation Boxes (Stacked Vertically)
        self.node_calc_label = self._create_data_box(self.data_grid, "📍 NODE ECONOMICS", 0, 0)
        self.line_calc_label = self._create_data_box(self.data_grid, "🔌 FLOW ANALYSIS", 1, 0)
        self.diagnostics_label = self._create_data_box(self.data_grid, "⚠️ SYSTEM DIAGNOSTICS", 2, 0)

    def _create_section_label(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_dim"])
        lbl.pack(anchor="w", padx=5, pady=(10, 5))

    def _create_data_box(self, parent, title, row, col):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12, 
                            border_color=COLORS["border"], border_width=1)
        # Vertical stacking: add padding between boxes
        pady = (0, 0) if row == 0 else (10, 0)
        frame.grid(row=row, column=col, sticky="nsew", pady=pady)
        
        lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["accent"])
        lbl.pack(pady=(10, 5), padx=15, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        content = ctk.CTkLabel(scroll, text="Awaiting calculation...", 
                              font=ctk.CTkFont(family="Courier", size=12), 
                              justify="left", text_color=COLORS["text_main"], anchor="nw")
        content.pack(fill="both", expand=True, padx=10)
        return content

    def _build_line_entries(self):
        # Header Row
        h_frame = ctk.CTkFrame(self.line_frame, fg_color="transparent")
        h_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(h_frame, text="Line", width=70, font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS["text_dim"]).pack(side="left")
        ctk.CTkLabel(h_frame, text="Cap (MW)", width=75, font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS["text_dim"]).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Len (km)", width=75, font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS["text_dim"]).pack(side="left")

        self.line_vars = {}
        self.line_len_vars = {}
        for i, line in enumerate(self.param['lines']):
            row = ctk.CTkFrame(self.line_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            name = f"{line['from']}→{line['to']}"
            ctk.CTkLabel(row, text=name, width=70, anchor="w", 
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_main"]).pack(side="left")
            
            cap_var = tk.DoubleVar(value=line['capacity'])
            self.line_vars[i] = cap_var
            e1 = ctk.CTkEntry(row, textvariable=cap_var, width=70, height=28, 
                             border_width=1, fg_color=COLORS["bg_dark"],
                             border_color=COLORS["border"])
            e1.pack(side="left", padx=5)
            e1.bind("<Return>", lambda e: self._update_model())

            len_var = tk.DoubleVar(value=line.get('length', 100))
            self.line_len_vars[i] = len_var
            e2 = ctk.CTkEntry(row, textvariable=len_var, width=70, height=28, 
                             border_width=1, fg_color=COLORS["bg_dark"],
                             border_color=COLORS["border"])
            e2.pack(side="left", padx=5)
            e2.bind("<Return>", lambda e: self._update_model())

    def _build_gen_entries(self):
        # Header Row
        h_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        h_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(h_frame, text="Node", width=50, font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS["text_dim"]).pack(side="left")
        ctk.CTkLabel(h_frame, text="Max MW", width=75, font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS["text_dim"]).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="€/MWh", width=75, font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS["text_dim"]).pack(side="left")

        self.gen_cap_vars = {}
        self.gen_cost_vars = {}
        for node in self.param['nodes']:
            row = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=node, width=50, anchor="w",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_main"]).pack(side="left")
            
            cap_v = tk.DoubleVar(value=self.param['generation'][node]['capacity'])
            cost_v = tk.DoubleVar(value=self.param['generation'][node]['cost'])
            
            self.gen_cap_vars[node] = cap_v
            self.gen_cost_vars[node] = cost_v
            
            cap_e = ctk.CTkEntry(row, textvariable=cap_v, width=70, height=28,
                                border_width=1, fg_color=COLORS["bg_dark"],
                                border_color=COLORS["border"])
            cap_e.pack(side="left", padx=5)
            cap_e.bind("<Return>", lambda e: self._update_model())
            
            cost_e = ctk.CTkEntry(row, textvariable=cost_v, width=70, height=28,
                                 border_width=1, fg_color=COLORS["bg_dark"],
                                 border_color=COLORS["border"])
            cost_e.pack(side="left", padx=5)
            cost_e.bind("<Return>", lambda e: self._update_model())

    def _build_demand_entries(self):
        self.demand_vars = {}
        for node in self.param['nodes']:
            row = ctk.CTkFrame(self.dem_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"Node {node}:", width=70, anchor="w",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_main"]).pack(side="left")
            
            var = tk.DoubleVar(value=self.param['consumption'][node])
            self.demand_vars[node] = var
            
            e = ctk.CTkEntry(row, textvariable=var, width=100, height=28,
                            border_width=1, fg_color=COLORS["bg_dark"],
                            border_color=COLORS["border"])
            e.pack(side="left", padx=5)
            e.bind("<Return>", lambda e: self._update_model())

    def _update_model(self, event=None):
        try:
            # Sync GUI variables to NetworkData
            for node in self.param['nodes']:
                self.network_data.update_consumption(node, float(self.demand_vars[node].get()))
                self.network_data.update_generation(node, float(self.gen_cap_vars[node].get()), 
                                                    float(self.gen_cost_vars[node].get()))
            
            for i in range(len(self.param['lines'])):
                self.network_data.update_line_capacity(i, float(self.line_vars[i].get()))
                self.network_data.update_line_length(i, float(self.line_len_vars[i].get()))

            results = self.dc_flow.solve()
            self._display_results(results)
            self.network_plot.update(results)
        except Exception as e:
            self.results_label.configure(text=f"❌ Error: {str(e)[:50]}", text_color=COLORS["danger"])
            self.status_pill.configure(text="● ERROR", fg_color="#7f1d1d", text_color="#fca5a5")

    def _display_results(self, results):
        if not results['feasible']:
            self.results_label.configure(text="⚠ INFEASIBLE SOLUTION\nCheck line capacities.", 
                                        text_color=COLORS["danger"])
            self.status_pill.configure(text="● INFEASIBLE", fg_color="#7f1d1d", text_color="#fca5a5")
            self.node_calc_label.configure(text="Solution not feasible")
            self.line_calc_label.configure(text="Solution not feasible")
            self.diagnostics_label.configure(text="🚨 INFEASIBLE PROBLEM\n\nThe optimization could not find a solution.\n\n→ Check that total generation capacity\n  exceeds total demand\n→ Ensure line capacities are reasonable\n→ Verify all input values are positive")
            return
        
        # 1. SIDEBAR RESULTS (Summary only)
        total_cost = results['total_cost']
        total_shed = sum(results.get('shedding', {}).values())
        
        txt = "SYSTEM SUMMARY\n"
        txt += f"Total Cost: €{total_cost:.2f}/h\n"
        
        if total_shed > 0.1:
            txt += f"⚠ SHORTFALL: {total_shed:.1f} MW"
            self.results_label.configure(text=txt, text_color=COLORS["warning"])
            self.status_pill.configure(text="● SCARCITY", fg_color="#78350f", text_color="#fbbf24")
        else:
            txt += "Status: ✓ Healthy"
            self.results_label.configure(text=txt, text_color=COLORS["accent"])
            self.status_pill.configure(text="● SYSTEM STABLE", fg_color="#065f46", text_color="#34d399")

        # 2. NODE CALCULATIONS
        node_txt = ""
        energy_price = results['energy_price']
        for node, lmp in results['lmp'].items():
            node_txt += f"NODE {node}:\n"
            node_txt += f"  Energy:     €{energy_price:>7.2f}\n"
            
            details = results['lmp_details'].get(node, {})
            line_details = details.get('line_details', [])
            congestion = 0
            if not line_details:
                node_txt += f"  Congestion: €0.00 (No bottlenecks)\n"
            else:
                for line_id, contrib in line_details:
                    node_txt += f"  - {line_id}: €{contrib:>+7.2f}\n"
                    congestion += contrib
                node_txt += f"  Total Cong: €{congestion:>7.2f}\n"
            node_txt += f"  LMP Result: €{lmp:>7.2f}/MWh\n"
            
            # Show shedding if any
            shed = results.get('shedding', {}).get(node, 0)
            if shed > 0.1:
                node_txt += f"  ⚠ UNMET: {shed:.1f} MW\n"
            
            node_txt += "-" * 32 + "\n"
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
            
            # Show PTDFs for this line
            ptdf_row = results['ptdf'][i]
            line_txt += "  PTDFs: "
            for j, node in enumerate(self.param['nodes']):
                line_txt += f"{node}:{ptdf_row[j]:+.2f} "
            line_txt += "\n" + "-" * 37 + "\n"
        self.line_calc_label.configure(text=line_txt)

        # 4. SYSTEM DIAGNOSTICS
        diagnostics_txt = self._generate_diagnostics(results)
        self.diagnostics_label.configure(text=diagnostics_txt)

    def _generate_diagnostics(self, results):
        """Analyze system constraints and provide actionable suggestions"""
        issues = []
        suggestions = []
        
        # 1. Check for overloaded lines
        for i, line in enumerate(self.param['lines']):
            line_id = f"{line['from']}→{line['to']}"
            flow = results['flows'][line_id]
            capacity = results['capacities'][line_id]
            utilization = (abs(flow) / capacity * 100) if capacity > 0 else 0
            
            if abs(flow) > capacity + 0.1:
                issues.append(f"⚠ LINE {line_id} OVERLOADED")
                issues.append(f"  Flow: {abs(flow):.1f} MW > Capacity: {capacity:.1f} MW")
                suggestions.append(f"→ Increase {line_id} capacity to {abs(flow)*1.2:.0f}+ MW")
                suggestions.append(f"→ Add generation closer to demand")
                suggestions.append(f"→ Reduce total system demand")
                suggestions.append("")
            elif utilization > 95:
                issues.append(f"⚡ LINE {line_id} NEAR LIMIT")
                issues.append(f"  Utilization: {utilization:.1f}%")
                suggestions.append(f"→ Consider increasing {line_id} capacity")
                suggestions.append("")
        
        # 2. Check for generation at maximum capacity
        for node in self.param['nodes']:
            gen = results['generation'][node]
            capacity = self.network_data.generation[node]['capacity']
            
            if capacity > 0 and gen > capacity * 0.99:
                issues.append(f"⚡ GENERATOR {node} AT MAX CAPACITY")
                issues.append(f"  Output: {gen:.1f} MW / {capacity:.1f} MW")
                suggestions.append(f"→ Increase generator {node} capacity")
                suggestions.append(f"→ Add generation at other nodes")
                suggestions.append(f"→ Reduce system demand")
                suggestions.append("")
        
        # 3. Check for load shedding (unmet demand)
        total_shed = sum(results.get('shedding', {}).values())
        if total_shed > 0.1:
            issues.append(f"🚨 LOAD SHEDDING: {total_shed:.1f} MW UNMET")
            for node, shed in results.get('shedding', {}).items():
                if shed > 0.1:
                    issues.append(f"  Node {node}: {shed:.1f} MW unmet")
            
            # Analyze why shedding is happening
            total_gen_cap = sum(self.network_data.generation[n]['capacity'] 
                               for n in self.param['nodes'])
            total_demand = sum(self.network_data.consumption.values())
            
            if total_gen_cap < total_demand:
                suggestions.append(f"→ INSUFFICIENT GENERATION CAPACITY")
                suggestions.append(f"  Total capacity: {total_gen_cap:.1f} MW")
                suggestions.append(f"  Total demand: {total_demand:.1f} MW")
                suggestions.append(f"  Deficit: {total_demand - total_gen_cap:.1f} MW")
                suggestions.append(f"→ Increase generation capacity by {(total_demand - total_gen_cap)*1.1:.0f}+ MW")
            else:
                suggestions.append(f"→ TRANSMISSION CONSTRAINTS LIMITING DELIVERY")
                suggestions.append(f"  Enough generation exists, but can't reach demand")
                suggestions.append(f"→ Increase transmission line capacities")
                suggestions.append(f"→ Add generation closer to load centers")
            suggestions.append("")
        
        # 4. Check for high LMP prices (scarcity pricing)
        max_lmp = max(results['lmp'].values())
        if max_lmp > 1000:
            issues.append(f"💰 HIGH PRICES: LMP up to €{max_lmp:.0f}/MWh")
            issues.append(f"  Indicates scarcity or severe constraints")
            suggestions.append(f"→ System is under stress - see issues above")
            suggestions.append("")
        
        # 5. Check for congestion (price differences)
        lmps = list(results['lmp'].values())
        if len(lmps) > 1:
            price_spread = max(lmps) - min(lmps)
            if price_spread > 50:
                issues.append(f"📊 SIGNIFICANT CONGESTION")
                issues.append(f"  Price spread: €{price_spread:.2f}/MWh")
                
                # Find which lines are causing congestion
                congested_lines = []
                for node in self.param['nodes']:
                    details = results['lmp_details'].get(node, {})
                    line_details = details.get('line_details', [])
                    for line_id, contrib in line_details:
                        if abs(contrib) > 10 and line_id not in congested_lines:
                            congested_lines.append(line_id)
                
                if congested_lines:
                    issues.append(f"  Congested lines: {', '.join(congested_lines)}")
                    suggestions.append(f"→ Increase capacity on: {', '.join(congested_lines)}")
                suggestions.append(f"→ Balance generation across nodes")
                suggestions.append("")
        
        # Build final text
        if not issues:
            return "✅ NO CONSTRAINTS ACTIVE\n\nSystem operating normally.\nAll limits satisfied."
        
        diag_txt = "ACTIVE CONSTRAINTS & ISSUES:\n"
        diag_txt += "=" * 42 + "\n\n"
        diag_txt += "\n".join(issues)
        diag_txt += "\n\n"
        diag_txt += "SUGGESTED ACTIONS:\n"
        diag_txt += "=" * 42 + "\n\n"
        diag_txt += "\n".join(suggestions)
        
        return diag_txt

if __name__ == "__main__":
    app = LMPApp(param)
    app.mainloop()

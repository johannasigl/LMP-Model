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
    "bg_header": "#1e3a5f",    # Header blue
    "accent": "#10b981",       # Emerald Green
    "accent_hover": "#059669",
    "text_main": "#f8fafc",    # Ghost White
    "text_dim": "#94a3b8",     # Muted Blue/Gray
    "border": "#334155",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "success": "#10b981"
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
    'window_size': '1600x1000',
}

class LMPAppV2(ctk.CTk):
    def __init__(self, param):
        super().__init__()
        
        self.param = param
        self.title("⚡ LMP Market Simulator v2.0")
        self.geometry(param['window_size'])
        
        # Set Global Appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg_dark"])

        # Initialize Logic
        self.network_data = NetworkData(param)
        self.dc_flow = DCPowerFlow(self.network_data)
        self.network_plot = NetworkPlot(self.network_data)
        
        # State for collapsible sections
        self.section_states = {
            'network': True,
            'generation': True,
            'demand': True
        }
        
        self._build_gui()
        self.after(200, self._update_model)

    def _build_gui(self):
        # Main Grid Configuration
        self.grid_columnconfigure(0, weight=0)  # Left sidebar
        self.grid_columnconfigure(1, weight=1)  # Center + Right
        self.grid_rowconfigure(0, weight=0)     # Header
        self.grid_rowconfigure(1, weight=1)     # Main content

        # === SYSTEM STATUS HEADER ===
        self._build_status_header()

        # === LEFT PANEL: INPUTS & CONTROLS ===
        self._build_left_panel()

        # === CENTER + RIGHT: Network Canvas and Results ===
        self._build_center_right_panel()

    def _build_status_header(self):
        """Top system status bar"""
        header = ctk.CTkFrame(self, height=60, corner_radius=0, 
                             fg_color=COLORS["bg_header"], border_width=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        # Left side: System info
        left_frame = ctk.CTkFrame(header, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        # System Status
        self.status_text = ctk.CTkLabel(left_frame, text="⚡ SYSTEM STATUS: Calculating...", 
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       text_color=COLORS["text_main"])
        self.status_text.pack(side="left", padx=(0, 30))
        
        # Total Cost
        self.cost_text = ctk.CTkLabel(left_frame, text="💶 Cost: €0/h", 
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     text_color=COLORS["text_main"])
        self.cost_text.pack(side="left", padx=(0, 30))
        
        # Total Load
        self.load_text = ctk.CTkLabel(left_frame, text="⚡ Load: 0 MW", 
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     text_color=COLORS["text_main"])
        self.load_text.pack(side="left", padx=(0, 30))
        
        # Active Constraints
        self.constraints_text = ctk.CTkLabel(left_frame, text="Active Constraints: 0", 
                                            font=ctk.CTkFont(size=13),
                                            text_color=COLORS["text_dim"])
        self.constraints_text.pack(side="left")
        
        # Right side: Recalculate button
        self.recalc_btn = ctk.CTkButton(header, text="⟳ RECALCULATE", 
                                       command=self._update_model,
                                       width=150, height=40,
                                       fg_color=COLORS["accent"],
                                       hover_color=COLORS["accent_hover"],
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.recalc_btn.pack(side="right", padx=20, pady=10)

    def _build_left_panel(self):
        """Left sidebar with collapsible input sections"""
        self.left_panel = ctk.CTkFrame(self, width=320, corner_radius=0, 
                                      fg_color=COLORS["bg_card"], border_width=0)
        self.left_panel.grid(row=1, column=0, sticky="nsew")
        self.left_panel.grid_propagate(False)
        
        # Header
        header_label = ctk.CTkLabel(self.left_panel, text="INPUTS & CONTROLS", 
                                    font=ctk.CTkFont(size=16, weight="bold"), 
                                    text_color=COLORS["text_main"])
        header_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent",
                                                       scrollbar_button_color=COLORS["border"])
        self.scroll_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # === COLLAPSIBLE SECTIONS ===
        self._build_network_section()
        self._build_generation_section()
        self._build_demand_section()

    def _build_collapsible_section(self, parent, title, section_key):
        """Create a collapsible section header"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(15, 5))
        
        # Header button
        is_open = self.section_states[section_key]
        arrow = "▾" if is_open else "▸"
        btn = ctk.CTkButton(frame, text=f"{arrow} {title}", 
                           font=ctk.CTkFont(size=13, weight="bold"),
                           fg_color="transparent",
                           text_color=COLORS["accent"],
                           hover_color=COLORS["bg_dark"],
                           anchor="w",
                           command=lambda: self._toggle_section(section_key))
        btn.pack(fill="x", padx=5)
        
        # Content frame
        content = ctk.CTkFrame(parent, fg_color="transparent")
        if is_open:
            content.pack(fill="x", padx=10, pady=(0, 10))
        
        return content, btn

    def _toggle_section(self, section_key):
        """Toggle a collapsible section"""
        self.section_states[section_key] = not self.section_states[section_key]
        # Rebuild the entire left panel to reflect changes
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
        self._build_network_section()
        self._build_generation_section()
        self._build_demand_section()

    def _build_network_section(self):
        """Network/Lines section"""
        content, btn = self._build_collapsible_section(self.scroll_container, "NETWORK", "network")
        self.network_section_btn = btn
        
        if not self.section_states['network']:
            return
        
        # Column headers
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(5, 3))
        ctk.CTkLabel(header_frame, text="Line", width=70, 
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dim"], anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Cap (MW)", width=80,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dim"]).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Len (km)", width=80,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dim"]).pack(side="left")
        
        # Line entries
        self.line_vars = {}
        self.line_len_vars = {}
        for i, line in enumerate(self.param['lines']):
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            name = f"{line['from']}–{line['to']}"
            ctk.CTkLabel(row, text=name, width=70, anchor="w",
                        font=ctk.CTkFont(size=11),
                        text_color=COLORS["text_main"]).pack(side="left")
            
            cap_var = tk.DoubleVar(value=line['capacity'])
            self.line_vars[i] = cap_var
            e1 = ctk.CTkEntry(row, textvariable=cap_var, width=75, height=28,
                             border_width=1, fg_color=COLORS["bg_dark"],
                             border_color=COLORS["border"])
            e1.pack(side="left", padx=5)
            e1.bind("<Return>", lambda e: self._update_model())
            
            len_var = tk.DoubleVar(value=line.get('length', 100))
            self.line_len_vars[i] = len_var
            e2 = ctk.CTkEntry(row, textvariable=len_var, width=75, height=28,
                             border_width=1, fg_color=COLORS["bg_dark"],
                             border_color=COLORS["border"])
            e2.pack(side="left")
            e2.bind("<Return>", lambda e: self._update_model())

    def _build_generation_section(self):
        """Generation section"""
        content, btn = self._build_collapsible_section(self.scroll_container, "GENERATION", "generation")
        self.generation_section_btn = btn
        
        if not self.section_states['generation']:
            return
        
        # Column headers
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(5, 3))
        ctk.CTkLabel(header_frame, text="Node", width=50,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dim"], anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Max (MW)", width=80,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dim"]).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="€/MWh", width=80,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dim"]).pack(side="left")
        
        # Generation entries
        self.gen_cap_vars = {}
        self.gen_cost_vars = {}
        for node in self.param['nodes']:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(row, text=node, width=50, anchor="w",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_main"]).pack(side="left")
            
            cap_v = tk.DoubleVar(value=self.param['generation'][node]['capacity'])
            cost_v = tk.DoubleVar(value=self.param['generation'][node]['cost'])
            
            self.gen_cap_vars[node] = cap_v
            self.gen_cost_vars[node] = cost_v
            
            cap_e = ctk.CTkEntry(row, textvariable=cap_v, width=75, height=28,
                                border_width=1, fg_color=COLORS["bg_dark"],
                                border_color=COLORS["border"])
            cap_e.pack(side="left", padx=5)
            cap_e.bind("<Return>", lambda e: self._update_model())
            
            cost_e = ctk.CTkEntry(row, textvariable=cost_v, width=75, height=28,
                                 border_width=1, fg_color=COLORS["bg_dark"],
                                 border_color=COLORS["border"])
            cost_e.pack(side="left")
            cost_e.bind("<Return>", lambda e: self._update_model())

    def _build_demand_section(self):
        """Demand section"""
        content, btn = self._build_collapsible_section(self.scroll_container, "DEMAND", "demand")
        self.demand_section_btn = btn
        
        if not self.section_states['demand']:
            return
        
        # Demand entries
        self.demand_vars = {}
        for node in self.param['nodes']:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(row, text=f"{node}:", width=70, anchor="w",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_main"]).pack(side="left")
            
            var = tk.DoubleVar(value=self.param['consumption'][node])
            self.demand_vars[node] = var
            
            e = ctk.CTkEntry(row, textvariable=var, width=120, height=28,
                            border_width=1, fg_color=COLORS["bg_dark"],
                            border_color=COLORS["border"])
            e.pack(side="left", padx=5)
            e.bind("<Return>", lambda e: self._update_model())
            
            ctk.CTkLabel(row, text="MW", 
                        font=ctk.CTkFont(size=10),
                        text_color=COLORS["text_dim"]).pack(side="left")

    def _build_center_right_panel(self):
        """Center network canvas and right results panel"""
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=3)  # Network canvas
        main_content.grid_columnconfigure(1, weight=1)  # Results panel
        
        # === NETWORK CANVAS ===
        self.plot_container = ctk.CTkFrame(main_content, fg_color=COLORS["bg_card"],
                                          corner_radius=12, border_color=COLORS["border"],
                                          border_width=1)
        self.plot_container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Canvas title
        canvas_title = ctk.CTkLabel(self.plot_container, text="NETWORK CANVAS",
                                   font=ctk.CTkFont(size=14, weight="bold"),
                                   text_color=COLORS["text_dim"])
        canvas_title.pack(pady=(15, 5))
        
        # Embed plot
        self.network_plot.embed_in_frame(self.plot_container)
        
        # === RESULTS PANEL ===
        self._build_results_panel(main_content)

    def _build_results_panel(self, parent):
        """Right results panel with tabs"""
        results_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"],
                                    corner_radius=12, border_color=COLORS["border"],
                                    border_width=1)
        results_frame.grid(row=0, column=1, sticky="nsew")
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(results_frame, text="RESULTS & ANALYSIS",
                            font=ctk.CTkFont(size=14, weight="bold"),
                            text_color=COLORS["text_main"])
        header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        # Tab view
        self.results_tabview = ctk.CTkTabview(results_frame, 
                                             fg_color="transparent",
                                             segmented_button_fg_color=COLORS["bg_dark"],
                                             segmented_button_selected_color=COLORS["accent"],
                                             segmented_button_selected_hover_color=COLORS["accent_hover"])
        self.results_tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Add tabs
        self.results_tabview.add("Prices")
        self.results_tabview.add("Flows")
        self.results_tabview.add("Details")
        
        # Prices tab content
        self.prices_scroll = ctk.CTkScrollableFrame(self.results_tabview.tab("Prices"),
                                                    fg_color="transparent")
        self.prices_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.prices_label = ctk.CTkLabel(self.prices_scroll, text="Calculating...",
                                        font=ctk.CTkFont(family="Courier", size=11),
                                        justify="left", anchor="nw",
                                        text_color=COLORS["text_main"])
        self.prices_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Flows tab content
        self.flows_scroll = ctk.CTkScrollableFrame(self.results_tabview.tab("Flows"),
                                                   fg_color="transparent")
        self.flows_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.flows_label = ctk.CTkLabel(self.flows_scroll, text="Calculating...",
                                       font=ctk.CTkFont(family="Courier", size=11),
                                       justify="left", anchor="nw",
                                       text_color=COLORS["text_main"])
        self.flows_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Details tab content
        self.details_scroll = ctk.CTkScrollableFrame(self.results_tabview.tab("Details"),
                                                     fg_color="transparent")
        self.details_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.details_label = ctk.CTkLabel(self.details_scroll, text="Calculating...",
                                         font=ctk.CTkFont(family="Courier", size=11),
                                         justify="left", anchor="nw",
                                         text_color=COLORS["text_main"])
        self.details_label.pack(fill="both", expand=True, padx=5, pady=5)

    def _update_model(self, event=None):
        """Update the model and refresh all displays"""
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
            self._display_error(f"Error: {str(e)}")

    def _display_results(self, results):
        """Display results in header and tabs"""
        if not results['feasible']:
            self._display_error("Infeasible solution")
            return
        
        # === UPDATE HEADER ===
        total_cost = results['total_cost']
        total_demand = sum(self.network_data.consumption.values())
        total_shed = sum(results.get('shedding', {}).values())
        
        # Count active constraints (lines near capacity)
        active_constraints = 0
        for line_id, flow in results['flows'].items():
            capacity = results['capacities'][line_id]
            if capacity > 0 and abs(flow) / capacity > 0.95:
                active_constraints += 1
        
        # System status
        if total_shed > 0.1:
            status = "⚠ SCARCITY"
            status_color = COLORS["warning"]
        else:
            status = "✓ Healthy"
            status_color = COLORS["success"]
        
        self.status_text.configure(text=f"⚡ SYSTEM STATUS: {status}", 
                                  text_color=status_color)
        self.cost_text.configure(text=f"💶 Cost: €{total_cost:,.0f}/h")
        self.load_text.configure(text=f"⚡ Load: {total_demand:.0f} MW")
        self.constraints_text.configure(text=f"Active Constraints: {active_constraints}")
        
        # === UPDATE TABS ===
        self._update_prices_tab(results)
        self._update_flows_tab(results)
        self._update_details_tab(results)

    def _update_prices_tab(self, results):
        """Update the Prices tab"""
        text = ""
        energy_price = results['energy_price']
        
        text += f"ENERGY PRICE: €{energy_price:.2f}/MWh\n\n"
        text += "═" * 35 + "\n\n"
        
        for node in self.param['nodes']:
            lmp = results['lmp'][node]
            text += f"NODE {node}:\n"
            text += f"  LMP: €{lmp:>8.2f}/MWh\n"
            
            details = results['lmp_details'].get(node, {})
            line_details = details.get('line_details', [])
            
            if line_details:
                text += f"  Congestion Components:\n"
                for line_id, contrib in line_details:
                    text += f"    {line_id}: €{contrib:>+7.2f}\n"
            else:
                text += f"  No congestion\n"
            
            # Show shedding if any
            shed = results.get('shedding', {}).get(node, 0)
            if shed > 0.1:
                text += f"  ⚠ UNMET: {shed:.1f} MW\n"
            
            text += "\n"
        
        self.prices_label.configure(text=text)

    def _update_flows_tab(self, results):
        """Update the Flows tab"""
        text = ""
        
        for i, line in enumerate(self.param['lines']):
            line_id = f"{line['from']}→{line['to']}"
            flow = results['flows'][line_id]
            capacity = results['capacities'][line_id]
            util = (abs(flow) / capacity * 100) if capacity > 0 else 0
            
            text += f"LINE {line_id}:\n"
            
            if abs(flow) > capacity + 0.1:
                text += f"  ⚠ OVERLOAD ⚠\n"
            
            direction = "→" if flow >= 0 else "←"
            text += f"  Flow:     {flow:>7.2f} MW {direction}\n"
            text += f"  Capacity: {capacity:>7.2f} MW\n"
            text += f"  Util:     {util:>7.1f}%\n"
            
            # Generator breakdown
            gen_flows = results.get('generator_flows', {}).get(line_id, {})
            if gen_flows:
                text += f"  By Generator:\n"
                for gen_node, mw in gen_flows.items():
                    text += f"    {gen_node}: {mw:>+7.2f} MW\n"
            
            text += "\n"
        
        self.flows_label.configure(text=text)

    def _update_details_tab(self, results):
        """Update the Details tab with technical information"""
        text = ""
        
        text += "GENERATION DISPATCH:\n"
        text += "─" * 35 + "\n"
        for node in self.param['nodes']:
            gen = results['generation'][node]
            cap = self.network_data.generation[node]['capacity']
            cost = self.network_data.generation[node]['cost']
            if gen > 0.01:
                text += f"  {node}: {gen:>6.2f} MW / {cap:>6.2f} MW"
                text += f"  (@€{cost:.0f}/MWh)\n"
        
        text += "\n"
        text += "POWER TRANSFER DISTRIBUTION FACTORS:\n"
        text += "─" * 35 + "\n"
        ptdf = results['ptdf']
        for i, line in enumerate(self.param['lines']):
            line_id = f"{line['from']}→{line['to']}"
            text += f"  {line_id}: "
            for j, node in enumerate(self.param['nodes']):
                text += f"{node}:{ptdf[i][j]:+.3f} "
            text += "\n"
        
        text += "\n"
        text += "SYSTEM SUMMARY:\n"
        text += "─" * 35 + "\n"
        total_gen = sum(results['generation'].values())
        total_demand = sum(self.network_data.consumption.values())
        total_shed = sum(results.get('shedding', {}).values())
        text += f"  Total Generation: {total_gen:>6.2f} MW\n"
        text += f"  Total Demand:     {total_demand:>6.2f} MW\n"
        if total_shed > 0.01:
            text += f"  Load Shedding:    {total_shed:>6.2f} MW\n"
        text += f"  Total Cost:       €{results['total_cost']:>8.2f}/h\n"
        
        self.details_label.configure(text=text)

    def _display_error(self, message):
        """Display error message"""
        self.status_text.configure(text=f"⚠ ERROR: {message}", 
                                  text_color=COLORS["danger"])
        self.prices_label.configure(text=f"Error: {message}")
        self.flows_label.configure(text=f"Error: {message}")
        self.details_label.configure(text=f"Error: {message}")


if __name__ == "__main__":
    app = LMPAppV2(param)
    app.mainloop()


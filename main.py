"""
DC Power Flow Model for Illustrating Nodal Pricing (LMP)

Main entry point with parameters and GUI workflow.
"""

import tkinter as tk
from tkinter import ttk
from data import NetworkData
from func import DCPowerFlow
from plot import NetworkPlot


# =============================================================================
# Parameters
# =============================================================================
param = {
    # Network topology: 3-node example
    'nodes': ['A', 'B', 'C'],
    'lines': [
        {'from': 'A', 'to': 'B', 'reactance': 0.1, 'capacity': 100, 'length': 100},
        {'from': 'B', 'to': 'C', 'reactance': 0.1, 'capacity': 100, 'length': 100},
        {'from': 'A', 'to': 'C', 'reactance': 0.2, 'capacity': 50, 'length': 200},
    ],
    # Generation at each node (MW) and variable cost (€/MWh)
    'generation': {
        'A': {'capacity': 200, 'cost': 20},
        'B': {'capacity': 50, 'cost': 40},
        'C': {'capacity': 100, 'cost': 60},
    },
    # Demand at each node (MW)
    'consumption': {
        'A': 50,
        'B': 100,
        'C': 100,
    },
    # GUI settings
    'window_size': '1400x900',
    'update_interval': 100,  # ms
}


# =============================================================================
# GUI Application
# =============================================================================
class LMPApp:
    """
    GUI application for interactive DC power flow and LMP visualization.
    """
    
    def __init__(self, root, param):
        """
        Initialize the application.
        
        Parameters
        ----------
        root : tk.Tk
            Root window.
        param : dict
            Model parameters.
        """
        self.root = root
        self.param = param
        self.root.title("DC Power Flow - Nodal Pricing (LMP) Model")
        self.root.geometry(param['window_size'])
        
        # Initialize data and model
        self.network_data = NetworkData(param)
        self.dc_flow = DCPowerFlow(self.network_data)
        self.network_plot = NetworkPlot(self.network_data)
        
        # Build GUI
        self._build_gui()
        
        # Force window update
        self.root.update_idletasks()
        
        # Initial calculation and plot
        self._update_model()
    
    def _build_gui(self):
        """Build the GUI layout."""
        # Main frames
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.plot_frame = ttk.Frame(self.root, padding="10")
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Control sections
        self._build_line_controls()
        self._build_generation_controls()
        self._build_consumption_controls()
        self._build_results_display()
        
        # Plot area
        self.network_plot.embed_in_frame(self.plot_frame)
    
    def _build_line_controls(self):
        """Build controls for line capacities and lengths."""
        frame = ttk.LabelFrame(self.control_frame, text="Lines", padding="5")
        frame.pack(fill=tk.X, pady=5)
        
        # Header
        ttk.Label(frame, text="Line").grid(row=0, column=0, padx=5)
        ttk.Label(frame, text="Capacity (MW)").grid(row=0, column=1, padx=5)
        ttk.Label(frame, text="Length (km)").grid(row=0, column=2, padx=5)
        
        self.line_capacity_vars = {}
        self.line_length_vars = {}
        
        for i, line in enumerate(self.param['lines']):
            label = f"{line['from']} \u2192 {line['to']}"
            ttk.Label(frame, text=label).grid(row=i+1, column=0, sticky=tk.W, padx=5)
            
            # Capacity
            cap_var = tk.DoubleVar(value=line['capacity'])
            self.line_capacity_vars[i] = cap_var
            cap_entry = ttk.Entry(frame, textvariable=cap_var, width=8)
            cap_entry.grid(row=i+1, column=1, padx=5)
            cap_entry.bind('<Return>', lambda e, idx=i: self._on_line_change(idx))
            
            # Length
            len_var = tk.DoubleVar(value=line.get('length', 100))
            self.line_length_vars[i] = len_var
            len_entry = ttk.Entry(frame, textvariable=len_var, width=8)
            len_entry.grid(row=i+1, column=2, padx=5)
            len_entry.bind('<Return>', lambda e, idx=i: self._on_line_change(idx))
        
        update_btn = ttk.Button(frame, text="Update Lines", command=self._update_all_lines)
        update_btn.grid(row=len(self.param['lines'])+1, column=0, columnspan=3, pady=5)
    
    def _build_generation_controls(self):
        """Build controls for generation capacity and cost."""
        frame = ttk.LabelFrame(self.control_frame, text="Generation", padding="5")
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Node").grid(row=0, column=0, padx=5)
        ttk.Label(frame, text="Capacity (MW)").grid(row=0, column=1, padx=5)
        ttk.Label(frame, text="Cost (€/MWh)").grid(row=0, column=2, padx=5)
        
        self.gen_capacity_vars = {}
        self.gen_cost_vars = {}
        
        for i, node in enumerate(self.param['nodes']):
            ttk.Label(frame, text=node).grid(row=i+1, column=0, padx=5)
            
            cap_var = tk.DoubleVar(value=self.param['generation'][node]['capacity'])
            self.gen_capacity_vars[node] = cap_var
            cap_entry = ttk.Entry(frame, textvariable=cap_var, width=8)
            cap_entry.grid(row=i+1, column=1, padx=5)
            cap_entry.bind('<Return>', lambda e: self._update_model())
            
            cost_var = tk.DoubleVar(value=self.param['generation'][node]['cost'])
            self.gen_cost_vars[node] = cost_var
            cost_entry = ttk.Entry(frame, textvariable=cost_var, width=8)
            cost_entry.grid(row=i+1, column=2, padx=5)
            cost_entry.bind('<Return>', lambda e: self._update_model())
        
        update_btn = ttk.Button(frame, text="Update", command=self._update_model)
        update_btn.grid(row=len(self.param['nodes'])+1, column=0, columnspan=3, pady=5)
    
    def _build_consumption_controls(self):
        """Build controls for demand at each node."""
        frame = ttk.LabelFrame(self.control_frame, text="Demand (MW)", padding="5")
        frame.pack(fill=tk.X, pady=5)
        
        self.consumption_vars = {}
        
        for i, node in enumerate(self.param['nodes']):
            ttk.Label(frame, text=node).grid(row=i, column=0, sticky=tk.W, padx=5)
            
            var = tk.DoubleVar(value=self.param['consumption'][node])
            self.consumption_vars[node] = var
            
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.grid(row=i, column=1, padx=5)
            entry.bind('<Return>', lambda e, n=node: self._on_consumption_change(n))
            
            ttk.Label(frame, text="MW").grid(row=i, column=2, sticky=tk.W, padx=2)
        
        update_btn = ttk.Button(frame, text="Update Demand", command=self._update_all_consumption)
        update_btn.grid(row=len(self.param['nodes']), column=0, columnspan=3, pady=5)
    
    def _update_all_consumption(self):
        """Update all consumption values."""
        for node in self.param['nodes']:
            consumption = self.consumption_vars[node].get()
            self.network_data.update_consumption(node, consumption)
        self._update_model()
    
    def _build_results_display(self):
        """Build display area for results."""
        frame = ttk.LabelFrame(self.control_frame, text="Results", padding="5")
        frame.pack(fill=tk.X, pady=5)
        
        self.results_text = tk.Text(frame, height=15, width=35, font=('Courier', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
    
    def _on_line_change(self, line_idx):
        """Handle line capacity or length change."""
        capacity = self.line_capacity_vars[line_idx].get()
        length = self.line_length_vars[line_idx].get()
        self.network_data.update_line_capacity(line_idx, capacity)
        self.network_data.update_line_length(line_idx, length)
        self._update_model()
    
    def _update_all_lines(self):
        """Update all line parameters."""
        for i in range(len(self.param['lines'])):
            self._on_line_change(i)
    
    def _on_consumption_change(self, node):
        """Handle consumption change."""
        consumption = self.consumption_vars[node].get()
        self.network_data.update_consumption(node, consumption)
        self._update_model()
    
    def _update_model(self):
        """Update generation and costs from GUI, recalculate, and refresh plot."""
        # Update generation data
        for node in self.param['nodes']:
            capacity = self.gen_capacity_vars[node].get()
            cost = self.gen_cost_vars[node].get()
            self.network_data.update_generation(node, capacity, cost)
        
        # Solve DC power flow
        results = self.dc_flow.solve()
        
        # Update results display
        self._display_results(results)
        
        # Update plot
        self.network_plot.update(results)
    
    def _display_results(self, results):
        """Display calculation results."""
        self.results_text.delete('1.0', tk.END)
        
        if not results['feasible']:
            self.results_text.insert(tk.END, "⚠ INFEASIBLE SOLUTION\n\n")
            self._show_infeasibility_explanation(results)
            return
        
        self.results_text.insert(tk.END, "═══ LMPs (€/MWh) ═══\n")
        for node, lmp in results['lmp'].items():
            self.results_text.insert(tk.END, f"  {node}: {lmp:.2f}\n")
        
        self.results_text.insert(tk.END, "\n═══ Generation (MW) ═══\n")
        for node, gen in results['generation'].items():
            self.results_text.insert(tk.END, f"  {node}: {gen:.1f}\n")
        
        self.results_text.insert(tk.END, "\n═══ Line Flows (MW) ═══\n")
        for line_id, flow in results['flows'].items():
            capacity = results['capacities'][line_id]
            utilization = abs(flow) / capacity * 100 if capacity > 0 else 0
            congested = "⚡" if utilization >= 99.9 else ""
            self.results_text.insert(tk.END, f"  {line_id}: {flow:+.1f} ({utilization:.0f}%) {congested}\n")
        
        self.results_text.insert(tk.END, f"\n═══ Total Cost ═══\n")
        self.results_text.insert(tk.END, f"  {results['total_cost']:.2f} €/h\n")
    
    def _show_infeasibility_explanation(self, results):
        """Show detailed explanation of why the solution is infeasible."""
        analysis = results.get('infeasibility_analysis', {})
        causes = analysis.get('causes', ['Unknown cause'])
        details = analysis.get('details', [])
        suggestions = analysis.get('suggestions', [])
        
        # Show summary in results panel
        self.results_text.insert(tk.END, "Click 'Why Infeasible?' for details.\n\n")
        
        for i, cause in enumerate(causes):
            self.results_text.insert(tk.END, f"• {cause}\n")
        
        # Create popup window with full explanation
        self._create_infeasibility_popup(causes, details, suggestions)
    
    def _create_infeasibility_popup(self, causes, details, suggestions):
        """Create a popup window explaining infeasibility."""
        popup = tk.Toplevel(self.root)
        popup.title("Infeasibility Analysis")
        popup.geometry("500x450")
        popup.configure(bg='white')
        
        # Header
        header = tk.Label(popup, text="⚠ Why is this configuration infeasible?",
                         font=('Arial', 14, 'bold'), bg='white', fg='#D26A5E')
        header.pack(pady=(15, 10), padx=15, anchor='w')
        
        # Scrollable content
        content_frame = ttk.Frame(popup)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        text_widget = tk.Text(content_frame, wrap=tk.WORD, font=('Arial', 11),
                             bg='#FAFAFA', relief=tk.FLAT, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for formatting
        text_widget.tag_configure('cause', font=('Arial', 12, 'bold'), foreground='#D26A5E')
        text_widget.tag_configure('section', font=('Arial', 11, 'bold'), foreground='#4B8246')
        text_widget.tag_configure('normal', font=('Arial', 11), foreground='#333333')
        
        # Add content
        for i, cause in enumerate(causes):
            text_widget.insert(tk.END, f"\n{cause}\n", 'cause')
            
            if i < len(details):
                text_widget.insert(tk.END, "\nDetails:\n", 'section')
                text_widget.insert(tk.END, f"{details[i]}\n", 'normal')
            
            if i < len(suggestions):
                text_widget.insert(tk.END, "\nHow to fix:\n", 'section')
                text_widget.insert(tk.END, f"{suggestions[i]}\n", 'normal')
            
            text_widget.insert(tk.END, "\n" + "─" * 50 + "\n", 'normal')
        
        text_widget.configure(state=tk.DISABLED)
        
        # Close button
        close_btn = ttk.Button(popup, text="Close", command=popup.destroy)
        close_btn.pack(pady=15)
        
        # Center popup on parent window
        popup.transient(self.root)
        popup.grab_set()


# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = LMPApp(root, param)
    root.mainloop()
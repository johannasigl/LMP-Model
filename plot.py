"""
Network Visualization

Contains plotting functionality for the DC power flow network
and LMP visualization using plotting_standards.
"""

import matplotlib
matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import plotting_standards as ps


class NetworkPlot:
    """
    Network visualization with LMP coloring and generator flow paths.
    
    Displays:
    - Nodes with LMP prices and demand
    - Lines colored by utilization (load)
    - Generator flows as dashed colored lines showing power split
    """
    
    def __init__(self, network_data):
        """
        Initialize the network plot.
        
        Parameters
        ----------
        network_data : NetworkData
            Network data object.
        """
        self.network = network_data
        self.fig = None
        self.ax = None
        self.canvas = None
        ps.setup_plotting_standards()
    
    def embed_in_frame(self, frame):
        """
        Embed the plot in a tkinter frame.
        
        Parameters
        ----------
        frame : ttk.Frame
            Frame to embed the plot in.
        """
        # Increased figure size for clarity
        self.fig, self.ax = plt.subplots(figsize=(13, 10))
        self.fig.patch.set_facecolor('white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self._setup_axes()
        self.canvas.draw()
    
    def _setup_axes(self):
        """Set up axes properties."""
        self.ax.set_xlim(-2.0, 2.0)
        self.ax.set_ylim(-2.0, 2.0)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_title('DC Power Flow - Nodal Pricing', fontsize=14, fontweight='light')
    
    def update(self, results):
        """
        Update the plot with new results.
        
        Parameters
        ----------
        results : dict
            Results dictionary from DC power flow solver.
        """
        self.ax.clear()
        self._setup_axes()
        
        self._draw_generator_flows(results)
        self._draw_lines(results)
        self._draw_nodes(results)
        self._draw_legend(results)
        
        self.canvas.draw()
    
    def _draw_nodes(self, results):
        """
        Draw nodes with LMP display and demand info.
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        positions = self.network.node_positions
        lmps = results['lmp']
        generation = results['generation']
        
        for node in self.network.nodes:
            x, y = positions[node]
            lmp = lmps[node]
            gen = generation[node]
            demand = self.network.consumption[node]
            gen_cap = self.network.generation[node]['capacity']
            gen_cost = self.network.generation[node]['cost']
            gen_color = self.network.generator_colors[node]
            
            node_size = 0.22
            circle = Circle((x, y), node_size, facecolor='white', 
                           edgecolor='#595959', linewidth=2, zorder=20)
            self.ax.add_patch(circle)
            
            self.ax.text(x, y, node, ha='center', va='center', 
                        fontsize=14, fontweight='bold', color='#595959', zorder=21)
            
            self.ax.text(x, y - node_size - 0.12, f'{lmp:.1f} EUR/MWh',
                        ha='center', va='top', fontsize=10, fontweight='bold',
                        color='#4B8246', zorder=21)
            
            self.ax.text(x, y - node_size - 0.28, f'D: {demand:.0f} MW',
                        ha='center', va='top', fontsize=9, color='#595959', zorder=21)
            
            if gen_cap > 0:
                gen_text = f'G: {gen:.0f}/{gen_cap:.0f} MW\n@ {gen_cost:.0f} EUR/MWh'
                self.ax.text(x, y + node_size + 0.08, gen_text,
                            ha='center', va='bottom', fontsize=8, color=gen_color,
                            fontweight='bold', linespacing=1.1, zorder=21)
                
                sq_size = 0.06
                sq = plt.Rectangle((x - sq_size/2, y + node_size + 0.02), 
                                   sq_size, sq_size, facecolor=gen_color, 
                                   edgecolor='none', zorder=21)
                self.ax.add_patch(sq)
    
    def _draw_lines(self, results):
        """
        Draw lines colored by utilization (load).
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        positions = self.network.node_positions
        flows = results['flows']
        capacities = results['capacities']
        
        for line in self.network.lines:
            from_node = line['from']
            to_node = line['to']
            line_id = f"{from_node}\u2192{to_node}"
            x1, y1 = positions[from_node]
            x2, y2 = positions[to_node]
            flow = flows.get(line_id, 0)
            capacity = capacities.get(line_id, line['capacity'])
            length = line.get('length', 100)
            utilization = abs(flow) / capacity if capacity > 0 else 0
            if utilization >= 0.99:
                line_color = '#D26A5E'
                line_width = 6
            elif utilization >= 0.8:
                line_color = '#FFD966'
                line_width = 5
            elif utilization >= 0.5:
                line_color = '#BAD1AC'
                line_width = 4
            else:
                line_color = '#D9D9D9'
                line_width = 3
            node_radius = 0.22
            dx = x2 - x1
            dy = y2 - y1
            line_length = np.sqrt(dx**2 + dy**2)
            if line_length > 0:
                dx_norm = dx / line_length
                dy_norm = dy / line_length
                x1_off = x1 + dx_norm * node_radius
                y1_off = y1 + dy_norm * node_radius
                x2_off = x2 - dx_norm * node_radius
                y2_off = y2 - dy_norm * node_radius
            else:
                x1_off, y1_off, x2_off, y2_off = x1, y1, x2, y2
                dx_norm, dy_norm = 0, 0
            self.ax.plot([x1_off, x2_off], [y1_off, y2_off], 
                        color=line_color, linewidth=line_width, 
                        solid_capstyle='round', zorder=5)
            # Move label further from line (increase offset)
            mid_x = (x1_off + x2_off) / 2
            mid_y = (y1_off + y2_off) / 2
            perp_x = -dy_norm * 0.35  # increased offset
            perp_y = dx_norm * 0.35
            label_text = f'{abs(flow):.0f}/{capacity:.0f} MW\n{length:.0f} km'
            self.ax.text(mid_x + perp_x, mid_y + perp_y, label_text,
                        ha='center', va='center', fontsize=8, color='#595959',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                                 edgecolor='#CCCCCC', alpha=0.9),
                        zorder=15)
    
    def _draw_generator_flows(self, results):
        """
        Draw generator flow contributions as dashed colored lines.
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        if not results['feasible']:
            return
            
        positions = self.network.node_positions
        generator_flows = results.get('generator_flows', {})
        
        # Show all generators, even if only one is active
        all_generators = [node for node in self.network.nodes if self.network.generation[node]['capacity'] > 0]
        n_generators = len(all_generators)
        if n_generators == 0:
            return
        for line in self.network.lines:
            from_node = line['from']
            to_node = line['to']
            line_id = f"{from_node}\u2192{to_node}"
            x1, y1 = positions[from_node]
            x2, y2 = positions[to_node]
            dx = x2 - x1
            dy = y2 - y1
            line_length = np.sqrt(dx**2 + dy**2)
            if line_length == 0:
                continue
            dx_norm = dx / line_length
            dy_norm = dy / line_length
            perp_x = -dy_norm
            perp_y = dx_norm
            node_radius = 0.22
            x1_base = x1 + dx_norm * (node_radius + 0.05)
            y1_base = y1 + dy_norm * (node_radius + 0.05)
            x2_base = x2 - dx_norm * (node_radius + 0.05)
            y2_base = y2 - dy_norm * (node_radius + 0.05)
            gen_line_flows = generator_flows.get(line_id, {})
            offset_spacing = 0.08
            total_width = (n_generators - 1) * offset_spacing
            start_offset = -total_width / 2
            for i, gen_node in enumerate(all_generators):
                flow = gen_line_flows.get(gen_node, 0)
                if abs(flow) < 0.1:
                    continue
                gen_color = self.network.generator_colors[gen_node]
                offset = start_offset + i * offset_spacing
                x1_off = x1_base + perp_x * offset
                y1_off = y1_base + perp_y * offset
                x2_off = x2_base + perp_x * offset
                y2_off = y2_base + perp_y * offset
                # Thinner dashed lines for generator flows
                line_width = 1.2
                # Animated dashes: use a dash pattern and phase that changes each update
                # Use a static phase for now (animation in matplotlib+tkinter is nontrivial)
                dash_pattern = (4, 8)
                if flow >= 0:
                    self.ax.plot([x1_off, x2_off], [y1_off, y2_off],
                                 color=gen_color, linewidth=line_width, linestyle=(0, dash_pattern),
                                 zorder=3, alpha=0.9)
                else:
                    self.ax.plot([x2_off, x1_off], [y2_off, y1_off],
                                 color=gen_color, linewidth=line_width, linestyle=(0, dash_pattern),
                                 zorder=3, alpha=0.9)
    
    def _draw_legend(self, results):
        """
        Draw legends for line utilization and generator colors.
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        util_elements = [
            plt.Line2D([0], [0], color='#D9D9D9', linewidth=4, label='<50%'),
            plt.Line2D([0], [0], color='#BAD1AC', linewidth=4, label='50-80%'),
            plt.Line2D([0], [0], color='#FFD966', linewidth=5, label='80-99%'),
            plt.Line2D([0], [0], color='#D26A5E', linewidth=6, label='100% (congested)'),
        ]
        
        leg1 = self.ax.legend(handles=util_elements, loc='lower right', 
                             framealpha=0.95, fontsize=8, title='Line Load',
                             title_fontsize=9)
        self.ax.add_artist(leg1)
        
        gen_elements = []
        for node in self.network.nodes:
            gen = results['generation'].get(node, 0)
            if gen > 0.1:
                color = self.network.generator_colors[node]
                gen_elements.append(
                    plt.Line2D([0], [0], color=color, linewidth=2, 
                              linestyle='--', label=f'Gen {node}')
                )
        
        if gen_elements:
            self.ax.legend(handles=gen_elements, loc='lower left',
                          framealpha=0.95, fontsize=8, title='Generator Flows',
                          title_fontsize=9)
        
        if not results['feasible']:
            self.ax.text(0, 0, 'INFEASIBLE', ha='center', va='center',
                        fontsize=24, color='red', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                                 edgecolor='red', linewidth=3),
                        zorder=100)
"""
Network Visualization

Contains plotting functionality for the DC power flow network
and LMP visualization using plotting_standards.
"""

import matplotlib
matplotlib.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import plotting_standards as ps


class NetworkPlot:
    """
    Network visualization with LMP coloring and generator flow paths.
    
    Displays:
    - Nodes with LMP prices and demand
    - Lines colored by utilization (load)
    - Generator flows as dashed colored lines showing power split
    """
    
    def __init__(self, network_data):
        """
        Initialize the network plot.
        
        Parameters
        ----------
        network_data : NetworkData
            Network data object.
        """
        self.network = network_data
        self.fig = None
        self.ax = None
        self.canvas = None
        
        ps.setup_plotting_standards()
    
    def embed_in_frame(self, frame):
        """
        Embed the plot in a tkinter frame.
        
        Parameters
        ----------
        frame : ttk.Frame
            Frame to embed the plot in.
        """
        # Increased figure size for clarity
        self.fig, self.ax = plt.subplots(figsize=(13, 10))
        self.fig.patch.set_facecolor('white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self._setup_axes()
        self.canvas.draw()
    
    def _setup_axes(self):
        """Set up axes properties."""
        self.ax.set_xlim(-2.0, 2.0)
        self.ax.set_ylim(-2.0, 2.0)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_title('DC Power Flow - Nodal Pricing', fontsize=14, fontweight='light')
    
    def update(self, results):
        """
        Update the plot with new results.
        
        Parameters
        ----------
        results : dict
            Results dictionary from DC power flow solver.
        """
        self.ax.clear()
        self._setup_axes()
        
        self._draw_generator_flows(results)
        self._draw_lines(results)
        self._draw_nodes(results)
        self._draw_legend(results)
        
        self.canvas.draw()
    
    def _draw_nodes(self, results):
        """
        Draw nodes with LMP display and demand info.
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        positions = self.network.node_positions
        lmps = results['lmp']
        generation = results['generation']
        
        for node in self.network.nodes:
            x, y = positions[node]
            lmp = lmps[node]
            gen = generation[node]
            demand = self.network.consumption[node]
            gen_cap = self.network.generation[node]['capacity']
            gen_cost = self.network.generation[node]['cost']
            gen_color = self.network.generator_colors[node]
            
            node_size = 0.22
            circle = Circle((x, y), node_size, facecolor='white', 
                           edgecolor='#595959', linewidth=2, zorder=20)
            self.ax.add_patch(circle)
            
            self.ax.text(x, y, node, ha='center', va='center', 
                        fontsize=14, fontweight='bold', color='#595959', zorder=21)
            
            self.ax.text(x, y - node_size - 0.12, f'{lmp:.1f} EUR/MWh',
                        ha='center', va='top', fontsize=10, fontweight='bold',
                        color='#4B8246', zorder=21)
            
            self.ax.text(x, y - node_size - 0.28, f'D: {demand:.0f} MW',
                        ha='center', va='top', fontsize=9, color='#595959', zorder=21)
            
            if gen_cap > 0:
                gen_text = f'G: {gen:.0f}/{gen_cap:.0f} MW\n@ {gen_cost:.0f} EUR/MWh'
                self.ax.text(x, y + node_size + 0.08, gen_text,
                            ha='center', va='bottom', fontsize=8, color=gen_color,
                            fontweight='bold', linespacing=1.1, zorder=21)
                
                sq_size = 0.06
                sq = plt.Rectangle((x - sq_size/2, y + node_size + 0.02), 
                                   sq_size, sq_size, facecolor=gen_color, 
                                   edgecolor='none', zorder=21)
                self.ax.add_patch(sq)
    
    def _draw_lines(self, results):
        """
        Draw lines colored by utilization (load).
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        positions = self.network.node_positions
        flows = results['flows']
        capacities = results['capacities']
        
        for line in self.network.lines:
            from_node = line['from']
            to_node = line['to']
            line_id = f"{from_node}\u2192{to_node}"
            x1, y1 = positions[from_node]
            x2, y2 = positions[to_node]
            flow = flows.get(line_id, 0)
            capacity = capacities.get(line_id, line['capacity'])
            length = line.get('length', 100)
            utilization = abs(flow) / capacity if capacity > 0 else 0
            if utilization >= 0.99:
                line_color = '#D26A5E'
                line_width = 6
            elif utilization >= 0.8:
                line_color = '#FFD966'
                line_width = 5
            elif utilization >= 0.5:
                line_color = '#BAD1AC'
                line_width = 4
            else:
                line_color = '#D9D9D9'
                line_width = 3
            node_radius = 0.22
            dx = x2 - x1
            dy = y2 - y1
            line_length = np.sqrt(dx**2 + dy**2)
            if line_length > 0:
                dx_norm = dx / line_length
                dy_norm = dy / line_length
                x1_off = x1 + dx_norm * node_radius
                y1_off = y1 + dy_norm * node_radius
                x2_off = x2 - dx_norm * node_radius
                y2_off = y2 - dy_norm * node_radius
            else:
                x1_off, y1_off, x2_off, y2_off = x1, y1, x2, y2
                dx_norm, dy_norm = 0, 0
            self.ax.plot([x1_off, x2_off], [y1_off, y2_off], 
                        color=line_color, linewidth=line_width, 
                        solid_capstyle='round', zorder=5)
            # Move label further from line (increase offset)
            mid_x = (x1_off + x2_off) / 2
            mid_y = (y1_off + y2_off) / 2
            perp_x = -dy_norm * 0.35  # increased offset
            perp_y = dx_norm * 0.35
            label_text = f'{abs(flow):.0f}/{capacity:.0f} MW\n{length:.0f} km'
            self.ax.text(mid_x + perp_x, mid_y + perp_y, label_text,
                        ha='center', va='center', fontsize=8, color='#595959',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                                 edgecolor='#CCCCCC', alpha=0.9),
                        zorder=15)
    
    def _draw_generator_flows(self, results):
        """
        Draw generator flow contributions as dashed colored lines.
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        if not results['feasible']:
            return
            
        positions = self.network.node_positions
        generator_flows = results.get('generator_flows', {})
        
        # Show all generators, even if only one is active
        all_generators = [node for node in self.network.nodes if self.network.generation[node]['capacity'] > 0]
        n_generators = len(all_generators)
        if n_generators == 0:
            return
        for line in self.network.lines:
            from_node = line['from']
            to_node = line['to']
            line_id = f"{from_node}\u2192{to_node}"
            x1, y1 = positions[from_node]
            x2, y2 = positions[to_node]
            dx = x2 - x1
            dy = y2 - y1
            line_length = np.sqrt(dx**2 + dy**2)
            if line_length == 0:
                continue
            dx_norm = dx / line_length
            dy_norm = dy / line_length
            perp_x = -dy_norm
            perp_y = dx_norm
            node_radius = 0.22
            x1_base = x1 + dx_norm * (node_radius + 0.05)
            y1_base = y1 + dy_norm * (node_radius + 0.05)
            x2_base = x2 - dx_norm * (node_radius + 0.05)
            y2_base = y2 - dy_norm * (node_radius + 0.05)
            gen_line_flows = generator_flows.get(line_id, {})
            offset_spacing = 0.08
            total_width = (n_generators - 1) * offset_spacing
            start_offset = -total_width / 2
            for i, gen_node in enumerate(all_generators):
                flow = gen_line_flows.get(gen_node, 0)
                if abs(flow) < 0.1:
                    continue
                gen_color = self.network.generator_colors[gen_node]
                offset = start_offset + i * offset_spacing
                x1_off = x1_base + perp_x * offset
                y1_off = y1_base + perp_y * offset
                x2_off = x2_base + perp_x * offset
                y2_off = y2_base + perp_y * offset
                # Thinner dashed lines for generator flows
                line_width = 1.2
                # Animated dashes: use a dash pattern and phase that changes each update
                # Use a static phase for now (animation in matplotlib+tkinter is nontrivial)
                dash_pattern = (4, 8)
                if flow >= 0:
                    self.ax.plot([x1_off, x2_off], [y1_off, y2_off],
                                 color=gen_color, linewidth=line_width, linestyle=(0, dash_pattern),
                                 zorder=3, alpha=0.9)
                else:
                    self.ax.plot([x2_off, x1_off], [y2_off, y1_off],
                                 color=gen_color, linewidth=line_width, linestyle=(0, dash_pattern),
                                 zorder=3, alpha=0.9)
    
    def _draw_legend(self, results):
        """
        Draw legends for line utilization and generator colors.
        
        Parameters
        ----------
        results : dict
            Results dictionary.
        """
        util_elements = [
            plt.Line2D([0], [0], color='#D9D9D9', linewidth=4, label='<50%'),
            plt.Line2D([0], [0], color='#BAD1AC', linewidth=4, label='50-80%'),
            plt.Line2D([0], [0], color='#FFD966', linewidth=5, label='80-99%'),
            plt.Line2D([0], [0], color='#D26A5E', linewidth=6, label='100% (congested)'),
        ]
        
        leg1 = self.ax.legend(handles=util_elements, loc='lower right', 
                             framealpha=0.95, fontsize=8, title='Line Load',
                             title_fontsize=9)
        self.ax.add_artist(leg1)
        
        gen_elements = []
        for node in self.network.nodes:
            gen = results['generation'].get(node, 0)
            if gen > 0.1:
                color = self.network.generator_colors[node]
                gen_elements.append(
                    plt.Line2D([0], [0], color=color, linewidth=2, 
                              linestyle='--', label=f'Gen {node}')
                )
        
        if gen_elements:
            self.ax.legend(handles=gen_elements, loc='lower left',
                          framealpha=0.95, fontsize=8, title='Generator Flows',
                          title_fontsize=9)
        
        if not results['feasible']:
            self.ax.text(0, 0, 'INFEASIBLE', ha='center', va='center',
                        fontsize=24, color='red', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                                 edgecolor='red', linewidth=3),
                        zorder=100)

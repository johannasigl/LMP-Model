import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import plotting_standards as ps

class NetworkPlot:
    def __init__(self, network_data):
        self.network = network_data
        self.fig = None
        self.ax = None
        self.canvas = None
        self.last_results = None
        ps.setup_plotting_standards()
    
    def embed_in_frame(self, frame):
        self.fig, self.ax = plt.subplots(figsize=(10, 8), dpi=100)
        self.fig.patch.set_facecolor('#ffffff')
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True)
        self._setup_axes()
        self._redraw_all()
    
    def _setup_axes(self):
        pos = list(self.network.node_positions.values())
        x_coords, y_coords = zip(*pos)
        padding = 1.0
        self.ax.set_xlim(min(x_coords) - padding, max(x_coords) + padding)
        self.ax.set_ylim(min(y_coords) - padding, max(y_coords) + padding)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

    def update(self, results):
        self.last_results = results
        self._redraw_all()

    def _redraw_all(self):
        if not self.last_results: return
        self.ax.clear()
        self._setup_axes()
        
        # 1. Background Grid (Static Lines)
        self._draw_static_lines(self.last_results)
        
        # 2. Moving Generator-Specific Flows
        self._draw_generator_flows(self.last_results)
        
        # 3. Nodes and Prices
        self._draw_nodes(self.last_results)
        self.canvas.draw_idle()

    def _draw_static_lines(self, results):
        """Draws a base grey 'pipe' for each transmission line with length and capacity info."""
        for line in self.network.lines:
            u, v = line['from'], line['to']
            x1, y1 = self.network.node_positions[u]
            x2, y2 = self.network.node_positions[v]
            
            # Draw the line
            self.ax.plot([x1, x2], [y1, y2], color='#f0f0f0', linewidth=10, solid_capstyle='round', zorder=1)
            
            # Line info text (Length and Capacity)
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            angle = np.degrees(np.arctan2(dy, dx))
            if angle > 90: angle -= 180
            if angle < -90: angle += 180
            
            # Offset the text slightly from the line
            perp_dx, perp_dy = -dy/np.sqrt(dx**2+dy**2), dx/np.sqrt(dx**2+dy**2)
            offset = 0.15
            
            info_text = f"{line['capacity']}MW | {line['length']}km"
            self.ax.text(mid_x + perp_dx*offset, mid_y + perp_dy*offset, info_text, 
                         ha='center', va='center', rotation=angle, fontsize=8, color='#7f8c8d',
                         bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))

    def _draw_generator_flows(self, results):
        """
        Draws generator flows as lines with triangle markers indicating direction.
        Each color = power from a specific generator node.
        """
        gen_flows = results.get('generator_flows', {}) # Expected format: {line_id: {gen_node: MW}}
        all_gens = [n for n in self.network.nodes if self.network.generation[n]['capacity'] > 0]
        
        for line in self.network.lines:
            u, v = line['from'], line['to']
            line_id = f"{u}\u2192{v}"
            x1, y1 = self.network.node_positions[u]
            x2, y2 = self.network.node_positions[v]
            
            # Line Geometry
            dx, dy = x2 - x1, y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            if length == 0: continue
            perp_x, perp_y = -dy/length, dx/length
            
            # Find all generators contributing to this line
            contributions = []
            for gen in all_gens:
                val = gen_flows.get(line_id, {}).get(gen, 0)
                if abs(val) > 0.1: # Only plot significant flows
                    contributions.append((gen, val))
            
            # Draw a separate parallel line for each generator's power contribution
            n_parallel = len(contributions)
            spacing = 0.08
            start_offset = -(n_parallel - 1) * spacing / 2

            for i, (gen_node, mw_val) in enumerate(contributions):
                color = self.network.generator_colors.get(gen_node, 'black')
                offset = start_offset + (i * spacing)
                
                # Visual scaling
                line_width = 1.5 + (abs(mw_val) / 50) * 5 # More MW = thicker line
                
                # CRITICAL: Direction
                # If mw_val is +, power goes from U to V.
                # If mw_val is -, power goes from V to U.
                direction = np.sign(mw_val)
                
                # Add arrow markers with better visibility
                if direction > 0:
                    start_pos = [x1 + perp_x*offset, y1 + perp_y*offset]
                    end_pos = [x2 + perp_x*offset, y2 + perp_y*offset]
                    self.ax.plot([start_pos[0], end_pos[0]], [start_pos[1], end_pos[1]],
                                 color=color, linewidth=line_width, linestyle='-', zorder=10)
                    
                    # Add arrows along the line
                    n_arrows = 3
                    for a in range(1, n_arrows):
                        frac = a / n_arrows
                        arrow_x = x1 + frac * dx + perp_x*offset
                        arrow_y = y1 + frac * dy + perp_y*offset
                        self.ax.annotate('', xy=(arrow_x + 0.05*dx/length, arrow_y + 0.05*dy/length), 
                                         xytext=(arrow_x, arrow_y),
                                         arrowprops=dict(arrowstyle='->', color=color, lw=line_width, mutation_scale=15),
                                         zorder=11)
                else:
                    start_pos = [x2 + perp_x*offset, y2 + perp_y*offset]
                    end_pos = [x1 + perp_x*offset, y1 + perp_y*offset]
                    self.ax.plot([start_pos[0], end_pos[0]], [start_pos[1], end_pos[1]],
                                 color=color, linewidth=line_width, linestyle='-', zorder=10)

                    # Add arrows along the line (reverse direction)
                    n_arrows = 3
                    for a in range(1, n_arrows):
                        frac = a / n_arrows
                        arrow_x = x2 - frac * dx + perp_x*offset
                        arrow_y = y2 - frac * dy + perp_y*offset
                        self.ax.annotate('', xy=(arrow_x - 0.05*dx/length, arrow_y - 0.05*dy/length), 
                                         xytext=(arrow_x, arrow_y),
                                         arrowprops=dict(arrowstyle='->', color=color, lw=line_width, mutation_scale=15),
                                         zorder=11)

    def _draw_nodes(self, results):
        """Draws nodes with labels, price tags, and generation legend."""
        for node in self.network.nodes:
            x, y = self.network.node_positions[node]
            # White node circle
            self.ax.add_patch(Circle((x, y), 0.25, facecolor='white', edgecolor='#333', lw=2, zorder=20))
            self.ax.text(x, y, node, ha='center', va='center', fontweight='bold', fontsize=12, zorder=21)
            
            # LMP Text (above the node)
            lmp = results['lmp'][node]
            self.ax.text(x, y + 0.45, f"LMP: €{lmp:.2f}", ha='center', fontsize=10, fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', fc='#ecf0f1', ec='#27ae60', lw=1.5, alpha=1.0), zorder=25)
            
            # Generation Legend (below the node)
            gen_val = results['generation'][node]
            gen_cost = self.network.generation[node]['cost']
            gen_cap = self.network.generation[node]['capacity']
            
            # Individual color for generator
            c = self.network.generator_colors.get(node, 'black')
            
            legend_text = f"GEN: {gen_val:.1f} MW\nCost: {gen_cost:.1f} €/MWh\nMax: {gen_cap:.1f} MW"
            self.ax.text(x, y - 0.7, legend_text, ha='center', va='top', fontsize=9,
                         bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=c, lw=2, alpha=0.9), zorder=25)
            
            # Small color indicator dot on the node
            if gen_cap > 0:
                self.ax.add_patch(Circle((x + 0.18, y + 0.18), 0.05, color=c, zorder=30))
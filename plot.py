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
        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=100)  # Larger plot
        self.fig.patch.set_facecolor('#ffffff')
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True)
        self._setup_axes()
        self._redraw_all()
    
    def _setup_axes(self):
        pos = list(self.network.node_positions.values())
        x_coords, y_coords = zip(*pos)
        padding = 2.5  # Adjusted padding for the larger scale
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
        
        self.canvas.draw()

    def _draw_static_lines(self, results):
        """Draws a base grey 'pipe' for each transmission line with length and capacity info."""
        for line in self.network.lines:
            u, v = line['from'], line['to']
            x1, y1 = self.network.node_positions[u]
            x2, y2 = self.network.node_positions[v]
            
            # Calculate flow and overload status
            total_flow = results.get('flows', {}).get(f"{u}→{v}", 0)
            capacity = line['capacity']
            utilization = (abs(total_flow) / capacity * 100) if capacity > 0 else 0
            is_overloaded = abs(total_flow) > (capacity + 0.1)
            
            # Draw the line with color indicating overload status
            if is_overloaded:
                line_color = '#ff6b6b'  # Bright red if overloaded
                line_width = 10  # Thicker for visibility
            else:
                line_color = '#f0f0f0'  # Light grey
                line_width = 8
            
            self.ax.plot([x1, x2], [y1, y2], color=line_color, linewidth=line_width, 
                         solid_capstyle='round', zorder=1, alpha=0.8 if is_overloaded else 1.0)
            
            # Line info text (Length and Capacity)
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            angle = np.degrees(np.arctan2(dy, dx))
            if angle > 90: angle -= 180
            if angle < -90: angle += 180
            
            # Offset the text to the side to avoid overlapping with colored flows
            perp_dx, perp_dy = -dy/np.sqrt(dx**2+dy**2), dx/np.sqrt(dx**2+dy**2)
            offset = 0.6  # Increased offset to move labels to the side
            
            # Draw color-coded flow legend NEXT TO THIS SPECIFIC LINE
            gen_flows = results.get('generator_flows', {})
            line_id = f"{u}\u2192{v}"
            gen_contributions = gen_flows.get(line_id, {})
            
            if gen_contributions:
                significant_flows = [(node, mw) for node, mw in gen_contributions.items() if abs(mw) > 0.1]
                if significant_flows:
                    # Special positioning for A-C line: move to left side of triangle
                    if line_id == "A\u2192C":
                        # Position on the left side, similar y-position to A-B
                        legend_x = mid_x - 3.5  # Left of the triangle
                        legend_y = mid_y + 0.5  # Similar height to A-B label
                    elif line_id == "A\u2192B":
                        # Position A-B legend further to the right
                        legend_offset = 2.5  # Increased distance from line center
                        legend_x = mid_x + perp_dx * legend_offset
                        legend_y = mid_y + perp_dy * legend_offset
                    else:
                        # Default positioning perpendicular to the line
                        legend_offset = 1.5  # Distance from line center
                        legend_x = mid_x + perp_dx * legend_offset
                        legend_y = mid_y + perp_dy * legend_offset
                    
                    # Draw line label first
                    self.ax.text(legend_x, legend_y + 0.4, f"{line_id}:", 
                               ha='center', va='bottom', fontsize=7, fontweight='bold',
                               color='#2c3e50')
                    
                    # Draw generator boxes horizontally next to each other
                    num_boxes = len(significant_flows)
                    box_spacing = 0.9
                    total_width = (num_boxes - 1) * box_spacing
                    start_x = legend_x - (total_width / 2)
                    
                    for idx, (gen_node, mw_val) in enumerate(significant_flows):
                        box_x = start_x + idx * box_spacing
                        color = self.network.generator_colors.get(gen_node, 'black')
                        flow_text = f"{gen_node}\n{abs(mw_val):.0f}MW"
                        
                        self.ax.text(box_x, legend_y, flow_text,
                                   ha='center', va='center', fontsize=7, fontweight='bold',
                                   color='white',
                                   bbox=dict(boxstyle='round,pad=0.3', fc=color, ec=color, 
                                            alpha=0.95, lw=1.5),
                                   rotation=0, zorder=15)
            
            # Capacity and length label on the other side
            info_text = f"Cap: {capacity:.0f}MW | Len: {line['length']:.0f}km\n"
            flow_direction = "→" if total_flow >= 0 else "←"
            info_text += f"Total: {abs(total_flow):.1f}MW {flow_direction} ({utilization:.0f}%)"
            
            if is_overloaded:
                text_color = '#ffffff'  # White text on red background
                font_weight = 'bold'
                bg_color = '#e74c3c'  # Red background
                border_color = '#c0392b'  # Dark red border
                info_text = f"⚠️ OVERLOAD ⚠️\n{info_text}"
            else:
                text_color = '#2c3e50'  # Dark text
                font_weight = 'normal'
                bg_color = 'white'
                border_color = 'none'
            
            self.ax.text(mid_x + perp_dx*offset, mid_y + perp_dy*offset, info_text, 
                         ha='center', va='center', rotation=angle, fontsize=8, 
                         color=text_color, fontweight=font_weight,
                         bbox=dict(boxstyle='round,pad=0.3', 
                                   fc=bg_color, 
                                   ec=border_color, 
                                   lw=2 if is_overloaded else 0,
                                   alpha=0.95))

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
            spacing = 0.25  # Increased spacing between parallel flows
            start_offset = -(n_parallel - 1) * spacing / 2

            for i, (gen_node, mw_val) in enumerate(contributions):
                color = self.network.generator_colors.get(gen_node, 'black')
                offset = start_offset + (i * spacing)
                
                # Visual scaling: base width + proportional to MW
                line_width = 1.5 + (abs(mw_val) / 100) * 5 
                
                # CRITICAL: Direction
                direction = np.sign(mw_val)
                
                # Offset positions for parallel lines
                sx, sy = x1 + perp_x*offset, y1 + perp_y*offset
                ex, ey = x2 + perp_x*offset, y2 + perp_y*offset
                
                # Draw the flow line (reversed if direction is negative)
                if direction >= 0:
                    # Positive: draw from start (sx,sy) to end (ex,ey)
                    self.ax.plot([sx, ex], [sy, ey], color=color, linewidth=line_width, 
                                 alpha=0.8, solid_capstyle='round', zorder=10)
                    arrow_start_x, arrow_start_y = sx, sy
                    arrow_end_x, arrow_end_y = ex, ey
                else:
                    # Negative: draw from end to start (reverse direction)
                    self.ax.plot([ex, sx], [ey, sy], color=color, linewidth=line_width, 
                                 alpha=0.8, solid_capstyle='round', zorder=10)
                    arrow_start_x, arrow_start_y = ex, ey
                    arrow_end_x, arrow_end_y = sx, sy
                
                # Add directional arrows (always in positive direction along the line)
                n_arrows = 3
                for a in range(1, n_arrows):
                    frac = a / n_arrows
                    # Base position on the line
                    ax_base = arrow_start_x + frac * (arrow_end_x - arrow_start_x)
                    ay_base = arrow_start_y + frac * (arrow_end_y - arrow_start_y)
                    
                    # Arrow tip position (pointing forward along the line)
                    line_dx = arrow_end_x - arrow_start_x
                    line_dy = arrow_end_y - arrow_start_y
                    line_len = np.sqrt(line_dx**2 + line_dy**2)
                    arrow_dx = line_dx / line_len * 0.15
                    arrow_dy = line_dy / line_len * 0.15
                    
                    self.ax.annotate('', xy=(ax_base + arrow_dx, ay_base + arrow_dy), 
                                     xytext=(ax_base, ay_base),
                                     arrowprops=dict(arrowstyle='->', color=color, 
                                                     lw=min(line_width, 2.5), mutation_scale=12),
                                     zorder=11)

    def _draw_nodes(self, results):
        """Draws nodes with labels, price tags, and generation legend outside the triangle."""
        for node in self.network.nodes:
            x, y = self.network.node_positions[node]
            # Direction vector from center (0,0) to node for offsetting
            norm = np.sqrt(x**2 + y**2)
            dx, dy = (x/norm, y/norm) if norm > 0 else (0, 1)
            
            # Individual color for node/generator
            c = self.network.generator_colors.get(node, 'black')
            
            # Colored node circle
            self.ax.add_patch(Circle((x, y), 0.25, facecolor='white', edgecolor=c, lw=2, zorder=20))
            self.ax.text(x, y, node, ha='center', va='center', fontweight='bold', fontsize=12, zorder=21)
            
            # LMP Text (pushed outwards from node)
            lmp = results['lmp'][node]
            lmp_x, lmp_y = x + dx * 1.3, y + dy * 1.3  # Increased from 0.7 to 1.3 for better spacing
            self.ax.text(lmp_x, lmp_y, f"LMP: €{lmp:.2f}", ha='center', fontsize=10, fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', fc='#ecf0f1', ec='#27ae60', lw=1.5, alpha=1.0), zorder=25)
            
            # Generation & Demand Legend (positioned directly UNDER the LMP panel)
            gen_val = results['generation'][node]
            gen_cost = self.network.generation[node]['cost']
            gen_cap = self.network.generation[node]['capacity']
            demand_val = self.network.consumption[node]
            
            # Special positioning for Node A: place above the node
            if node == 'A':
                leg_x = lmp_x  # Same X as LMP
                leg_y = lmp_y + 0.8  # Above the LMP panel instead of below
                ha = 'center'
                va = 'bottom'  # Bottom-aligned so it extends upward
            else:
                # Position legend directly below LMP panel for other nodes
                leg_x = lmp_x  # Same X as LMP
                leg_y = lmp_y - 0.8  # Below the LMP panel
                ha = 'center'
                va = 'top'  # Top-aligned so it extends downward from the position
            
            # Show shedding if applicable
            shed_val = results.get('shedding', {}).get(node, 0)
            legend_text = f"NODE {node}\n"
            legend_text += f"DEMAND: {demand_val:.1f} MW\n"
            legend_text += f"GEN: {gen_val:.1f} MW\n"
            legend_text += f"Cost: {gen_cost:.1f} €/MWh\n"
            legend_text += f"Max: {gen_cap:.1f} MW"
            
            if shed_val > 0.1:
                legend_text += f"\n⚠ UNMET: {shed_val:.1f} MW"
            
            self.ax.text(leg_x, leg_y, legend_text, ha=ha, va=va, fontsize=9,
                         bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=c, lw=2, alpha=0.9), zorder=25)
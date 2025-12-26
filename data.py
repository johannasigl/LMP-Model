"""
Network Data Management

Contains classes for storing and managing network topology,
generation, and consumption data.
"""


class NetworkData:
    """
    Container for network topology and operational data.
    
    Manages nodes, lines, generation, and consumption data
    with update methods for GUI interaction.
    
    Each line has: from, to, reactance, capacity (MW), length (km)
    Each node has: one generator (capacity MW, cost €/MWh), demand (MW)
    """
    
    def __init__(self, param):
        """
        Initialize network data from parameters.
        
        Parameters
        ----------
        param : dict
            Parameter dictionary containing:
            - nodes: list of node names
            - lines: list of line dictionaries (from, to, capacity, length, reactance)
            - generation: dict of generation data per node (capacity, cost)
            - consumption: dict of consumption per node (MW)
        """
        self.nodes = list(param['nodes'])
        self.lines = [dict(line) for line in param['lines']]  # deep copy
        self.generation = {node: dict(gen) for node, gen in param['generation'].items()}
        self.consumption = dict(param['consumption'])
        
        # Assign colors to generators for flow visualization
        self._assign_generator_colors()
        
        # Calculate node positions for visualization
        self._calculate_node_positions()
    
    def _assign_generator_colors(self):
        """
        Assign distinct colors to each generator for flow visualization.
        """
        # Color palette for generators
        colors = ['#4B8246', '#4061A4', '#D26A5E', '#FFD966', '#9673A6', '#E07941', '#5DADE2']
        self.generator_colors = {}
        for i, node in enumerate(self.nodes):
            self.generator_colors[node] = colors[i % len(colors)]
    
    def _calculate_node_positions(self):
        """
        Calculate node positions for network visualization.
        
        Arranges nodes in a circular layout.
        """
        import numpy as np
        
        n = len(self.nodes)
        self.node_positions = {}
        
        for i, node in enumerate(self.nodes):
            angle = 2 * np.pi * i / n - np.pi / 2  # Start from top
            x = np.cos(angle)
            y = np.sin(angle)
            self.node_positions[node] = (x, y)
    
    def update_line_capacity(self, line_idx, capacity):
        """
        Update the capacity of a line.
        
        Parameters
        ----------
        line_idx : int
            Index of the line in the lines list.
        capacity : float
            New capacity value in MW.
        """
        self.lines[line_idx]['capacity'] = max(0, capacity)
    
    def update_line_length(self, line_idx, length):
        """
        Update the length of a line.
        
        Parameters
        ----------
        line_idx : int
            Index of the line in the lines list.
        length : float
            New length value in km.
        """
        self.lines[line_idx]['length'] = max(0.1, length)
        # Update reactance based on length (proportional)
        self.lines[line_idx]['reactance'] = length * 0.001  # 0.001 p.u./km
    
    def update_generation(self, node, capacity, cost):
        """
        Update generation parameters at a node.
        
        Parameters
        ----------
        node : str
            Node name.
        capacity : float
            New generation capacity in MW.
        cost : float
            New marginal cost in €/MWh.
        """
        self.generation[node]['capacity'] = max(0, capacity)
        self.generation[node]['cost'] = max(0, cost)
    
    def update_consumption(self, node, consumption):
        """
        Update consumption at a node.
        
        Parameters
        ----------
        node : str
            Node name.
        consumption : float
            New consumption in MW.
        """
        self.consumption[node] = max(0, consumption)
    
    def get_total_generation_capacity(self):
        """
        Get total available generation capacity.
        
        Returns
        -------
        float
            Sum of all generation capacities.
        """
        return sum(gen['capacity'] for gen in self.generation.values())
    
    def get_total_consumption(self):
        """
        Get total consumption.
        
        Returns
        -------
        float
            Sum of all consumption.
        """
        return sum(self.consumption.values())
    
    def get_line_id(self, line_idx):
        """
        Get string identifier for a line.
        
        Parameters
        ----------
        line_idx : int
            Index of the line.
        
        Returns
        -------
        str
            Line identifier string.
        """
        line = self.lines[line_idx]
        return f"{line['from']}→{line['to']}"

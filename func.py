"""
DC Power Flow and LMP Calculation Functions

Contains the core logic for solving DC optimal power flow and computing
Locational Marginal Prices (LMPs).
"""

import numpy as np
from scipy.optimize import linprog


class DCPowerFlow:
    """
    DC Optimal Power Flow solver with LMP calculation.
    
    Uses a linearized power flow model where:
    - Power flow on a line is proportional to angle difference
    - Losses are neglected
    - Voltage magnitudes are assumed to be 1 p.u.
    """
    
    def __init__(self, network_data):
        """
        Initialize the DC power flow solver.
        
        Parameters
        ----------
        network_data : NetworkData
            Network data object containing topology and parameters.
        """
        self.network = network_data
    
    def solve(self):
        """
        Solve the DC optimal power flow problem.
        
        Minimizes total generation cost subject to:
        - Power balance at each node
        - Generation capacity limits
        - Line flow limits
        
        Returns
        -------
        dict
            Results dictionary containing:
            - feasible: bool, whether solution was found
            - lmp: dict, LMP at each node
            - generation: dict, generation at each node
            - flows: dict, power flow on each line
            - capacities: dict, capacity of each line
            - total_cost: float, total generation cost
        """
        nodes = self.network.nodes
        lines = self.network.lines
        n_nodes = len(nodes)
        n_lines = len(lines)
        
        # Build PTDF matrix (Power Transfer Distribution Factors)
        ptdf = self._build_ptdf_matrix()
        
        # Decision variables: generation at each node
        # Objective: minimize sum(cost_i * gen_i)
        costs = np.array([self.network.generation[node]['cost'] for node in nodes])
        
        # Equality constraint: sum(gen) = sum(consumption)
        total_consumption = sum(self.network.consumption.values())
        A_eq = np.ones((1, n_nodes))
        b_eq = np.array([total_consumption])
        
        # Inequality constraints for line flows
        # PTDF @ gen <= line_capacity + PTDF @ consumption
        # -PTDF @ gen <= line_capacity + PTDF @ (-consumption)
        consumption_vector = np.array([self.network.consumption[node] for node in nodes])
        capacities = np.array([line['capacity'] for line in lines])
        
        # Net injection = generation - consumption
        # Flow = PTDF @ (generation - consumption)
        # |Flow| <= capacity
        # => PTDF @ gen <= capacity + PTDF @ consumption
        # => -PTDF @ gen <= capacity - PTDF @ consumption
        
        A_ub = np.vstack([ptdf, -ptdf])
        b_ub = np.hstack([
            capacities + ptdf @ consumption_vector,
            capacities - ptdf @ consumption_vector
        ])
        
        # Bounds: 0 <= gen <= capacity
        bounds = [(0, self.network.generation[node]['capacity']) for node in nodes]
        
        # Solve LP
        result = linprog(
            c=costs,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs'
        )
        
        if not result.success:
            # Analyze why the problem is infeasible
            infeasibility_analysis = self._analyze_infeasibility(ptdf, capacities, consumption_vector)
            return {
                'feasible': False,
                'message': result.message,
                'infeasibility_analysis': infeasibility_analysis,
                'lmp': {node: 0 for node in nodes},
                'generation': {node: 0 for node in nodes},
                'flows': {self._line_id(line): 0 for line in lines},
                'capacities': {self._line_id(line): line['capacity'] for line in lines},
                'lengths': {self._line_id(line): line.get('length', 100) for line in lines},
                'generator_flows': {self._line_id(line): {} for line in lines},
                'ptdf': ptdf,
                'total_cost': 0
            }
        
        # Extract results
        generation = {node: result.x[i] for i, node in enumerate(nodes)}
        
        # Calculate line flows
        net_injection = result.x - consumption_vector
        line_flows = ptdf @ net_injection
        flows = {self._line_id(lines[i]): line_flows[i] for i in range(n_lines)}
        
        # Calculate LMPs from dual variables
        # LMP = shadow price of power balance constraint + congestion component
        lmp = self._calculate_lmp(result, ptdf, costs, capacities, consumption_vector)
        
        # Calculate generator flow contributions on each line
        generator_flows = self._calculate_generator_flows(result.x, ptdf)
        
        return {
            'feasible': True,
            'lmp': lmp,
            'generation': generation,
            'flows': flows,
            'capacities': {self._line_id(line): line['capacity'] for line in lines},
            'lengths': {self._line_id(line): line.get('length', 100) for line in lines},
            'generator_flows': generator_flows,
            'ptdf': ptdf,
            'total_cost': result.fun
        }
    
    def _build_ptdf_matrix(self):
        """
        Build the Power Transfer Distribution Factor matrix.
        
        Returns
        -------
        np.ndarray
            PTDF matrix of shape (n_lines, n_nodes).
        """
        nodes = self.network.nodes
        lines = self.network.lines
        n_nodes = len(nodes)
        n_lines = len(lines)
        
        # Build susceptance matrix B
        B = np.zeros((n_nodes, n_nodes))
        for line in lines:
            i = nodes.index(line['from'])
            j = nodes.index(line['to'])
            b = 1.0 / line['reactance']
            B[i, i] += b
            B[j, j] += b
            B[i, j] -= b
            B[j, i] -= b
        
        # Remove slack bus (first node) to make B invertible
        B_reduced = B[1:, 1:]
        
        # Calculate B inverse (with slack bus row/col as zeros)
        B_inv = np.zeros((n_nodes, n_nodes))
        if n_nodes > 1:
            B_inv[1:, 1:] = np.linalg.inv(B_reduced)
        
        # Build PTDF matrix
        # PTDF(l, n) = (1/x_l) * (B_inv[from_l, n] - B_inv[to_l, n])
        ptdf = np.zeros((n_lines, n_nodes))
        for l, line in enumerate(lines):
            i = nodes.index(line['from'])
            j = nodes.index(line['to'])
            b = 1.0 / line['reactance']
            for n in range(n_nodes):
                ptdf[l, n] = b * (B_inv[i, n] - B_inv[j, n])
        
        return ptdf
    
    def _calculate_lmp(self, result, ptdf, costs, capacities, consumption):
        """
        Calculate Locational Marginal Prices from optimization result.
        
        LMP consists of:
        - Energy component (marginal cost of generation)
        - Congestion component (shadow prices of line constraints)
        
        Parameters
        ----------
        result : scipy.optimize.OptimizeResult
            LP solution result.
        ptdf : np.ndarray
            PTDF matrix.
        costs : np.ndarray
            Generation costs.
        capacities : np.ndarray
            Line capacities.
        consumption : np.ndarray
            Consumption at each node.
        
        Returns
        -------
        dict
            LMP at each node.
        """
        nodes = self.network.nodes
        n_nodes = len(nodes)
        n_lines = len(self.network.lines)
        
        # The dual of the power balance constraint gives the reference LMP
        # Congestion rents modify LMPs at different nodes
        
        # For HiGHS, we need to extract marginal prices differently
        # Use the marginal costs from the result if available
        if hasattr(result, 'ineqlin') and result.ineqlin is not None:
            # Dual variables for inequality constraints (line limits)
            mu_upper = result.ineqlin.marginals[:n_lines]  # upper flow limit
            mu_lower = result.ineqlin.marginals[n_lines:]  # lower flow limit
            
            # Energy price from equality constraint dual
            if hasattr(result, 'eqlin') and result.eqlin is not None:
                lambda_energy = result.eqlin.marginals[0]
            else:
                # Use marginal generator cost as approximation
                lambda_energy = self._find_marginal_cost(result.x, costs)
            
            # LMP = lambda_energy + sum over lines of (mu_upper - mu_lower) * PTDF
            lmp_values = np.ones(n_nodes) * lambda_energy
            for l in range(n_lines):
                congestion_price = mu_upper[l] - mu_lower[l]
                lmp_values -= congestion_price * ptdf[l, :]
        else:
            # Fallback: use marginal cost of marginal generator
            lambda_energy = self._find_marginal_cost(result.x, costs)
            lmp_values = np.ones(n_nodes) * lambda_energy
        
        return {node: lmp_values[i] for i, node in enumerate(nodes)}
    
    def _find_marginal_cost(self, generation, costs):
        """
        Find the cost of the marginal generator.
        
        Parameters
        ----------
        generation : np.ndarray
            Generation at each node.
        costs : np.ndarray
            Generation costs.
        
        Returns
        -------
        float
            Marginal cost.
        """
        nodes = self.network.nodes
        marginal_cost = 0
        for i, node in enumerate(nodes):
            gen = generation[i]
            cap = self.network.generation[node]['capacity']
            # If generator is partially loaded, it's marginal
            if 0 < gen < cap - 0.01:
                marginal_cost = max(marginal_cost, costs[i])
            # If generator is at capacity, it might set the price
            elif gen >= cap - 0.01 and gen > 0.01:
                marginal_cost = max(marginal_cost, costs[i])
        
        # If no marginal generator found, use lowest cost of active generators
        if marginal_cost == 0:
            for i, node in enumerate(nodes):
                if generation[i] > 0.01:
                    if marginal_cost == 0:
                        marginal_cost = costs[i]
                    else:
                        marginal_cost = max(marginal_cost, costs[i])
        
        return marginal_cost
    
    def _line_id(self, line):
        """
        Create a string identifier for a line.
        
        Parameters
        ----------
        line : dict
            Line dictionary.
        
        Returns
        -------
        str
            Line identifier string.
        """
        return f"{line['from']}→{line['to']}"
    
    def _calculate_generator_flows(self, generation, ptdf):
        """
        Calculate each generator's contribution to flow on each line.
        
        Uses PTDF to decompose total flow into per-generator contributions.
        Each generator's injection creates flow on lines proportional to PTDF.
        
        Parameters
        ----------
        generation : np.ndarray
            Generation at each node.
        ptdf : np.ndarray
            PTDF matrix (n_lines x n_nodes).
        
        Returns
        -------
        dict
            Dictionary mapping line_id -> {generator_node: flow_contribution}.
            Positive flow = from -> to direction.
        """
        nodes = self.network.nodes
        lines = self.network.lines
        n_lines = len(lines)
        
        generator_flows = {}
        
        for l, line in enumerate(lines):
            line_id = self._line_id(line)
            generator_flows[line_id] = {}
            
            for n, node in enumerate(nodes):
                gen = generation[n]
                if gen > 0.01:  # Only track active generators
                    # Flow contribution = PTDF * generation
                    flow_contribution = ptdf[l, n] * gen
                    generator_flows[line_id][node] = flow_contribution
        
        return generator_flows
    
    def _analyze_infeasibility(self, ptdf, capacities, consumption_vector):
        """
        Analyze why the power flow problem is infeasible.
        
        Checks for:
        1. Insufficient total generation capacity
        2. Transmission bottlenecks preventing power delivery
        3. Node-specific supply-demand imbalances
        
        Parameters
        ----------
        ptdf : np.ndarray
            PTDF matrix.
        capacities : np.ndarray
            Line capacities.
        consumption_vector : np.ndarray
            Consumption at each node.
        
        Returns
        -------
        dict
            Analysis results with explanation and suggestions.
        """
        nodes = self.network.nodes
        lines = self.network.lines
        
        total_demand = sum(self.network.consumption.values())
        total_gen_capacity = sum(self.network.generation[n]['capacity'] for n in nodes)
        
        analysis = {
            'causes': [],
            'details': [],
            'suggestions': []
        }
        
        # Check 1: Total generation vs demand
        if total_gen_capacity < total_demand:
            shortfall = total_demand - total_gen_capacity
            analysis['causes'].append("INSUFFICIENT GENERATION CAPACITY")
            analysis['details'].append(
                f"Total demand: {total_demand:.0f} MW\n"
                f"Total generation capacity: {total_gen_capacity:.0f} MW\n"
                f"Shortfall: {shortfall:.0f} MW"
            )
            analysis['suggestions'].append(
                f"Increase generation capacity by at least {shortfall:.0f} MW,\n"
                f"or reduce demand by {shortfall:.0f} MW."
            )
        
        # Check 2: Nodes with demand but no local generation - check if reachable
        for i, node in enumerate(nodes):
            demand = self.network.consumption[node]
            local_gen = self.network.generation[node]['capacity']
            
            if demand > 0 and local_gen < demand:
                # This node needs imports - check transmission capacity
                net_import_needed = demand - local_gen
                
                # Find lines connected to this node
                import_capacity = 0
                connected_lines = []
                
                for j, line in enumerate(lines):
                    if line['to'] == node:
                        import_capacity += line['capacity']
                        connected_lines.append(f"{line['from']}→{node}: {line['capacity']:.0f} MW")
                    elif line['from'] == node:
                        import_capacity += line['capacity']
                        connected_lines.append(f"{node}→{line['to']}: {line['capacity']:.0f} MW (reverse)")
                
                if import_capacity < net_import_needed and total_gen_capacity >= total_demand:
                    analysis['causes'].append(f"TRANSMISSION BOTTLENECK TO NODE {node}")
                    analysis['details'].append(
                        f"Node {node} needs {net_import_needed:.0f} MW imports\n"
                        f"(Demand: {demand:.0f} MW, Local gen: {local_gen:.0f} MW)\n"
                        f"Connected lines:\n  " + "\n  ".join(connected_lines) + f"\n"
                        f"Max import capacity: ~{import_capacity:.0f} MW"
                    )
                    analysis['suggestions'].append(
                        f"Increase line capacity to node {node},\n"
                        f"add local generation at {node},\n"
                        f"or reduce demand at {node}."
                    )
        
        # Check 3: If still no cause found, it's likely a network topology issue
        if not analysis['causes']:
            analysis['causes'].append("NETWORK CONSTRAINTS")
            analysis['details'].append(
                "The combination of generation locations, demand locations,\n"
                "and transmission limits makes it impossible to balance\n"
                "power flows across the network.\n\n"
                "This can happen when power must flow through congested\n"
                "intermediate nodes to reach demand."
            )
            analysis['suggestions'].append(
                "Try increasing line capacities,\n"
                "redistributing generation or demand,\n"
                "or adding transmission paths."
            )
        
        return analysis
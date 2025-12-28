"""
DC Power Flow and LMP Calculation Functions

Contains the core logic for solving DC optimal power flow and computing
Locational Marginal Prices (LMPs).
"""

import numpy as np
from scipy.optimize import linprog


class DCPowerFlow:
    """
    DC Optimal Power Flow solver with LMP calculation and Load Shedding.
    
    Uses a linearized power flow model with slack variables for unmet demand
    to ensure feasibility during scarcity and calculate scarcity-based LMPs.
    """
    
    def __init__(self, network_data):
        """
        Initialize the DC power flow solver.
        """
        self.network = network_data
    
    def solve(self):
        """
        Solve the DC optimal power flow problem with load shedding.
        """
        nodes = self.network.nodes
        lines = self.network.lines
        n_nodes = len(nodes)
        n_lines = len(lines)
        
        # 1. Build PTDF matrix
        ptdf = self._build_ptdf_matrix()
        
        # 2. Setup LP variables: [generation_nodes (n_nodes), load_shed_nodes (n_nodes)]
        # Objective: minimize gen cost + load shedding penalty (VOLL)
        costs = np.array([self.network.generation[node]['cost'] for node in nodes])
        VOLL = 5000.0  # Scarcity price
        c = np.hstack([costs, np.ones(n_nodes) * VOLL])
        
        # 3. Equality constraint: System Power Balance
        # sum(gen) + sum(shed) = sum(consumption)
        consumption_vector = np.array([self.network.consumption[node] for node in nodes])
        total_demand = sum(consumption_vector)
        A_eq = np.ones((1, 2 * n_nodes))
        b_eq = np.array([total_demand])
        
        # 4. Inequality constraints: Transmission Limits
        # Flow = PTDF @ (gen + shed - consumption)
        # -cap <= PTDF @ (gen + shed) - PTDF @ consumption <= cap
        capacities = np.array([line['capacity'] for line in lines])
        
        ptdf_extended = np.hstack([ptdf, ptdf])
        A_ub = np.vstack([ptdf_extended, -ptdf_extended])
        b_ub = np.hstack([
            capacities + ptdf @ consumption_vector,
            capacities - ptdf @ consumption_vector
        ])
        
        # 5. Variable Bounds
        gen_bounds = [(0, self.network.generation[node]['capacity']) for node in nodes]
        shed_bounds = [(0, max(0.0, self.network.consumption[node])) for node in nodes]
        bounds = gen_bounds + shed_bounds
        
        # 6. Solve LP
        result = linprog(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs'
        )
        
        if not result.success:
            print(f"Solver failed: {result.message}")
            return {
                'feasible': False,
                'lmp': {node: 0.0 for node in nodes},
                'generation': {node: 0.0 for node in nodes},
                'flows': {self._line_id(line): 0.0 for line in lines},
                'capacities': {self._line_id(line): line['capacity'] for line in lines},
                'generator_flows': {self._line_id(line): {} for line in lines},
                'total_cost': 0.0
            }
        
        # 7. Extract Results
        generation = {node: result.x[i] for i, node in enumerate(nodes)}
        shedding = {node: result.x[i + n_nodes] for i, node in enumerate(nodes)}
        
        # Net injection including shed load (which acts like local generation)
        net_injection = (result.x[:n_nodes] + result.x[n_nodes:]) - consumption_vector
        line_flows = ptdf @ net_injection
        flows = {self._line_id(lines[i]): line_flows[i] for i in range(n_lines)}
        
        # 8. Calculate LMPs and Details
        lmp_data = self._calculate_lmp_detailed(result, ptdf, costs)
        generator_flows = self._calculate_generator_flows(result.x[:n_nodes], ptdf)
        
        return {
            'feasible': True,
            'lmp': lmp_data['lmp'],
            'lmp_details': lmp_data['details'],
            'energy_price': lmp_data['energy_price'],
            'generation': generation,
            'shedding': shedding,
            'flows': flows,
            'capacities': {self._line_id(line): line['capacity'] for line in lines},
            'lengths': {self._line_id(line): line.get('length', 100) for line in lines},
            'generator_flows': generator_flows,
            'ptdf': ptdf,
            'total_cost': result.fun
        }

    def _calculate_lmp_detailed(self, result, ptdf, costs):
        nodes = self.network.nodes
        n_nodes = len(nodes)
        n_lines = len(self.network.lines)
        details = {node: {'congestion': 0.0, 'line_details': []} for node in nodes}
        
        if hasattr(result, 'ineqlin') and result.ineqlin is not None:
            mu_upper = result.ineqlin.marginals[:n_lines]
            mu_lower = result.ineqlin.marginals[n_lines:]
            
            if hasattr(result, 'eqlin') and result.eqlin is not None:
                # Use the marginal directly (positive for demand sensitivity)
                lambda_energy = result.eqlin.marginals[0]
            else:
                lambda_energy = self._find_marginal_cost(result.x[:n_nodes], costs)
            
            congestion_component = np.zeros(n_nodes)
            for l in range(n_lines):
                price_diff = mu_upper[l] - mu_lower[l]
                if abs(price_diff) > 0.001:
                    line_contrib = price_diff * ptdf[l, :]
                    congestion_component += line_contrib
                    for i, node in enumerate(nodes):
                        if abs(line_contrib[i]) > 0.001:
                            line_id = self._line_id(self.network.lines[l])
                            details[node]['line_details'].append((line_id, line_contrib[i]))
            
            lmp_values = lambda_energy + congestion_component
        else:
            lambda_energy = self._find_marginal_cost(result.x[:n_nodes], costs)
            lmp_values = np.ones(n_nodes) * lambda_energy

        return {
            'lmp': {node: float(lmp_values[i]) for i, node in enumerate(nodes)},
            'energy_price': float(lambda_energy),
            'details': details
        }

    def _build_ptdf_matrix(self):
        nodes = self.network.nodes
        lines = self.network.lines
        n_nodes = len(nodes)
        n_lines = len(lines)
        
        B = np.zeros((n_nodes, n_nodes))
        for line in lines:
            i, j = nodes.index(line['from']), nodes.index(line['to'])
            b = 1.0 / line['reactance']
            B[i, i] += b
            B[j, j] += b
            B[i, j] -= b
            B[j, i] -= b
        
        B_inv = np.zeros((n_nodes, n_nodes))
        if n_nodes > 1:
            B_inv[1:, 1:] = np.linalg.inv(B[1:, 1:])
        
        ptdf = np.zeros((n_lines, n_nodes))
        for l, line in enumerate(lines):
            i, j = nodes.index(line['from']), nodes.index(line['to'])
            b = 1.0 / line['reactance']
            for n in range(n_nodes):
                ptdf[l, n] = b * (B_inv[i, n] - B_inv[j, n])
        return ptdf

    def _find_marginal_cost(self, generation, costs):
        marginal_cost = 0
        for i, node in enumerate(self.network.nodes):
            gen, cap = generation[i], self.network.generation[node]['capacity']
            if 0.01 < gen < cap - 0.01: return costs[i]
            if gen > 0.01: marginal_cost = max(marginal_cost, costs[i])
        return marginal_cost if marginal_cost > 0 else (costs[0] if len(costs) > 0 else 0)

    def _line_id(self, line):
        return f"{line['from']}→{line['to']}"

    def _calculate_generator_flows(self, generation, ptdf):
        nodes, lines = self.network.nodes, self.network.lines
        total_gen = sum(generation)
        if total_gen < 0.1: return {self._line_id(l): {} for l in lines}
        
        consumption_vector = np.array([self.network.consumption[n] for n in nodes])
        generator_flows = {self._line_id(l): {} for l in lines}
        
        for n, gen_node in enumerate(nodes):
            if generation[n] < 0.1: continue
            gen_injection = np.zeros(len(nodes))
            gen_injection[n] = generation[n]
            gen_injection -= (generation[n] / total_gen) * consumption_vector
            line_flows = ptdf @ gen_injection
            for l, line in enumerate(lines):
                if abs(line_flows[l]) > 0.05:
                    generator_flows[self._line_id(line)][gen_node] = line_flows[l]
        return generator_flows

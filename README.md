# DC Power Flow Model - Nodal Pricing (LMP) Visualization

An interactive educational tool for understanding **Locational Marginal Pricing (LMP)** in electricity markets using DC power flow analysis.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This application provides an interactive GUI to explore how:
- **Transmission constraints** affect nodal prices
- **Generation costs** propagate through the network
- **Congestion** creates price differences between nodes
- **Power flows** distribute across the network

## Features

- 🔌 **Interactive Network Editor**: Adjust line capacities, generation, and consumption in real-time
- 📊 **Visual Feedback**: Color-coded nodes (by LMP) and lines (by utilization)
- ⚡ **DC Optimal Power Flow**: Solves economic dispatch with network constraints
- 💰 **LMP Calculation**: Computes nodal prices based on marginal costs and congestion

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LMP-Model.git
cd LMP-Model

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### GUI Controls

| Section | Description |
|---------|-------------|
| **Line Capacities** | Adjust transmission limits (MW) with sliders |
| **Generation** | Set capacity (MW) and marginal cost (€/MWh) per node |
| **Consumption** | Set demand (MW) at each node |
| **Results** | View LMPs, generation dispatch, line flows, and total cost |

## How It Works

### DC Power Flow Model

The model uses linearized power flow equations:
- Power flow on a line is proportional to the angle difference: $P_{ij} = \frac{\theta_i - \theta_j}{X_{ij}}$
- Losses are neglected
- Voltage magnitudes are assumed constant

### Locational Marginal Pricing

LMPs are calculated as the marginal cost of serving an additional MW at each node:

$$LMP_n = \lambda + \sum_l \mu_l \cdot PTDF_{l,n}$$

Where:
- $\lambda$ = system marginal energy price
- $\mu_l$ = shadow price of line $l$ constraint
- $PTDF_{l,n}$ = Power Transfer Distribution Factor

## Project Structure

```
LMP-Model/
├── main.py              # Entry point, parameters, GUI application
├── func.py              # DC power flow solver and LMP calculation
├── data.py              # Network data management
├── plot.py              # Network visualization
├── plotting_standards.py # Plotting configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Example Scenarios

### Scenario 1: No Congestion
With sufficient line capacity, all nodes have the same LMP equal to the marginal generator's cost.

### Scenario 2: Congested Line
When a line hits its capacity limit:
- Cheap generation cannot fully reach high-demand nodes
- LMPs diverge between nodes
- Expensive local generation is dispatched

### Scenario 3: Infeasible Dispatch
If total generation capacity < total demand, or network constraints prevent power delivery, the model reports infeasibility.

## Dependencies

- Python 3.8+
- NumPy
- SciPy
- Matplotlib
- Tkinter (usually included with Python)

## License

MIT License - feel free to use for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## References

- Schweppe, F.C., et al. "Spot Pricing of Electricity" (1988)
- Wood, A.J., Wollenberg, B.F. "Power Generation, Operation and Control" (2014)

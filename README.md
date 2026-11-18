# Automated N-1 Contingency & Power Flow Analyzer (IEEE 30-Bus)

A Python-based transmission network analysis tool built with **pandapower**, **Pandas**, and **NumPy** to execute AC power flow studies, automated $N-1$ line-outage contingency screening, high-load integration stress testing, and reactive power compensation sizing.

## Engineering Scope
* **Network Model:** Standard IEEE 30-Bus Transmission System (`pandapower.networks.case30`).
* **Compliance Thresholds:** Flags steady-state bus voltage violations outside ANSI/IEEE $\pm5\%$ limits ($0.95 - 1.05\text{ p.u.}$) and transmission line thermal overloads ($>100\%$ rated capacity).
* **Automated $N-1$ Screening:** Iteratively trips every in-service transmission line, solves the AC power flow, catches non-convergence/islanding events, and exports a ranked CSV report.
* **Load Integration & Mitigation:** Models a +15 MW / +5 MVAr load addition (e.g., data center or industrial interconnection) at a weak peripheral bus (Bus 29) and iteratively sizes a shunt capacitor bank to restore voltage stability above $0.95\text{ p.u.}$

## Repository Structure
```text
├── main.py                      # Main execution pipeline
├── requirements.txt             # Python dependencies
└── src/
    ├── contingency_analyzer.py  # AC power flow, N-1 loop, and capacitor sizing logic
    └── plotting.py              # Matplotlib visualization generators

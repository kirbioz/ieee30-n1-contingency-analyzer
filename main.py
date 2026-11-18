import os
from src.contingency_analyzer import GridContingencyAnalyzer
from src.plotting import plot_voltage_comparison, plot_worst_contingencies


def main():
    os.makedirs("outputs", exist_ok=True)
    analyzer = GridContingencyAnalyzer(v_min_pu=0.95, v_max_pu=1.05, max_loading_pct=100.0)

    print("=" * 60)
    print("IEEE 30-BUS AUTOMATED N-1 CONTINGENCY & POWER FLOW ANALYZER")
    print("=" * 60)

    # 1. Base Case Analysis
    base_res = analyzer.run_base_case()
    print("\n[1] BASE CASE POWER FLOW")
    print(f"    Min Voltage : {base_res['min_vm_pu']:.4f} p.u. (Bus {base_res['min_vm_bus']})")
    print(f"    Max Voltage : {base_res['max_vm_pu']:.4f} p.u. (Bus {base_res['max_vm_bus']})")
    print(f"    Max Loading : {base_res['max_line_loading_pct']:.2f}% (Line {base_res['max_loading_line']})")
    print(f"    Violations  : {base_res['voltage_violations']} Voltage | {base_res['thermal_overloads']} Thermal")

    # 2. Automated N-1 Contingency Screening
    n1_df = analyzer.run_n1_contingencies()
    n1_csv_path = "outputs/n1_contingency_report.csv"
    n1_df.to_csv(n1_csv_path, index=False)

    violations_count = (n1_df["status"] != "PASS").sum()
    print("\n[2] N-1 CONTINGENCY SCREENING")
    print(f"    Total Lines Tested : {len(n1_df)}")
    print(f"    Contingencies Flagged (Violations/Diverged): {violations_count}")
    print(f"    Full report saved to: {n1_csv_path}")

    # 3. High-Load Integration Scenario (e.g., Data Center / Industrial Load at Bus 29)
    target_bus = 29
    stressed_net = analyzer.simulate_high_load_integration(target_bus=target_bus, p_mw=15.0, q_mvar=5.0)
    stressed_res = analyzer.run_base_case(stressed_net)
    print(f"\n[3] HIGH-LOAD INTEGRATION (+15 MW / +5 MVAr at Bus {target_bus})")
    print(f"    Min Voltage : {stressed_res['min_vm_pu']:.4f} p.u. (Bus {stressed_res['min_vm_bus']})")
    print(f"    Violations  : {stressed_res['voltage_violations']} Voltage | {stressed_res['thermal_overloads']} Thermal")

    # 4. Reactive Power Mitigation (Shunt Capacitor Sizing)
    mitigated_net, cap_mvar = analyzer.size_shunt_capacitor(stressed_net, target_bus=target_bus, step_mvar=2.0)
    mitigated_res = analyzer.run_base_case(mitigated_net)
    print(f"\n[4] REACTIVE POWER MITIGATION (Shunt Capacitor at Bus {target_bus})")
    print(f"    Sized Capacitor Bank : {cap_mvar:.1f} MVAr")
    print(f"    Restored Min Voltage : {mitigated_res['min_vm_pu']:.4f} p.u. (Bus {mitigated_res['min_vm_bus']})")
    print(f"    Violations Remaining : {mitigated_res['voltage_violations']} Voltage | {mitigated_res['thermal_overloads']} Thermal")

    # 5. Generate Visualizations
    plot_voltage_comparison(
        base_res["bus_voltages"],
        stressed_res["bus_voltages"],
        mitigated_res["bus_voltages"],
    )
    plot_worst_contingencies(n1_df)
    print("\n[5] OUTPUTS GENERATED")
    print("    - outputs/n1_contingency_report.csv")
    print("    - outputs/voltage_profile_comparison.png")
    print("    - outputs/n1_worst_contingencies.png")
    print("=" * 60)


if __name__ == "__main__":
    main()
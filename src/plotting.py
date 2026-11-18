import os
import matplotlib.pyplot as plt
import pandas as pd


def plot_voltage_comparison(
    base_vm: pd.Series,
    stressed_vm: pd.Series,
    mitigated_vm: pd.Series,
    output_path: str = "outputs/voltage_profile_comparison.png",
    v_min: float = 0.95,
    v_max: float = 1.05,
) -> None:
    """Plots bus voltage profiles across Base, High-Load, and Mitigated scenarios."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.figure(figsize=(11, 5))
    buses = base_vm.index

    plt.plot(buses, base_vm.values, marker="o", markersize=4, label="Base Case", linewidth=1.8)
    plt.plot(buses, stressed_vm.values, marker="s", markersize=4, label="High-Load Integration (+15 MW)", linewidth=1.8, linestyle="--")
    plt.plot(buses, mitigated_vm.values, marker="^", markersize=4, label="Mitigated (Shunt Capacitor)", linewidth=1.8)

    plt.axhline(v_min, color="red", linestyle=":", linewidth=1.5, label=f"ANSI Lower Limit ({v_min} p.u.)")
    plt.axhline(v_max, color="red", linestyle=":", linewidth=1.5, label=f"ANSI Upper Limit ({v_max} p.u.)")

    plt.title("IEEE 30-Bus Steady-State Voltage Profile Comparison", fontsize=13, fontweight="bold")
    plt.xlabel("Bus Index", fontsize=11)
    plt.ylabel("Voltage Magnitude (p.u.)", fontsize=11)
    plt.xticks(buses)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_worst_contingencies(
    n1_df: pd.DataFrame,
    output_path: str = "outputs/n1_worst_contingencies.png",
    top_n: int = 10,
) -> None:
    """Plots the top N most severe N-1 line outages by minimum bus voltage."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    converged_df = n1_df[n1_df["converged"]].nsmallest(top_n, "min_vm_pu").copy()
    converged_df["label"] = (
        "L" + converged_df["outage_line_idx"].astype(str)
        + " (" + converged_df["from_bus"].astype(str)
        + "-" + converged_df["to_bus"].astype(str) + ")"
    )

    plt.figure(figsize=(10, 5))
    colors = ["#d62728" if v < 0.95 else "#1f77b4" for v in converged_df["min_vm_pu"]]
    plt.barh(converged_df["label"], converged_df["min_vm_pu"], color=colors)
    plt.axvline(0.95, color="red", linestyle="--", linewidth=1.5, label="0.95 p.u. Limit")

    plt.title(f"Top {top_n} Most Severe N-1 Line Outages (Minimum Bus Voltage)", fontsize=13, fontweight="bold")
    plt.xlabel("Minimum Bus Voltage (p.u.)", fontsize=11)
    plt.ylabel("Tripped Transmission Line (From-To Bus)", fontsize=11)
    plt.xlim(left=max(0.80, converged_df["min_vm_pu"].min() - 0.03), right=1.02)
    plt.gca().invert_yaxis()
    plt.grid(True, axis="x", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

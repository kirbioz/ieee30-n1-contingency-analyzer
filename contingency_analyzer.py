import copy
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn


class GridContingencyAnalyzer:
    """
    Automated AC Power Flow and N-1 Contingency Analyzer for the IEEE 30-Bus System.
    Evaluates steady-state voltage stability (ANSI/IEEE +/-5%) and thermal line loading.
    """

    def __init__(self, v_min_pu: float = 0.95, v_max_pu: float = 1.05, max_loading_pct: float = 100.0):
        self.v_min_pu = v_min_pu
        self.v_max_pu = v_max_pu
        self.max_loading_pct = max_loading_pct
        self.net = pn.case30()

    def run_base_case(self, net: pp.pandapowerNet = None) -> dict:
        """Executes AC power flow on the intact network and returns key metrics."""
        target_net = self.net if net is None else net
        pp.runpp(target_net)

        vm = target_net.res_bus["vm_pu"]
        loading = target_net.res_line["loading_percent"]

        return {
            "converged": True,
            "min_vm_pu": float(vm.min()),
            "min_vm_bus": int(vm.idxmin()),
            "max_vm_pu": float(vm.max()),
            "max_vm_bus": int(vm.idxmax()),
            "max_line_loading_pct": float(loading.max()),
            "max_loading_line": int(loading.idxmax()),
            "voltage_violations": int(((vm < self.v_min_pu) | (vm > self.v_max_pu)).sum()),
            "thermal_overloads": int((loading > self.max_loading_pct).sum()),
            "bus_voltages": vm.copy(),
            "line_loadings": loading.copy(),
        }

    def run_n1_contingencies(self, net: pp.pandapowerNet = None) -> pd.DataFrame:
        """
        Iteratively trips each in-service transmission line (N-1), runs AC power flow,
        and records voltage violations, thermal overloads, and convergence failures.
        """
        base_net = self.net if net is None else net
        results = []

        for line_idx in base_net.line.index:
            if not base_net.line.at[line_idx, "in_service"]:
                continue

            sim_net = copy.deepcopy(base_net)
            sim_net.line.at[line_idx, "in_service"] = False

            from_bus = int(sim_net.line.at[line_idx, "from_bus"])
            to_bus = int(sim_net.line.at[line_idx, "to_bus"])

            try:
                pp.runpp(sim_net)
                vm = sim_net.res_bus["vm_pu"]
                loading = sim_net.res_line["loading_percent"]

                v_viol = int(((vm < self.v_min_pu) | (vm > self.v_max_pu)).sum())
                t_viol = int((loading > self.max_loading_pct).sum())

                status = "PASS"
                if v_viol > 0 or t_viol > 0:
                    status = "VIOLATION"

                results.append({
                    "outage_line_idx": int(line_idx),
                    "from_bus": from_bus,
                    "to_bus": to_bus,
                    "converged": True,
                    "min_vm_pu": round(float(vm.min()), 4),
                    "worst_bus": int(vm.idxmin()),
                    "max_vm_pu": round(float(vm.max()), 4),
                    "max_loading_pct": round(float(loading.max()), 2),
                    "worst_line_idx": int(loading.idxmax()),
                    "voltage_violations": v_viol,
                    "thermal_overloads": t_viol,
                    "status": status,
                })

            except pp.LoadflowNotConverged:
                results.append({
                    "outage_line_idx": int(line_idx),
                    "from_bus": from_bus,
                    "to_bus": to_bus,
                    "converged": False,
                    "min_vm_pu": np.nan,
                    "worst_bus": -1,
                    "max_vm_pu": np.nan,
                    "max_loading_pct": np.nan,
                    "worst_line_idx": -1,
                    "voltage_violations": -1,
                    "thermal_overloads": -1,
                    "status": "DIVERGED",
                })

        df = pd.DataFrame(results)
        return df.sort_values(by=["converged", "min_vm_pu"], ascending=[True, True]).reset_index(drop=True)

    def simulate_high_load_integration(self, target_bus: int = 29, p_mw: float = 15.0, q_mvar: float = 5.0) -> pp.pandapowerNet:
        """
        Clones the base network and integrates a large industrial/data center load
        at the specified bus to stress-test voltage stability.
        """
        stressed_net = copy.deepcopy(self.net)
        pp.create_load(
            stressed_net,
            bus=target_bus,
            p_mw=p_mw,
            q_mvar=q_mvar,
            name=f"High_Load_Bus_{target_bus}",
        )
        return stressed_net

    def size_shunt_capacitor(
        self,
        stressed_net: pp.pandapowerNet,
        target_bus: int = 29,
        step_mvar: float = 2.0,
        max_mvar: float = 40.0,
    ) -> tuple[pp.pandapowerNet, float]:
        """
        Iteratively sizes a shunt capacitor bank at the target bus until all bus
        voltages meet the minimum ANSI/IEEE threshold (default 0.95 p.u.).
        """
        q_mvar = 0.0
        while q_mvar <= max_mvar:
            test_net = copy.deepcopy(stressed_net)
            if q_mvar > 0:
                pp.create_shunt_as_capacitor(
                    test_net,
                    bus=target_bus,
                    q_mvar=q_mvar,
                    loss_factor=0.0,
                    name=f"Cap_Bank_{q_mvar}MVAr",
                )
            pp.runpp(test_net)
            if test_net.res_bus["vm_pu"].min() >= self.v_min_pu:
                return test_net, q_mvar
            q_mvar += step_mvar

        return test_net, max_mvar
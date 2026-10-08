from pathlib import Path
import numpy as np
from data_import import import_results
from result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results, load_ref_u
from plotting import plot_variables, plot_series, plot_smthng
from processing import *
import matplotlib.pyplot as plt
import pandas as pd
from plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots
from matplotlib.patches import Patch
from matplotlib.colors import to_rgb

PROJECT_ROOT = Path(__file__).resolve().parent
RAWDATA_DIR = (PROJECT_ROOT / "rawdata")
REF_U_DIR = (PROJECT_ROOT / "target_u")

if __name__ == "__main__":

    X_LABEL = "Deviation metric"
    Y_LABEL = r"$\Delta U_{PID}$, V"
    FILENAME = "U_dev_by_lgt"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0, 10, 20, 30]
    p_set = [10, 400]
    r_set = [30]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    lift_u_ds, tilt_u_ds = load_ref_u(REF_U_DIR)
    u_ds = realign_u(lift_u_ds, tilt_u_ds)

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    for case_id in case_set:
        datasets[case_id] = align_to_reference(u_ds, datasets[case_id])
        datasets[case_id] = smooth_series(datasets[case_id], "Lift_U", key_smooth="Lift_U_smooth", window=200)
        datasets[case_id] = smooth_series(datasets[case_id], "Tilt_U", key_smooth="Tilt_U_smooth", window=200)

    plot_df = pd.DataFrame()
    res_tup_list = list()

    for case_id in case_set:
        lift_dev = datasets[case_id]["Lift_U_smooth"].to_numpy() - u_ds["Lift_U"].to_numpy()
        tilt_dev = datasets[case_id]["Tilt_U_smooth"].to_numpy() - u_ds["Tilt_U"].to_numpy()

        lift_max = np.max(np.abs(lift_dev))
        lift_mean = np.mean(np.abs(lift_dev))
        lift_spread = np.std(lift_dev)

        tilt_max = np.max(np.abs(tilt_dev))
        tilt_mean = np.mean(np.abs(tilt_dev))
        tilt_spread = np.std(tilt_dev)

        res_tup_list.append((case_id, lift_max, lift_mean, lift_spread, tilt_max, tilt_mean, tilt_spread))

    sorted_res = sorted(res_tup_list)
    plot_df["lgt"] = [sol[0][0] for sol in sorted_res]
    plot_df["pld"] = [sol[0][1] for sol in sorted_res]
    plot_df["rfp"] = [sol[0][2] / 10 for sol in sorted_res]
    plot_df["Lift max deviation"] = [sol[1] for sol in sorted_res]
    plot_df["Lift mean deviation"] = [sol[2] for sol in sorted_res]
    plot_df["Lift spread deviation"] = [sol[3] for sol in sorted_res]
    plot_df["Tilt max deviation"] = [sol[4] for sol in sorted_res]
    plot_df["Tilt mean deviation"] = [sol[5] for sol in sorted_res]
    plot_df["Tilt spread deviation"] = [sol[6] for sol in sorted_res]
    plot_df.to_csv(f"{FILENAME}.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    base_colors = {10: "#ff8c00", 400: "#d62728"}
    saturation = {0: 1.0, 10: 0.80, 20: 0.60, 30: 0.40}
    color_map = dict()

    for pld in p_set:
        rgb = np.array(to_rgb(base_colors[pld]))
        for lgt in l_set:
            s = saturation[lgt]
            color_map[(pld, lgt)] = tuple(1.0 - s * (1.0 - rgb))

    legend_handles = [Patch(facecolor=color_map[(pld, lgt)], edgecolor="black", label=f"{pld} kg, {lgt}%") for pld in p_set for lgt in l_set]

    metrics = ["Maximum", "Mean", "Spread"]
    x = np.arange(len(metrics))
    width = 0.095

    for valve in ["Lift", "Tilt"]:
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)

        i = 0
        for pld in p_set:
            for lgt in l_set:
                row = plot_df[(plot_df["pld"] == pld) & (plot_df["lgt"] == lgt)].iloc[0]

                if valve == "Lift":
                    vals = [row["Lift max deviation"], row["Lift mean deviation"], row["Lift spread deviation"]]
                else:
                    vals = [row["Tilt max deviation"], row["Tilt mean deviation"], row["Tilt spread deviation"]]

                offset = (i - 3.5) * width
                plt.bar(x + offset, vals, width=width, color=color_map[(pld, lgt)], edgecolor="black", linewidth=0.8)
                i += 1

        plt.ylabel(Y_LABEL, fontsize=18)
        plt.xticks(x, metrics, fontsize=18)
        plt.yticks(fontsize=18)
        plt.title(f"{valve} PID control correction", fontsize=18)
        plt.grid(True, axis="y")

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.23)
        plt.savefig(f"figures/OUTPUT_{FILENAME}_{valve.lower()}.pdf", format="pdf", bbox_inches="tight")

        fig_legend = plt.figure(figsize=(10, 1))

        fig_legend.legend(handles=legend_handles, loc="center", ncol=4, fontsize=16, frameon=False, columnspacing=2.9, handletextpad=0.5, handlelength=2.2)
        #fig_legend.legend(handles=legend_handles, fontsize=16, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4, frameon=False)
        fig_legend.savefig(f"figures/LEGEND_{FILENAME}_{valve.lower()}.pdf", bbox_inches="tight", pad_inches=0.05)

        plt.show()
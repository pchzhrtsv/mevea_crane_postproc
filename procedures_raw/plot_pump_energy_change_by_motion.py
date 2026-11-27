from pathlib import Path
import numpy as np
from utils.data_import import import_results
from utils.result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results
from utils.plotting import plot_variables, plot_series, plot_smthng
from utils.processing import *
import matplotlib.pyplot as plt
import pandas as pd
from utils.plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots
from matplotlib.patches import Patch
from matplotlib.colors import to_rgb

from utils.paths import CSV_DIR, DATA_DIR, FIGURES_DIR

if __name__ == "__main__":
    FILENAME = "Energy_change_by_motion"
    X_LABEL = "Motion"
    Y_LABEL = r"$\delta W_{s}$, %"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0, 10, 20, 30]
    p_set = [10, 400]
    r_set = [30]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(DATA_DIR, case_set))

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    motion_set = [("I", 2.5, 8.5), ("II", 8.5, 15.0), ("III", 15.0, 21.0), ("IV", 21.0, None)]
    fs = 20
    fig_size = (6.48, 4.40)
    plot_df = pd.DataFrame()
    res_tup_list = list()

    for pld in p_set:
        ref_case_id = (0, pld, 30)
        ref_ds = datasets[ref_case_id]

        aligned_datasets = dict()

        for lgt in l_set:
            case_id = (lgt, pld, 30)

            if lgt == 0:
                ds = ref_ds.copy()
            else:
                ds = align_to_reference(ref_ds, datasets[case_id])

            power_df = pd.DataFrame()
            power_df["Time"] = ds["Time"]
            power_df["Pump_Q"] = ds["Pump_Q"]
            power_df["VolPump_p"] = ds["VolPump_p"]

            power_df = clean_spikes(power_df, "Pump_Q", key_clean="Pump_Q", window=20)
            power_df = clean_spikes(power_df, "VolPump_p", key_clean="VolPump_p", window=20)

            power_df["Pump_P"] = (power_df["VolPump_p"] - 1) * power_df["Pump_Q"] / 60000 * 1e5 / 1e3

            aligned_datasets[lgt] = power_df

        for motion, t_start, t_end in motion_set:
            ref_motion_ds = aligned_datasets[0]

            if t_end is None:
                ref_mask = ref_motion_ds["Time"] >= t_start
            else:
                ref_mask = (ref_motion_ds["Time"] >= t_start) & (ref_motion_ds["Time"] < t_end)

            ref_time = ref_motion_ds.loc[ref_mask, "Time"].to_numpy()
            ref_power = ref_motion_ds.loc[ref_mask, "Pump_P"].to_numpy()
            w_0 = np.trapezoid(ref_power, ref_time)

            for lgt in l_set[1:]:
                ds = aligned_datasets[lgt]

                if t_end is None:
                    mask = ds["Time"] >= t_start
                else:
                    mask = (ds["Time"] >= t_start) & (ds["Time"] < t_end)

                time = ds.loc[mask, "Time"].to_numpy()
                power = ds.loc[mask, "Pump_P"].to_numpy()
                w_lgt = np.trapezoid(power, time)

                delta_w = (w_lgt - w_0) / w_0 * 100.0

                res_tup_list.append((pld, lgt, motion, w_0, w_lgt, delta_w))

    plot_df["pld"] = [sol[0] for sol in res_tup_list]
    plot_df["lgt"] = [sol[1] for sol in res_tup_list]
    plot_df["motion"] = [sol[2] for sol in res_tup_list]
    plot_df["W_0"] = [sol[3] for sol in res_tup_list]
    plot_df["W_lgt"] = [sol[4] for sol in res_tup_list]
    plot_df["dW"] = [sol[5] for sol in res_tup_list]
    plot_df.to_csv(CSV_DIR / f"{FILENAME}.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    saturation = {10: 0.80, 20: 0.60, 30: 0.40}
    base_colors = {"positive": "#d62728", "negative": "#008000"}
    color_map = dict()

    for sign in ["positive", "negative"]:
        rgb = np.array(to_rgb(base_colors[sign]))
        for lgt in l_set[1:]:
            s = saturation[lgt]
            color_map[(sign, lgt)] = tuple(1.0 - s * (1.0 - rgb))

    motions = ["I", "II", "III", "IV"]
    group_spacing=0.9
    x = np.arange(len(motions)) * group_spacing
    width = 0.25

    for pld in p_set:
        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111)

        for i, lgt in enumerate(l_set[1:]):
            vals = list()

            for motion in motions:
                row = plot_df[(plot_df["pld"] == pld) & (plot_df["lgt"] == lgt) & (plot_df["motion"] == motion)].iloc[0]
                vals.append(row["dW"])

            vals = np.array(vals)
            colors = [color_map[("positive", lgt)] if val >= 0 else color_map[("negative", lgt)] for val in vals]
            offset = (i - 1) * width

            bars = ax.bar(x + offset, vals, width=width, color=colors, edgecolor="black", linewidth=0.8, zorder=3)

            for bar, val in zip(bars, vals):
                x_text = bar.get_x() + bar.get_width() / 2
                y_text = val + 0.02 if val >= 0 else val - 0.04
                va_text = "bottom" if val >= 0 else "top"
                ax.text(x_text, y_text, f"{val:.1f}", ha="center", va=va_text, fontsize=fs, rotation=90, zorder=3)

        ax.axhline(0, color="black", linewidth=1.5)
        ax.set_xlabel(X_LABEL, fontsize=fs)
        ax.set_ylabel(Y_LABEL, fontsize=fs)
        ax.set_xticks(x)
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(-6, 15)
        ax.set_xticklabels(motions, fontsize=fs)
        ax.tick_params(axis="y", labelsize=fs)
        ax.grid(True, axis="y", zorder=0)
        #plt.title(f"Payload: {pld} kg", fontsize=fs)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}_{pld}kg.pdf", format="pdf", bbox_inches="tight")
        plt.show()

    legend_handles = list()

    for lgt in l_set[1:]:
        legend_handles.append(Patch(facecolor=color_map[("negative", lgt)], edgecolor="black", label=f"L={lgt}%; Energy decrease"))
        legend_handles.append(Patch(facecolor=color_map[("positive", lgt)], edgecolor="black", label=f"L={lgt}%; Energy increase"))

    fig_legend = plt.figure(figsize=(12.96, 1.5))
    fig_legend.legend(handles=legend_handles, loc="center", ncol=3, fontsize=10, frameon=False)
    fig_legend.savefig(FIGURES_DIR / f"LEGEND_{FILENAME}.pdf", bbox_inches="tight",)
    plt.show()

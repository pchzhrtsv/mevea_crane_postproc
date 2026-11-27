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
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from tqdm import tqdm
import time

from utils.paths import CSV_DIR, FIGURES_DIR, RAWDATA_DIR

if __name__ == "__main__":
    folder = Path(RAWDATA_DIR)
    if not (folder.is_dir() and any(f.is_file() for f in folder.iterdir())):
        raise FileNotFoundError("This procedure requires specific rawdata dataset. Please, contact the developer.")

    X_LABEL = "Reference pressure, bar"
    Y_LABEL = r"$\frac{W_{30\%}-W_{0\%}}{W_{0\%}}$,  %"
    #TITLE = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$"
    FILENAME = "dW_by_LP"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    refp_l = [10,20,30,40]

    Z_MIN = -15
    Z_MAX = 5
    zero_pos = (0 - Z_MIN) / (Z_MAX - Z_MIN)

    cmap = LinearSegmentedColormap.from_list("green_yellow_red", [(0.0, "green"), (zero_pos, "yellow"), (1.0, "red")])
    norm = Normalize(vmin=Z_MIN, vmax=Z_MAX)
    levels_fill = np.linspace(Z_MIN, Z_MAX, 201)
    levels_lines = np.arange(Z_MIN, Z_MAX + 1, 1)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""
    for refp in refp_l:
        print(f"Processing reference pressure = {refp}")
        time.sleep(0.5)
        datasets = dict()
        l_set = [i for i in range(31)]
        p_set = [10*(i+1) for i in range(40)]
        r_set = [refp]
        case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
        datasets.update(load_specific_results(RAWDATA_DIR, case_set))

        """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""
        cutted_datasets = start_from(datasets, 2.5)

        plot_df = pd.DataFrame()
        res_tup_list = list()

        total_cases = sum(1 for c in case_set if c[0] != 0 and c[1] in p_set)

        with tqdm(total=total_cases, desc="Calculating cases", unit="case") as pbar:
            for p in p_set:
                cases_p = [case for case in case_set if case[1] == p]
                c0 = (0, p, refp)
                datasets[c0] = clean_spikes(datasets[c0], "Pump_Q", key_clean="Pump_Q", window=20)
                datasets[c0] = clean_spikes(datasets[c0], "VolPump_p", key_clean="VolPump_p", window=20)
                w_0 = pump_work(datasets[c0])
                for c in cases_p:
                    if c[0] == 0:
                        continue
                    datasets[c] = clean_spikes(datasets[c], "Pump_Q", key_clean="Pump_Q", window=20)
                    datasets[c] = clean_spikes(datasets[c], "VolPump_p", key_clean="VolPump_p", window=20)
                    w_c = pump_work(datasets[c])
                    delta_w = (w_c - w_0) / w_0 * 100
                    res_tup_list.append((c[0], c[1], delta_w))
                    pbar.update(1)

        x1 = [sol[0] for sol in sorted(res_tup_list)]
        x2 = [sol[1] for sol in sorted(res_tup_list)]
        y = [sol[2] for sol in sorted(res_tup_list)]

        plot_df["L"] = x1
        plot_df["P"] = x2
        plot_df["dW"] = y
        plot_df.to_csv(CSV_DIR / f"{FILENAME}_{refp}.csv", index=False)

        """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)

        surface_df = plot_df.pivot_table(index="L", columns="P", values="dW", aggfunc="mean")
        surface_df = surface_df.sort_index()
        surface_df = surface_df.sort_index(axis=1)

        P_values = surface_df.columns.to_numpy()
        L_values = surface_df.index.to_numpy()
        Z = surface_df.to_numpy()

        X, Y = np.meshgrid(P_values, L_values)
        Z = np.ma.masked_invalid(Z)

        surf = ax.contourf(X, Y, Z, levels=levels_fill, cmap=cmap, norm=norm, extend="both")

        cs = ax.contour(X, Y, Z, levels=levels_lines, colors="black", linewidths=0.6, alpha=0.75)

        nonzero_levels = [level for level in cs.levels if level != 0]

        ax.clabel(cs, levels=nonzero_levels, inline=True, fmt=lambda value: f"{value:.0f}%", fontsize=18)

        ax.contour(X, Y, Z, levels=[0], colors="white", linewidths=3.0)

        cs_zero = ax.contour(X, Y, Z, levels=[0], colors="black", linewidths=1.8)

        ax.clabel(cs_zero, levels=[0], inline=True, fmt={0: "0%"}, fontsize=18)

        ax.set_xlabel("Payload, kg", labelpad=12, fontsize=18)
        ax.set_ylabel("Lightening, %", labelpad=12, fontsize=18)

        ax.tick_params(axis="x", labelsize=18)
        ax.tick_params(axis="y", labelsize=18)

        ax.set_xlim(P_values.min(), P_values.max())
        ax.set_ylim(L_values.min(), L_values.max())

        ax.grid(True, linewidth=0.4, alpha=0.4)

        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}_{refp}_hm.pdf", format="pdf", bbox_inches="tight")
        plt.show(block=False)
        plt.pause(0.5)
        plt.close(fig)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| COLORBAR ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    fig = plt.figure(figsize=(2.2, 7.2))
    ax = fig.add_subplot(111)

    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(sm, cax=ax, extend="both")
    cbar.set_label("Consumption change, %", fontsize=18, labelpad=12)
    cbar.set_ticks(np.arange(Z_MIN, Z_MAX + 1, 5))
    cbar.ax.tick_params(labelsize=14)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}_colorbar.pdf", format="pdf", bbox_inches="tight")
    plt.show(block=False)
    plt.pause(0.5)
    plt.close(fig)

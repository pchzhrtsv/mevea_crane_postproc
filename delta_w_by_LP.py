from pathlib import Path
import numpy as np
from data_import import import_results
from result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results
from plotting import plot_variables, plot_series, plot_smthng
from processing import *
import matplotlib.pyplot as plt
# import pandas as pd
from plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.cm import ScalarMappable
from tqdm import tqdm
import time

PROJECT_ROOT = Path(__file__).resolve().parent
RAWDATA_DIR = (PROJECT_ROOT / "rawdata")

if __name__ == "__main__":

    X_LABEL = "Reference pressure, bar"
    Y_LABEL = r"$\frac{W_{30\%}-W_{0\%}}{W_{0\%}}$,  %"
    #TITLE = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$"
    FILENAME = "dW_by_LP"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    refp_l = [10,20,30,40]

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
        cutted_datasets = start_from(datasets, 2.4)

        plot_df = pd.DataFrame()
        res_tup_list = list()

        total_cases = sum(
            1 for c in case_set
            if c[0] != 0 and c[1] in p_set
        )
        with tqdm(total=total_cases, desc="Calculating cases", unit="case") as pbar:
            for p in p_set:
                cases_p = [case for case in case_set if case[1] == p]
                c0 = (0, p, refp)
                datasets[c0] = clean_spikes(datasets[c0], "Pump_Q", key_clean="Pump_Q", window=20)
                datasets[c0] = clean_spikes(datasets[c0], "VolPump_p", key_clean="VolPump_p", window=20)
                w_0 = pump_work(datasets[c0])
                for c in cases_p:
                    if c[0]==0:
                        continue
                    datasets[c] = clean_spikes(datasets[c], "Pump_Q", key_clean="Pump_Q", window=20)
                    datasets[c] = clean_spikes(datasets[c], "VolPump_p", key_clean="VolPump_p", window=20)
                    w_c = pump_work(datasets[c])
                    delta_w = (w_c - w_0) / w_0 * 100
                    res_tup_list.append((c[0],c[1], delta_w))
                    pbar.update(1)
        x1 = [sol[0] for sol in sorted(res_tup_list)]
        x2 = [sol[1] for sol in sorted(res_tup_list)]
        y =  [sol[2] for sol in sorted(res_tup_list)]
        plot_df["L"] = x1
        plot_df["P"] = x2
        plot_df["dW"] = y
        plot_df.to_csv(f"{FILENAME}.csv", index=False)

        """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

        fig = plt.figure(figsize=(12.8, 9.6))

        ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
        surface_df = plot_df.pivot_table(index="L", columns="P", values="dW", aggfunc="mean")

        P_values = surface_df.columns.to_numpy()
        L_values = surface_df.index.to_numpy()
        Z = surface_df.to_numpy()

        X, Y = np.meshgrid(P_values, L_values)
        # x = plot_df["P"].to_numpy()
        # y = plot_df["L"].to_numpy()
        # dW = plot_df["dW"].to_numpy()
        # z = np.zeros_like(dW)

        # unique_P = np.sort(plot_df["P"].unique())
        # unique_L = np.sort(plot_df["L"].unique())
        #
        # dx = 0.7 * np.min(np.diff(unique_P)) if len(unique_P) > 1 else 1.0
        # dy = 0.7 * np.min(np.diff(unique_L)) if len(unique_L) > 1 else 1.0
        zero_tol = 0.1
        # max_abs = np.max(np.abs(dW))
        max_abs = np.nanmax(np.abs(Z))

        cmap = LinearSegmentedColormap.from_list("green_gray_red", ["green", "yellow", "red"])

        norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)
        # colors = cmap(norm(dW))
        Z0 = np.zeros_like(Z)


        surf = ax.plot_surface(X, Y, Z, cmap=cmap, norm=norm, edgecolor="black", linewidth=0.4, antialiased=True, shade=False)
        ax.plot_surface(X, Y, np.zeros_like(Z), color="lightgray", alpha=0.2, edgecolor="none", shade=False)
        fig_tmp, ax_tmp = plt.subplots()

        cs = ax_tmp.contour(X, Y, Z, levels=[0])
        plt.close(fig_tmp)
        eps = 0.01

        for segment in cs.allsegs[0]:
            xx = segment[:, 0]
            yy = segment[:, 1]
            zz = np.full(len(segment), eps)

            ax.plot(xx, yy, zz, color="white", linewidth=2, zorder=19)

            ax.plot(xx, yy, zz, color="black", linewidth=1, zorder=20, linestyle="--")

            ax.scatter(xx, yy, zz, s=18, color="black", edgecolors="white", linewidths=0.8, depthshade=False, zorder=21)


        # ax.bar3d(x - dx / 2, y - dy / 2, z, dx, dy, dW, color=colors, shade=True, edgecolor="black", linewidth=0.6)
        # offset = 0.03 * max_abs
        # for xi, yi, dzi in zip(x, y, dW):
        #
        #     if dzi >= 0:
        #         z_text = dzi + offset
        #     else:
        #         z_text = offset
        #
        #     ax.text(xi, yi, z_text, f"{dzi:.1f}%", ha="center", va="bottom", fontsize=10)



        ax.set_xlabel("Payload, kg", labelpad=12, fontsize=18)
        ax.set_ylabel("Lightening, %", labelpad=12, fontsize=18)
        ax.set_zlabel("Consumption change, %", labelpad=12, fontsize=18)

        ax.tick_params(axis="x", labelsize=14)
        ax.tick_params(axis="y", labelsize=14)
        ax.tick_params(axis="z", labelsize=14)

        ax.scatter(X, Y, Z, s=30, edgecolors="black", depthshade=False, zorder=22)
        #ax.set_title("Consumption change vs. payload and lightening\nReference pressure = 30 bar", pad=20)

        ax.view_init(elev=25, azim=-45)

        # sm = ScalarMappable(norm=norm, cmap=cmap)
        # sm.set_array([])

        cbar = fig.colorbar(surf, ax=ax, pad=0.1, shrink=0.75)

        #cbar.set_label("Consumption change, %", fontsize=18)

        cbar.ax.tick_params(labelsize=12)
        plt.tight_layout()
        plt.savefig(f"figures/OUTPUT_{FILENAME}_{refp}.pdf", format="pdf")
        plt.show(block=False)
        plt.pause(0.5)
        plt.close(fig)

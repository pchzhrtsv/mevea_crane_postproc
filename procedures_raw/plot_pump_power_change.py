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

from utils.paths import DATA_DIR, FIGURES_DIR
RAWDATA_DIR = DATA_DIR
FILENAME = "Power_difference"

if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL = r"$\Delta P_{\mathrm{pump}}$, kW"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0, 30]
    p_set = [10, 400]
    r_set = [350]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_dfs = dict()
    fs = 20
    fig_size = (6.48, 4.40)
    for pld in p_set:
        ref_case_id = (0, pld, 350)
        light_case_id = (30, pld, 350)

        ref_ds = datasets[ref_case_id]
        datasets[light_case_id] = align_to_reference(ref_ds, datasets[light_case_id])

        plot_df = pd.DataFrame()
        plot_df["Time"] = ref_ds.Time
        plot_df["P_0"] = (ref_ds.VolPump_p-1)*ref_ds.Pump_Q/60000*1e5/1e3
        plot_df["P_30"] = (datasets[light_case_id].VolPump_p-1)*datasets[light_case_id].Pump_Q/60000*1e5/1e3

        plot_df = clean_spikes(plot_df, "P_0", key_clean="P_0", window=50)
        plot_df = clean_spikes(plot_df, "P_30", key_clean="P_30", window=50)
        plot_df = smooth_series(plot_df, "P_0", key_smooth="P_0", window=200)
        plot_df = smooth_series(plot_df, "P_30", key_smooth="P_30", window=200)

        plot_df["dP"] = plot_df["P_30"] - plot_df["P_0"]

        plot_dfs[pld] = plot_df

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    for pld in p_set:
        plot_df = plot_dfs[pld]

        time = plot_df["Time"].to_numpy()
        dP = plot_df["dP"].to_numpy()

        dP_positive = np.ma.masked_where(dP < 0, dP)
        dP_negative = np.ma.masked_where(dP >= 0, dP)

        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111)

        ax.plot(time, dP_positive, color="red", linewidth=2.0)
        ax.plot(time, dP_negative, color="green", linewidth=2.0)

        ax.fill_between(time, 0, dP, where=dP >= 0, facecolor="none", edgecolor="red", hatch="///", linewidth=0.0, interpolate=True)
        ax.fill_between(time, 0, dP, where=dP < 0, facecolor="none", edgecolor="green", hatch="\\\\\\", linewidth=0.0, interpolate=True)

        motion_times = [0, 2.5, 8.5, 15, 21, plot_df["Time"].max()]
        motion_labels = ["0", "I", "II", "III", "IV"]

        for t in motion_times[1:-1]:
            ax.axvline(t, color="black", linestyle="--", linewidth=1.2)

        for i in range(len(motion_labels)):
            if i % 2 == 0:
                ax.axvspan(motion_times[i], motion_times[i+1], color="black", alpha=0.035)

            x_mid = (motion_times[i] + motion_times[i+1]) / 2
            ax.text(x_mid, 0.07, motion_labels[i], ha="center", va="top", fontsize=fs, transform=ax.get_xaxis_transform(), clip_on=False)

        ax.axhline(0, color="black", linewidth=1.8, zorder=5)
        ax.set_xlim(0, plot_df["Time"].max())
        ax.yaxis.set_label_coords(-0.1, 0.5)
        plt.xlabel(X_LABEL, fontsize=fs)
        plt.ylabel(Y_LABEL, fontsize=fs)
        plt.xticks(fontsize=fs)
        plt.yticks(fontsize=fs)
        #plt.title(f"Payload {pld} kg", fontsize=fs)
        plt.grid(True)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.17)
        plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}_{pld}kg.pdf", format="pdf", bbox_inches="tight")
        plt.show()

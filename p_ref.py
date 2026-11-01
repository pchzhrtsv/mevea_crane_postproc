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

PROJECT_ROOT = Path(__file__).resolve().parent
RAWDATA_DIR = (PROJECT_ROOT / "refpress_data")
FILENAME = "Power_plot"
if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL = "Pump Power, kW"
    TITLE = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0]
    p_set = [10, 400]
    r_set = [350]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.DataFrame()

    ref_case_id = (0,10,350)
    ref_ds = datasets[ref_case_id]
    plot_df["Time"] = ref_ds.Time
    for case_id in case_set:
        datasets[case_id] = align_to_reference(ref_ds, datasets[case_id])
        plot_df[case_id] = (datasets[case_id].VolPump_p-1)*datasets[case_id].Pump_Q/60000*1e5/1e3
        plot_df = clean_spikes(plot_df, case_id, key_clean=case_id, window=20)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""
    fs = 20
    fig_size = (6.48, 5.40)
    fig = plt.figure(figsize=fig_size)
    ax = fig.add_subplot(111)

    for column in plot_df.columns:
        if column != "Time":
            curve_label = f"Payload: {column[1]} kg"
            ax.plot(plot_df["Time"], plot_df[column], label=curve_label)

    motion_times = [0, 2.5, 8.5, 15, 21, plot_df["Time"].max()]
    motion_labels = ["Motion 0", "Motion I", "Motion II", "Motion III", "Motion IV"]

    for t in motion_times[1:-1]:
        ax.axvline(t, color="black", linestyle="--", linewidth=1.2)

    for i in range(len(motion_labels)):
        if i % 2 == 0:
            ax.axvspan(motion_times[i], motion_times[i+1], color="black", alpha=0.05)

        x_mid = (motion_times[i] + motion_times[i+1]) / 2
        ax.text(x_mid, -0.1, motion_labels[i], ha="center", va="top", fontsize=fs, transform=ax.get_xaxis_transform(), clip_on=False)

    ax.set_xlim(0, plot_df["Time"].max())

    ax.axhline(0, color="black", linewidth=1.8, zorder=5)

    plt.xlabel(X_LABEL, fontsize=fs)
    plt.ylabel(Y_LABEL, fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    #plt.title(TITLE, fontsize=fs)
    plt.grid(True)
    plt.legend(fontsize=fs)
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.17)
    plt.savefig(f"figures/OUTPUT_{FILENAME}.pdf", format="pdf", bbox_inches="tight")
    plt.show()
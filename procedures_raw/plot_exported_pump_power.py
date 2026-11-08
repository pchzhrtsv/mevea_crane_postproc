from pathlib import Path
import numpy as np
from utils.data_import import import_results
from utils.result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results
from utils.plotting import plot_variables, plot_series, plot_smthng
from utils.processing import *
import matplotlib.pyplot as plt
# import pandas as pd
from utils.plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots

from utils.paths import DATA_DIR, FIGURES_DIR
RAWDATA_DIR = DATA_DIR
FILENAME = "Power_plot"
if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL = "Pump Power, W"
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
        plot_df[case_id] = datasets[case_id].Pump_P
        plot_df = clean_spikes(plot_df, case_id, key_clean=case_id, window=20)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plt.figure(figsize=(14, 8))

    for column in plot_df.columns:
        if column != "Time":
            curve_label = f"Payload: {column[1]} kg"
            plt.plot(plot_df["Time"], plot_df[column], label=curve_label)


    plt.xlabel(X_LABEL,  fontsize=18)
    plt.ylabel(Y_LABEL,  fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    #plt.title(TITLE, fontsize=18)
    plt.grid(True)
    plt.legend(fontsize=16)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}.pdf", format="pdf")
    plt.show()


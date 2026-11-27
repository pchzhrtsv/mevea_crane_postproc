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

from utils.paths import CSV_DIR, DATA_DIR, FIGURES_DIR, REFPRESS_DIR

if __name__ == "__main__":
    folder = Path(REFPRESS_DIR)
    if not (folder.is_dir() and any(f.is_file() for f in folder.iterdir())):
        raise FileNotFoundError("This procedure requires specific dataset with reference pressure analysis. Please, contact the developer.")
    X_LABEL = r"$\Delta p_{\mathrm{LS}}$, bar"
    Y_LABEL = r"$\delta W_{pump}$, %"
    #TITLE = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0,30]
    p_set = [10,400]
    r_set = [int(i/2*10) for i in range(10,81)]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(REFPRESS_DIR, case_set))
    datasets = start_from(datasets, 2.5)
    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.DataFrame()

    for p in p_set:
        res_tup_list = list()
        cases_0 = [case for case in case_set if case[0] == 0]
        for c0 in cases_0:
            if c0[1] == p:
                datasets[c0] = clean_spikes(datasets[c0], "Pump_Q", key_clean="Pump_Q", window=20)
                datasets[c0] = clean_spikes(datasets[c0], "VolPump_p", key_clean="VolPump_p", window=20)
                w_0 = pump_work(datasets[c0])
                c30 = (30, c0[1], c0[2])
                datasets[c30] = clean_spikes(datasets[c30], "Pump_Q", key_clean="Pump_Q", window=20)
                datasets[c30] = clean_spikes(datasets[c30], "VolPump_p", key_clean="VolPump_p", window=20)
                w_30 = pump_work(datasets[c30])
                delta_w = (w_30 - w_0) / w_0 * 100
                res_tup_list.append((c0[2], delta_w))
        x = [sol[0]/10 for sol in sorted(res_tup_list)]
        y = [sol[1] for sol in sorted(res_tup_list)]
        plot_df["p_ref"] = x
        plot_df[p] = y
    plot_df.to_csv(CSV_DIR / "delta_w_by_rfp.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plt.figure(figsize=(12.8, 7.2))

    for column in plot_df.columns:
        if column != "p_ref":
            curve_label = f"Payload: {column} kg"
            plt.plot(plot_df["p_ref"], plot_df[column], label=curve_label, linewidth=1, marker="o", markersize=4)


    plt.xlabel(X_LABEL,  fontsize=18)
    plt.ylabel(Y_LABEL,  fontsize=18)
    plt.hlines(y=0, xmin=3, xmax=42, linewidth=1, color='black')
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    #plt.title(TITLE, fontsize=18)
    plt.grid(True)
    plt.legend(fontsize=18, loc="upper left")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "OUTPUT_delta_w_by_rfp.pdf", format="pdf")
    plt.show()




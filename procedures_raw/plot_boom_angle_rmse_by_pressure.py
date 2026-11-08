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

from utils.paths import CSV_DIR, DATA_DIR, FIGURES_DIR, PROJECT_ROOT
RAWDATA_DIR = DATA_DIR
REFTHETA_DIR = (PROJECT_ROOT / "target_thetas")
if __name__ == "__main__":

    X_LABEL = "Reference pressure, bar"
    Y_LABEL = "RMSE, rad"
    TITLE = "RMS angular boom position error"
    FILENAME = "rmse_by_rfp"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0,30]
    p_set = [10,400]
    r_set = [int(i/2*10) for i in range(10,81)]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    lift_theta_ds, tilt_theta_ds = load_ref_thetas(REFTHETA_DIR)
    thetas_ds = realign_thetas(lift_theta_ds, tilt_theta_ds)

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.DataFrame()

    for p in p_set:
        for l in l_set:
            res_tup_list = list()
            for r in r_set:
                c = (l,p,r)
                datasets[c] = align_to_reference(thetas_ds, datasets[c])

                lift_rmse = np.sqrt(np.mean((datasets[c]["Lift_theta"] - thetas_ds["Lift_theta"]) ** 2))

                tilt_rmse = np.sqrt(np.mean((datasets[c]["Tilt_theta"] - thetas_ds["Tilt_theta"]) ** 2))

                combined_rmse = np.sqrt(lift_rmse ** 2 + tilt_rmse ** 2)

                res_tup_list.append((r, combined_rmse))

            x = [sol[0]/10 for sol in sorted(res_tup_list)]
            y = [sol[1] for sol in sorted(res_tup_list)]
            plot_df["p_ref"] = x
            plot_df[(l,p)] = y
    plot_df.to_csv(CSV_DIR / f"{FILENAME}.csv", index=False)
    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plt.figure(figsize=(12.8, 7.2))

    for column in plot_df.columns:
        if column != "p_ref":
            curve_label = f"Lightening {column[0]}%; payload: {column[1]} kg"
            curve_map = {
                (0,10): ("--", "tab:blue", 'o', "none"),
                (30,10): ("-", "tab:blue", 'o', "full"),
                (0,400): ("--", "tab:orange", 'o', "none"),
                (30,400): ("-", "tab:orange", 'o', "full"),
            }
            plt.plot(plot_df["p_ref"], plot_df[column], label=curve_label, color=curve_map[column][1], linestyle=curve_map[column][0], marker=curve_map[column][2], linewidth=1, markersize=4, fillstyle=curve_map[column][3])

    plt.xlabel(X_LABEL,  fontsize=18)
    plt.ylabel(Y_LABEL,  fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    #plt.title(TITLE, fontsize=18)
    plt.grid(True)
    plt.legend(fontsize=16, loc="upper right")
    plt.tight_layout()
    plt.hlines(y=0, xmin=3, xmax=42, linewidth=1, color='black')
    plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}.pdf", format="pdf")
    plt.show()


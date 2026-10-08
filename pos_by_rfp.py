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
REFTHETA_DIR = (PROJECT_ROOT / "target_thetas")
if __name__ == "__main__":

    X_LABEL = "Reference pressure, bar"
    Y_LABEL = "theta, rad"
    TITLE = "angular boom position"
    FILENAME = "theta_by_rfp"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0]
    p_set = [10]
    r_set = [200]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    lift_theta_ds, tilt_theta_ds = load_ref_thetas(REFTHETA_DIR)
    thetas_ds = realign_thetas(lift_theta_ds, tilt_theta_ds)

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    for case_id in case_set:
        datasets[case_id] = align_to_reference(thetas_ds, datasets[case_id])
        thetas_ds[f"Lift_theta {case_id}"] = datasets[case_id].Lift_theta
        thetas_ds[f"Tilt_theta {case_id}"] = datasets[case_id].Tilt_theta

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plt.figure(figsize=(16.5, 10.8))

    for column in thetas_ds.columns:
        if column != "Time":
            curve_label = f"Lightening: {column[0]}%; payload: {column[1]} kg; ref.pressure: {column[2]} bar"
            plt.plot(thetas_ds["Time"], thetas_ds[column], label=curve_label)

    plt.xlabel(X_LABEL,  fontsize=18)
    plt.ylabel(Y_LABEL,  fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.title(TITLE, fontsize=18)
    plt.grid(True)
    plt.legend(fontsize=16)
    plt.tight_layout()
    plt.show()


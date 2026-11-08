from pathlib import Path
import numpy as np
from utils.data_import import import_results
from utils.result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results,load_ref_u
from utils.plotting import plot_variables, plot_series, plot_smthng
from utils.processing import *
import matplotlib.pyplot as plt
# import pandas as pd
from utils.plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots

from utils.paths import DATA_DIR, FIGURES_DIR, PROJECT_ROOT
RAWDATA_DIR = DATA_DIR
REFTHETA_DIR = (PROJECT_ROOT / "target_thetas")
REF_U_DIR = (PROJECT_ROOT / "target_u")
if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL1 = r"$\Theta$, rad"
    Y_LABEL2 = r"$u_{ref}$, V"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""


    lift_theta_ds, tilt_theta_ds = load_ref_thetas(REFTHETA_DIR)
    thetas_ds = realign_thetas(lift_theta_ds, tilt_theta_ds)
    lift_u_ds, tilt_u_ds = load_ref_u(REF_U_DIR)
    u_ds = realign_u(lift_u_ds, tilt_u_ds)

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""
    fs = 20
    fig_size = (6.48, 5.40)
    fig, ax1 = plt.subplots(figsize=fig_size)
    plt.plot(thetas_ds["Time"], thetas_ds["Lift_theta"], label="Lift boom", linewidth=2, linestyle="--")
    plt.plot(thetas_ds["Time"], thetas_ds["Tilt_theta"], label="Tilt boom", linewidth=2, linestyle="-.")

    plt.xlabel(X_LABEL,  fontsize=fs)
    plt.ylabel(Y_LABEL1,  fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid(True)
    plt.legend(fontsize=fs,    loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3,frameon=False)
    plt.tight_layout()

    plt.savefig(FIGURES_DIR / f"OUTPUT_reference_theta.pdf", format="pdf")

    plt.show()

    fig, ax1 = plt.subplots(figsize=fig_size)
    plt.plot(u_ds["Time"], u_ds["Lift_U"], label="Lift valve", linewidth=2, linestyle="--")
    plt.plot(u_ds["Time"], u_ds["Tilt_U"], label="Tilt valve", linewidth=2, linestyle="-.")
    plt.xlabel(X_LABEL,  fontsize=fs)
    plt.ylabel(Y_LABEL2,  fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid(True)
    plt.legend(fontsize=fs,loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3,frameon=False)
    plt.tight_layout()

    plt.savefig(FIGURES_DIR / f"OUTPUT_reference_u.pdf", format="pdf")

    plt.show()

from pathlib import Path
import numpy as np
from utils.data_import import import_results
from utils.result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results,load_ref_u
from utils.plotting import plot_variables, plot_series, plot_smthng
from utils.processing import *
import matplotlib.pyplot as plt
import tqdm
# import pandas as pd
from utils.plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots

from utils.paths import DATA_DIR, FIGURES_DIR, PROJECT_ROOT
RAWDATA_DIR = DATA_DIR
VALID_DIR = (PROJECT_ROOT / "exp_pressures" )
REF_U_DIR = (PROJECT_ROOT / "target_u")
REFTHETA_DIR = (PROJECT_ROOT / "target_thetas")

if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL_theta = r"$\theta$, rad"
    Y_LABEL_p = r"$p$, bar"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""


    lift_theta_ds, tilt_theta_ds = load_ref_thetas(REFTHETA_DIR)
    thetas_ds = realign_thetas(lift_theta_ds, tilt_theta_ds)

    valid_ds = pd.read_csv(VALID_DIR / "validatio.txt", sep="\t")
    p_ds_LA = pd.read_csv(VALID_DIR / "press1.txt", sep=" ")
    p_ds_LB = pd.read_csv(VALID_DIR / "press2.txt", sep=" ")
    p_ds_TA = pd.read_csv(VALID_DIR / "press3.txt", sep=" ")
    p_ds_TB = pd.read_csv(VALID_DIR / "press4.txt", sep=" ")
    p_ds_P = pd.read_csv(VALID_DIR / "press5.txt", sep=" ")


    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""
    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    fs = 20
    fig_size = (6.48, 5.40)
    fig, ax1 = plt.subplots(figsize=fig_size)
    motion_times = [0, 2.5, 8.5, 15, 21, float(valid_ds.Time.iloc[-1])]
    for t in motion_times[1:-1]:
        ax1.axvline(t, color="black", linestyle="--", linewidth=1.2,
                    zorder=0.5, label="_motion_boundary")
    for i in range(len(motion_times) - 1):
        if i % 2 == 0:
            ax1.axvspan(motion_times[i], motion_times[i + 1], color="black",
                        alpha=0.035, zorder=0, label="_motion_shading")
    plt.plot(valid_ds["Time"], valid_ds["Lift_A_p"], label="Vol.A, model", linewidth=1., color=(0.0,0.3,0.0))
    plt.plot(valid_ds["Time"], valid_ds["Lift_B_p"], label="Vol.B, model", linewidth=1., color=(0.5,0.5,0.1))
    plt.plot(p_ds_LA["Time"], p_ds_LA["Lift_A_p_exp"], label="Vol.A, experiment", linewidth=1.5, linestyle="--", color=(0.4,0.5,0.4))
    plt.plot(p_ds_LB["Time"], p_ds_LB["Lift_B_p_exp"], label="Vol.B, experiment", linewidth=1.5, linestyle="--", color=(0.7,.7,0.1))
    plt.xlabel(X_LABEL,  fontsize=fs)
    plt.ylabel(r"$p_{v, lift}$, bar",  fontsize=fs)
    plt.xlim(0, float(valid_ds.Time.iloc[-1]))
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid(True)
    plt.legend(fontsize=fs, loc='upper center', bbox_to_anchor=(0.45, -0.2), ncol=2, frameon=False, columnspacing=1.,handletextpad=0.4,)
    #plt.title("Lift cylinder chambers pressure" , fontsize=24)
    plt.tight_layout()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"VALIDATION_Lift_press.pdf", format="pdf")
    plt.show()

    fig, ax1 = plt.subplots(figsize=fig_size)
    for t in motion_times[1:-1]:
        ax1.axvline(t, color="black", linestyle="--", linewidth=1.2,
                    zorder=0.5, label="_motion_boundary")
    for i in range(len(motion_times) - 1):
        if i % 2 == 0:
            ax1.axvspan(motion_times[i], motion_times[i + 1], color="black",
                        alpha=0.035, zorder=0, label="_motion_shading")
    plt.plot(valid_ds["Time"], valid_ds["Tilt_A_p"], label="Vol.A, model", linewidth=1., color=(0.0,0.0,0.3))
    plt.plot(valid_ds["Time"], valid_ds["Tilt_B_p"], label="Vol.B, model", linewidth=1., color=(0.1,0.6,0.6))
    plt.plot(p_ds_TA["Time"], p_ds_TA["Tilt_A_p_exp"], label="Vol.A, experiment", linewidth=1.5, linestyle="--", color=(0.4,0.4,0.5))
    plt.plot(p_ds_TB["Time"], p_ds_TB["Tilt_B_p_exp"], label="Vol.B, experiment", linewidth=1.5, linestyle="--", color=(0.1,0.8,0.8))
    plt.xlabel(X_LABEL,  fontsize=fs)
    plt.ylabel(r"$p_{v, tilt}$, bar",  fontsize=fs)
    plt.xlim(0, float(valid_ds.Time.iloc[-1]))
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid(True)
    #plt.title("Tilt cylinder chambers pressure" , fontsize=18)
    plt.legend(fontsize=fs, loc='upper center', bbox_to_anchor=(0.45, -0.2), ncol=2, frameon=False, columnspacing=1.,handletextpad=0.4,)
    plt.tight_layout()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"VALIDATION_Tilt_press.pdf", format="pdf")
    plt.show()

    fig_size = (6.48, 4.86)
    fig, ax1 = plt.subplots(figsize=fig_size)
    plt.plot(thetas_ds["Time"], thetas_ds["Lift_theta"], label=r"Experiment", linewidth=2, linestyle="--",color=(0.6,0.6,0.6))
    plt.plot(valid_ds["Time"], valid_ds["Lift_theta"], label=r"Model", linewidth=1, color=(0.2,0.2,0.2))
    plt.xlabel(X_LABEL,  fontsize=fs)
    plt.ylabel(r"$\Theta_{lift}$, rad.",  fontsize=fs)
    plt.xlim(0, float(valid_ds.Time.iloc[-1]))
    #plt.title("Lift boom angular position" , fontsize=24)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid(True)
    plt.legend(fontsize=fs,loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2,frameon=False)
    plt.tight_layout()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"VALIDATION_Lift_theta.pdf", format="pdf")

    plt.show()

    fig, ax1 = plt.subplots(figsize=fig_size)
    plt.plot(thetas_ds["Time"], thetas_ds["Tilt_theta"], label=r"Experiment", linewidth=2, linestyle="--", color=(0.6,0.6,0.6))
    plt.plot(valid_ds["Time"], valid_ds["Tilt_theta"], label=r"Model", linewidth=1, color=(0.2,0.2,0.2))
    plt.xlabel(X_LABEL,  fontsize=fs)
    plt.ylabel(r"$\Theta_{tilt}$, rad.",  fontsize=fs)
    plt.xlim(0, float(valid_ds.Time.iloc[-1]))
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    #plt.title("Tilt boom angular position" , fontsize=24)
    plt.grid(True)
    plt.legend(fontsize=fs,loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2,frameon=False)
    plt.tight_layout()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"VALIDATION_Tilt_theta.pdf", format="pdf")

    plt.show()

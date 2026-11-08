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

from utils.paths import CSV_DIR, DATA_DIR, FIGURES_DIR
RAWDATA_DIR = DATA_DIR
FILENAME = "Power_balance"

def hose_bulk_modulus(p_bar, beh=7e4, b_min=7e7, b_max=5e8):
    p_pa = np.maximum(p_bar, 0.0)*1e5
    return np.minimum(b_max, np.maximum(beh*np.sqrt(p_pa), b_min))

def hose_volume(length, diameter):
    diameter_m = diameter*0.0254
    return np.pi*diameter_m**2*length/4

if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL = "Power, kW"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    case_id = (0, 10, 300)
    case_set = [case_id]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))
    ds = datasets[case_id]

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.DataFrame()
    plot_df["Time"] = ds.Time

    p_tank = 1.0

    plot_df["P_pump"] = (ds.VolPump_p-p_tank)*ds.Pump_Q/600

    plot_df["P_mech_Lift"] = -ds.Lift_F*ds.Lift_ds/1e6
    plot_df["P_mech_Tilt"] = -ds.Tilt_F*ds.Tilt_ds/1e6

    plot_df["P_hyd_Lift"] = -(ds.Lift_A_p*ds.Lift_A_Q + ds.Lift_B_p*ds.Lift_B_Q)/600
    plot_df["P_hyd_Tilt"] = -(ds.Tilt_A_p*ds.Tilt_A_Q + ds.Tilt_B_p*ds.Tilt_B_Q)/600

    plot_df["P_DV_Lift"] = -((ds.VolPump_p-p_tank)*ds.Lift_DV_QP + (ds.Lift_A_p-p_tank)*ds.Lift_DV_QA + (ds.Lift_B_p-p_tank)*ds.Lift_DV_QB)/600
    plot_df["P_DV_Tilt"] = -((ds.VolPump_p-p_tank)*ds.Tilt_DV_QP + (ds.Tilt_A_p-p_tank)*ds.Tilt_DV_QA + (ds.Tilt_B_p-p_tank)*ds.Tilt_DV_QB)/600

    V_Lift_A = hose_volume(2, 0.5)
    V_Lift_B = hose_volume(2, 0.5)
    V_Tilt_A = hose_volume(3, 0.5)
    V_Tilt_B = hose_volume(3, 0.5)
    V_Pump = hose_volume(0.5, 0.5)

    B_Lift_A = hose_bulk_modulus(ds.Lift_A_p.to_numpy())
    B_Lift_B = hose_bulk_modulus(ds.Lift_B_p.to_numpy())
    B_Tilt_A = hose_bulk_modulus(ds.Tilt_A_p.to_numpy())
    B_Tilt_B = hose_bulk_modulus(ds.Tilt_B_p.to_numpy())
    B_Pump = hose_bulk_modulus(ds.VolPump_p.to_numpy())

    p_Lift_A = ds.Lift_A_p.to_numpy()*1e5
    p_Lift_B = ds.Lift_B_p.to_numpy()*1e5
    p_Tilt_A = ds.Tilt_A_p.to_numpy()*1e5
    p_Tilt_B = ds.Tilt_B_p.to_numpy()*1e5
    p_Pump = (ds.VolPump_p-1).to_numpy()*1e5
    time = ds.Time.to_numpy()

    dp_Lift_A = np.gradient(p_Lift_A, time)
    dp_Lift_B = np.gradient(p_Lift_B, time)
    dp_Tilt_A = np.gradient(p_Tilt_A, time)
    dp_Tilt_B = np.gradient(p_Tilt_B, time)
    dp_Pump = np.gradient(p_Pump, time)

    plot_df["P_hose_Lift_A"] = p_Lift_A*(V_Lift_A/B_Lift_A)*dp_Lift_A/1000
    plot_df["P_hose_Lift_B"] = p_Lift_B*(V_Lift_B/B_Lift_B)*dp_Lift_B/1000
    plot_df["P_hose_Tilt_A"] = p_Tilt_A*(V_Tilt_A/B_Tilt_A)*dp_Tilt_A/1000
    plot_df["P_hose_Tilt_B"] = p_Tilt_B*(V_Tilt_B/B_Tilt_B)*dp_Tilt_B/1000
    plot_df["P_hose_Pump"] = p_Pump*(V_Pump/B_Pump)*dp_Pump/1000

    c_joint = 2000

    omega_PillarLift = np.deg2rad(ds.PillarLift_dtheta)
    omega_LiftTilt = np.deg2rad(ds.LiftTilt_dtheta)
    omega_LiftBracket1 = np.deg2rad(ds.LiftBracket1_dtheta)
    omega_Bracket1Bracket2 = np.deg2rad(ds.Bracket1Bracket2_dtheta)
    omega_Bracket2Tilt = np.deg2rad(ds.Bracket2Tilt_dtheta)

    plot_df["P_damp_sum"] = c_joint*(omega_PillarLift**2 + omega_LiftTilt**2 + omega_LiftBracket1**2 + omega_Bracket1Bracket2**2 + omega_Bracket2Tilt**2)/1000

    clean_keys = ["P_pump", "P_mech_Lift", "P_mech_Tilt", "P_hyd_Lift", "P_hyd_Tilt", "P_DV_Lift", "P_DV_Tilt", "P_hose_Lift_A", "P_hose_Lift_B","P_hose_Pump", "P_hose_Tilt_A", "P_hose_Tilt_B", "P_damp_sum"]

    for key in clean_keys:
        plot_df = clean_spikes(plot_df, key, key_clean=key, window=50)

    plot_df["P_fric_Lift"] = plot_df["P_hyd_Lift"] - plot_df["P_mech_Lift"]
    plot_df["P_fric_Tilt"] = plot_df["P_hyd_Tilt"] - plot_df["P_mech_Tilt"]

    plot_df = clean_spikes(plot_df, "P_fric_Lift", key_clean="P_fric_Lift", window=20)
    plot_df = clean_spikes(plot_df, "P_fric_Tilt", key_clean="P_fric_Tilt", window=20)

    plot_df["P_fric_sum"] = plot_df["P_fric_Lift"] + plot_df["P_fric_Tilt"]
    plot_df["P_DV_sum"] = plot_df["P_DV_Lift"] + plot_df["P_DV_Tilt"]
    plot_df["P_hose_sum"] = plot_df["P_hose_Lift_A"] + plot_df["P_hose_Lift_B"] + plot_df["P_hose_Tilt_A"] + plot_df["P_hose_Tilt_B"] + plot_df["P_hose_Pump"]

    plot_df["P_sum_total"] = plot_df["P_hose_sum"] + plot_df["P_mech_Lift"] + plot_df["P_mech_Tilt"] + plot_df["P_fric_sum"] + plot_df["P_DV_sum"]
    plot_df["P_gap"] = plot_df["P_pump"] - plot_df["P_sum_total"]

    plot_df.to_csv(CSV_DIR / f"{FILENAME}_{case_id[0]}_{case_id[1]}_{case_id[2]}.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    fs = 18
    fig_size = (8.6, 6.2)

    fig = plt.figure(figsize=fig_size)
    ax = fig.add_subplot(111)

    ax.plot(plot_df["Time"], plot_df["P_hose_sum"], label="Hose expansion power", linewidth=1.8)
    ax.plot(plot_df["Time"], plot_df["P_mech_Lift"], label="Lift cylinder mechanical power", linewidth=1.8)
    ax.plot(plot_df["Time"], plot_df["P_mech_Tilt"], label="Tilt cylinder mechanical power", linewidth=1.8)
    ax.plot(plot_df["Time"], plot_df["P_fric_sum"], label="Cylinder friction losses", linewidth=1.8)
    ax.plot(plot_df["Time"], plot_df["P_damp_sum"], label="Joint damping losses", linewidth=1.8)
    ax.plot(plot_df["Time"], plot_df["P_DV_sum"], label="Valve throttling losses", linewidth=1.8)
    ax.plot(plot_df["Time"], plot_df["P_sum_total"], label="Total accounted power", linewidth=2.5, color="black")
    ax.plot(plot_df["Time"], plot_df["P_pump"], label="Pump input power", linewidth=2.5, color="red")
    ax.plot(plot_df["Time"], plot_df["P_gap"], label="Unaccounted power", linewidth=2.0, color="gray", linestyle=":")

    motion_times = [0, 2.5, 8.5, 15, 21, plot_df["Time"].max()]
    motion_labels = ["Motion 0", "Motion I", "Motion II", "Motion III", "Motion IV"]

    for t in motion_times[1:-1]:
        ax.axvline(t, color="black", linestyle="--", linewidth=1.2)

    for i in range(len(motion_labels)):
        if i % 2 == 0:
            ax.axvspan(motion_times[i], motion_times[i+1], color="black", alpha=0.05)

        x_mid = (motion_times[i] + motion_times[i+1])/2
        ax.text(x_mid, -0.1, motion_labels[i], ha="center", va="top", fontsize=fs, transform=ax.get_xaxis_transform(), clip_on=False)

    ax.set_xlim(0, plot_df["Time"].max())
    ax.axhline(0, color="black", linewidth=1.8, zorder=5)

    plt.xlabel(X_LABEL, fontsize=fs)
    plt.ylabel(Y_LABEL, fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.title(f"Payload: {case_id[1]} kg", fontsize=fs)
    plt.grid(True)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.17)
    plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}_{case_id[0]}_{case_id[1]}_{case_id[2]}.pdf", format="pdf", bbox_inches="tight")
    plt.show()

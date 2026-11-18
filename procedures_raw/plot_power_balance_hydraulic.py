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

from utils.paths import CSV_DIR, DATA_DIR, FIGURES_DIR, POWERBALANCE_DIR

if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL = r"$P$, kW"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    case_set = [(0, 400, 300),(0,10,300), (30,400,300), (30,10,300)]
    datasets.update(load_specific_results(POWERBALANCE_DIR, case_set))
    for case_id in case_set:
        ds = datasets[case_id]
        FILENAME = f"Power_balance"
        """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

        plot_df = pd.DataFrame()
        plot_df["Time"] = ds.Time

        p_tank = 1.0
        c_joint = 2000.0

        plot_df["P_pump"] = (ds.VolPump_p-p_tank)*ds.Pump_Q/600

        plot_df["P_hyd_Lift"] = -((ds.Lift_A_p-p_tank)*ds.Lift_A_Q + (ds.Lift_B_p-p_tank)*ds.Lift_B_Q)/600
        plot_df["P_hyd_Tilt"] = -((ds.Tilt_A_p-p_tank)*ds.Tilt_A_Q + (ds.Tilt_B_p-p_tank)*ds.Tilt_B_Q)/600

        plot_df["P_mech_Lift"] = -ds.Lift_F*ds.Lift_ds/1e6
        plot_df["P_mech_Tilt"] = -ds.Tilt_F*ds.Tilt_ds/1e6

        plot_df["P_fric_Lift"] = plot_df["P_hyd_Lift"] - plot_df["P_mech_Lift"]
        plot_df["P_fric_Tilt"] = plot_df["P_hyd_Tilt"] - plot_df["P_mech_Tilt"]
        plot_df["P_fric_sum"] = plot_df["P_fric_Lift"] + plot_df["P_fric_Tilt"]

        omega_PillarLift = np.deg2rad(ds.PillarLift_dtheta)
        omega_LiftTilt = np.deg2rad(ds.LiftTilt_dtheta)
        omega_LiftBracket1 = np.deg2rad(ds.LiftBracket1_dtheta)
        omega_Bracket1Bracket2 = np.deg2rad(ds.Bracket1Bracket2_dtheta)
        omega_Bracket2Tilt = np.deg2rad(ds.Bracket2Tilt_dtheta)

        plot_df["P_damp_sum"] = c_joint*(omega_PillarLift**2 + omega_LiftTilt**2 + omega_LiftBracket1**2 + omega_Bracket1Bracket2**2 + omega_Bracket2Tilt**2)/1000

        plot_df["P_DV_Lift"] = -((ds.VolPump_p-p_tank)*ds.Lift_DV_QP + (ds.Lift_A_p-p_tank)*ds.Lift_DV_QA + (ds.Lift_B_p-p_tank)*ds.Lift_DV_QB)/600
        plot_df["P_DV_Tilt"] = -((ds.VolPump_p-p_tank)*ds.Tilt_DV_QP + (ds.Tilt_A_p-p_tank)*ds.Tilt_DV_QA + (ds.Tilt_B_p-p_tank)*ds.Tilt_DV_QB)/600
        plot_df["P_DV_sum"] = plot_df["P_DV_Lift"] + plot_df["P_DV_Tilt"]

        plot_df["Q_leak_Lift"] = -(ds.Lift_DV_QP + ds.Lift_DV_QA + ds.Lift_DV_QB + ds.Lift_DV_QT)
        plot_df["Q_leak_Tilt"] = -(ds.Tilt_DV_QP + ds.Tilt_DV_QA + ds.Tilt_DV_QB + ds.Tilt_DV_QT)

        plot_df["P_leak_Lift"] = (ds.VolPump_p-p_tank)*np.abs(plot_df["Q_leak_Lift"])/600
        plot_df["P_leak_Tilt"] = (ds.VolPump_p-p_tank)*np.abs(plot_df["Q_leak_Tilt"])/600
        plot_df["P_leak_sum"] = plot_df["P_leak_Lift"] + plot_df["P_leak_Tilt"]

        plot_df["Q_storage_Pump"] = ds.Pump_Q + ds.Lift_DV_QP + ds.Tilt_DV_QP
        plot_df["Q_storage_Lift_A"] = ds.Lift_DV_QA + ds.Lift_A_Q
        plot_df["Q_storage_Lift_B"] = ds.Lift_DV_QB + ds.Lift_B_Q
        plot_df["Q_storage_Tilt_A"] = ds.Tilt_DV_QA + ds.Tilt_A_Q
        plot_df["Q_storage_Tilt_B"] = ds.Tilt_DV_QB + ds.Tilt_B_Q

        plot_df["P_storage_Pump"] = (ds.VolPump_p-p_tank)*plot_df["Q_storage_Pump"]/600
        plot_df["P_storage_Lift_A"] = (ds.Lift_A_p-p_tank)*plot_df["Q_storage_Lift_A"]/600
        plot_df["P_storage_Lift_B"] = (ds.Lift_B_p-p_tank)*plot_df["Q_storage_Lift_B"]/600
        plot_df["P_storage_Tilt_A"] = (ds.Tilt_A_p-p_tank)*plot_df["Q_storage_Tilt_A"]/600
        plot_df["P_storage_Tilt_B"] = (ds.Tilt_B_p-p_tank)*plot_df["Q_storage_Tilt_B"]/600

        clean_keys = ["P_pump", "P_hyd_Lift", "P_hyd_Tilt", "P_mech_Lift", "P_mech_Tilt", "P_fric_Lift", "P_fric_Tilt",
                      "P_fric_sum", "P_damp_sum", "P_DV_Lift", "P_DV_Tilt", "P_DV_sum", "Q_leak_Lift", "Q_leak_Tilt",
                      "P_leak_Lift", "P_leak_Tilt", "P_leak_sum", "P_storage_Pump", "P_storage_Lift_A",
                      "P_storage_Lift_B", "P_storage_Tilt_A", "P_storage_Tilt_B"]

        for key in clean_keys:
            plot_df = clean_spikes(plot_df, key, key_clean=key, window=20)
            plot_df = smooth_series(plot_df, key, key_smooth=key, window=100)

        plot_df["P_storage_sum"] = plot_df["P_storage_Pump"] + plot_df["P_storage_Lift_A"] + plot_df["P_storage_Lift_B"] + plot_df["P_storage_Tilt_A"] + plot_df["P_storage_Tilt_B"]

        plot_df["P_sum_total"] = plot_df["P_hyd_Lift"] + plot_df["P_hyd_Tilt"] + plot_df["P_DV_sum"] + plot_df["P_storage_sum"]
        plot_df["P_gap"] = plot_df["P_pump"] - plot_df["P_sum_total"]

        q_leak_lift_mean = np.mean(np.abs(plot_df["Q_leak_Lift"]))
        q_leak_tilt_mean = np.mean(np.abs(plot_df["Q_leak_Tilt"]))
        q_leak_lift_max = np.max(np.abs(plot_df["Q_leak_Lift"]))
        q_leak_tilt_max = np.max(np.abs(plot_df["Q_leak_Tilt"]))
        p_gap_rms = np.sqrt(np.mean(plot_df["P_gap"]**2))
        p_gap_max = np.max(np.abs(plot_df["P_gap"]))

        print(f"Lift reconstructed leakage mean: {q_leak_lift_mean:.6f} L/min")
        print(f"Lift reconstructed leakage max: {q_leak_lift_max:.6f} L/min")
        print(f"Tilt reconstructed leakage mean: {q_leak_tilt_mean:.6f} L/min")
        print(f"Tilt reconstructed leakage max: {q_leak_tilt_max:.6f} L/min")
        print(f"Power-balance RMS: {p_gap_rms:.6e} kW")
        print(f"Power-balance max: {p_gap_max:.6e} kW")

        plot_df.to_csv(CSV_DIR / f"{FILENAME}_{case_id[0]}_{case_id[1]}_{case_id[2]}.csv", index=False)

        """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

        fs = 20
        fig_size = (6.48, 4.40)

        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111)
        ax.plot(plot_df["Time"], plot_df["P_hyd_Lift"], label="Lift cylinder power", linewidth=2, color=(0.,0.6,0.2),linestyle=(0, (6, 1, 1, 1)))
        ax.plot(plot_df["Time"], plot_df["P_hyd_Tilt"], label="Tilt cylinder power", linewidth=2, color=(0.,0.2,0.6),linestyle=(0, (6, 1, 1, 1)))
        ax.plot(plot_df["Time"], plot_df["P_storage_sum"], label="Hydraulic storage power", linewidth=2,linestyle=(0, (3, 1, 1, 1)), color="orange")
        ax.plot(plot_df["Time"], plot_df["P_DV_sum"], label="Valve hydraulic losses", linewidth=2, color="purple", linestyle=(0, (8, 2)))
        #ax.plot(plot_df["Time"], plot_df["P_leak_sum"], label="External leakage power estimate", linewidth=1.5, color="purple")
        #ax.plot(plot_df["Time"], plot_df["P_fric_sum"], label="Cylinder friction losses", linewidth=1.5)
        #ax.plot(plot_df["Time"], plot_df["P_damp_sum"], label="Joint damping losses", linewidth=1.5)
        ax.plot(plot_df["Time"], plot_df["P_pump"], label="Pump hydraulic power", linewidth=3, color="black")
        ax.plot(plot_df["Time"], plot_df["P_sum_total"], label="Total hydraulic power", linewidth=2, color="red", linestyle="--")

        #ax.plot(plot_df["Time"], plot_df["P_gap"], label="Unaccounted power", linewidth=3.0, color="gray", linestyle=":")

        motion_times = [0, 2.5, 8.5, 15, 21, plot_df["Time"].max()]
        motion_labels = ["0", "I", "II", "III", "IV"]

        for t in motion_times[1:-1]:
            ax.axvline(t, color="black", linestyle="--", linewidth=1.2)

        for i in range(len(motion_labels)):
            if i % 2 == 0:
                ax.axvspan(motion_times[i], motion_times[i+1], color="black", alpha=0.05)

            x_mid = (motion_times[i] + motion_times[i+1])/2
            ax.text(x_mid, 0.07, motion_labels[i], ha="center", va="top", fontsize=fs, transform=ax.get_xaxis_transform(), clip_on=False)



        ax.set_xlim(0, plot_df["Time"].max())

        lines = ax.get_lines()
        y_min = min(np.nanmin(line.get_ydata()) for line in lines)
        y_max = max(np.nanmax(line.get_ydata()) for line in lines)
        ax.set_ylim(y_min-1, y_max+0.5)
        ax.axhline(0, color="black", linewidth=1., zorder=5)

        plt.xlabel(X_LABEL, fontsize=fs)
        plt.ylabel(Y_LABEL, fontsize=fs)
        plt.xticks(fontsize=fs)
        plt.yticks(fontsize=fs)
        #plt.title(f"Payload: {case_id[1]} kg", fontsize=fs)
        plt.grid(True)

        handles, labels = ax.get_legend_handles_labels()
        ax.yaxis.set_label_coords(-0.04, 0.5)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.17)
        plt.tight_layout()
        plt.savefig(
            FIGURES_DIR / f"OUTPUT_{FILENAME}_{case_id[0]}_{case_id[1]}_{case_id[2]}.pdf",
            format="pdf",
            bbox_inches="tight"
        )

    fig_legend = plt.figure(figsize=(6.48*2, 1.6))
    fig_legend.legend(
        handles,
        labels,
        loc="center",
        ncol=3,
        fontsize=20,
        frameon=False
    )

    fig_legend.savefig(
        FIGURES_DIR / f"OUTPUT_{FILENAME}_legend.pdf",
        format="pdf",
        bbox_inches="tight"
    )

    plt.show()

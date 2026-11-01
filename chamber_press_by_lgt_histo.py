from pathlib import Path
import numpy as np
from data_import import import_results
from result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results
from plotting import plot_variables, plot_series, plot_smthng
from processing import *
import matplotlib.pyplot as plt
import pandas as pd
from plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots
from matplotlib.patches import Patch
from matplotlib.colors import to_rgb

PROJECT_ROOT = Path(__file__).resolve().parent
RAWDATA_DIR = (PROJECT_ROOT / "rawdata")

if __name__ == "__main__":

    X_LABEL = "Motion"
    Y_LABEL = r"$\bar{p}_{\mathrm{ch}}$, bar"
    FILENAME = "Chamber_pressure_by_motion"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0, 10, 20, 30]
    p_set = [10, 400]
    r_set = [30]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    chamber_set = ["Lift_A_p", "Lift_B_p", "Tilt_A_p", "Tilt_B_p"]
    chamber_labels = {"Lift_A_p": "Lift vol.A", "Lift_B_p": "Lift vol.B", "Tilt_A_p": "Tilt vol.A", "Tilt_B_p": "Tilt vol.B"}
    motion_set = [("I", 2.5, 8.5), ("II", 8.5, 15.0), ("III", 15.0, 21.0), ("IV", 21.0, None)]

    plot_df = pd.DataFrame()
    res_tup_list = list()

    pilot_share_df = pd.DataFrame()
    pilot_share_list = list()

    PILOT_TOL = 5.0

    for case_id in case_set:
        ds = datasets[case_id]

        lsp = ds["LSp"].to_numpy()
        chamber_stack = np.vstack([ds[chamber].to_numpy() for chamber in chamber_set])
        diff_stack = np.abs(chamber_stack - lsp)

        pilot_idx = np.argmin(diff_stack, axis=0)
        pilot_error = np.min(diff_stack, axis=0)

        pilot_chambers = np.full(len(ds), None, dtype=object)
        valid_pilot = pilot_error <= PILOT_TOL
        pilot_chambers[valid_pilot] = np.array(chamber_set)[pilot_idx[valid_pilot]]

        share_row = [case_id[0], case_id[1], case_id[2]]
        for chamber in chamber_set:
            share_row.append(np.mean(pilot_chambers == chamber) * 100.0)
        pilot_share_list.append(tuple(share_row))

        for motion, t_start, t_end in motion_set:
            if t_end is None:
                mask = ds["Time"] >= t_start
            else:
                mask = (ds["Time"] >= t_start) & (ds["Time"] < t_end)

            motion_pilots = pilot_chambers[mask.to_numpy()]
            pilot_counts = {chamber: np.sum(motion_pilots == chamber) for chamber in chamber_set}

            if max(pilot_counts.values()) > 0:
                dominant_pilot = max(pilot_counts, key=pilot_counts.get)
            else:
                dominant_pilot = None

            lift_a_p = ds.loc[mask, "Lift_A_p"].mean()
            lift_b_p = ds.loc[mask, "Lift_B_p"].mean()
            tilt_a_p = ds.loc[mask, "Tilt_A_p"].mean()
            tilt_b_p = ds.loc[mask, "Tilt_B_p"].mean()

            res_tup_list.append((case_id, motion, lift_a_p, lift_b_p, tilt_a_p, tilt_b_p, dominant_pilot))

    plot_df["lgt"] = [sol[0][0] for sol in res_tup_list]
    plot_df["pld"] = [sol[0][1] for sol in res_tup_list]
    plot_df["rfp"] = [sol[0][2] for sol in res_tup_list]
    plot_df["motion"] = [sol[1] for sol in res_tup_list]
    plot_df["Lift_A_p"] = [sol[2] for sol in res_tup_list]
    plot_df["Lift_B_p"] = [sol[3] for sol in res_tup_list]
    plot_df["Tilt_A_p"] = [sol[4] for sol in res_tup_list]
    plot_df["Tilt_B_p"] = [sol[5] for sol in res_tup_list]
    plot_df["pilot_chamber"] = [sol[6] for sol in res_tup_list]
    plot_df.to_csv(f"{FILENAME}.csv", index=False)

    pilot_share_df["lgt"] = [sol[0] for sol in pilot_share_list]
    pilot_share_df["pld"] = [sol[1] for sol in pilot_share_list]
    pilot_share_df["rfp"] = [sol[2] for sol in pilot_share_list]
    pilot_share_df["case"] = [f"{sol[0]}% {sol[1]}kg" for sol in pilot_share_list]
    pilot_share_df["Lift vol.A"] = [sol[3] for sol in pilot_share_list]
    pilot_share_df["Lift vol.B"] = [sol[4] for sol in pilot_share_list]
    pilot_share_df["Tilt vol.A"] = [sol[5] for sol in pilot_share_list]
    pilot_share_df["Tilt vol.B"] = [sol[6] for sol in pilot_share_list]
    pilot_share_df = pilot_share_df.sort_values(["pld", "lgt"]).reset_index(drop=True)
    pilot_share_df[["case", "Lift vol.A", "Lift vol.B", "Tilt vol.A", "Tilt vol.B"]].to_csv(f"{FILENAME}_pilot_share.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    base_colors = {"Lift_A_p": "#005a32", "Lift_B_p": "#a1d99b", "Tilt_A_p": "#084594", "Tilt_B_p": "#6baed6"}
    saturation = {0: 1.00, 10: 0.82, 20: 0.64, 30: 0.46}
    color_map = dict()
    fs = 20
    fig_size = (6.48, 4.40)
    for chamber in chamber_set:
        rgb = np.array(to_rgb(base_colors[chamber]))
        for lgt in l_set:
            s = saturation[lgt]
            color_map[(chamber, lgt)] = tuple(1.0 - s * (1.0 - rgb))

    legend_handles = [Patch(facecolor=color_map[(chamber, lgt)], edgecolor="black", label=f"{chamber_labels[chamber]}, {lgt}%") for chamber in chamber_set for lgt in l_set]

    motions = ["I", "II", "III", "IV"]
    x = np.arange(len(motions))
    width = 0.055

    for pld in p_set:
        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111)

        bar_records = list()
        i = 0

        for chamber in chamber_set:
            for lgt in l_set:
                vals = list()
                pilot_flags = list()

                for motion in motions:
                    row = plot_df[(plot_df["pld"] == pld) & (plot_df["lgt"] == lgt) & (plot_df["motion"] == motion)].iloc[0]
                    vals.append(row[chamber])
                    pilot_flags.append(row["pilot_chamber"] == chamber)

                offset = (i - 7.5) * width
                xpos = x + offset
                plt.bar(xpos, vals, width=width, color=color_map[(chamber, lgt)], edgecolor="black", linewidth=0.6, zorder=3)

                for j in range(len(motions)):
                    bar_records.append((xpos[j], vals[j], pilot_flags[j]))

                i += 1

        y_max = max([rec[1] for rec in bar_records])
        y_star = 0.002 * y_max

        for xpos, val, is_pilot in bar_records:
            if is_pilot:
                ax.text(xpos, val + y_star, "*", ha="center", va="bottom", fontsize=10)

        plt.xlabel(X_LABEL, fontsize=fs)
        plt.ylabel(Y_LABEL, fontsize=fs)
        plt.xticks(x, motions, fontsize=fs)
        plt.yticks(fontsize=fs)
        #plt.title(f"Payload {pld} kg", fontsize=fs)
        ax.grid(True, axis="y", zorder=0)
        plt.grid(True, axis="y")
        plt.tight_layout()
        plt.savefig(f"figures/OUTPUT_{FILENAME}_{pld}kg.pdf", format="pdf", bbox_inches="tight")
        plt.show()

    fig_legend = plt.figure(figsize=(12.96, 2.2))
    fig_legend.legend(handles=legend_handles, loc="center", ncol=4, fontsize=fs, frameon=False, columnspacing=2.0, handletextpad=0.5, handlelength=2.0)
    fig_legend.savefig(f"figures/LEGEND_{FILENAME}.pdf", bbox_inches="tight", pad_inches=0.05)
    plt.show()

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING PILOT SHARE ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_share_df = pilot_share_df[["case", "pld", "Lift vol.A", "Lift vol.B", "Tilt vol.A", "Tilt vol.B"]].copy()
    plot_share_df["Valves closed"] = 100.0 - plot_share_df[["Lift vol.A", "Lift vol.B", "Tilt vol.A", "Tilt vol.B"]].sum(axis=1)
    plot_share_df["Valves closed"] = plot_share_df["Valves closed"].clip(lower=0)

    base_colors = {"Lift vol.A": "#005a32", "Lift vol.B": "#a1d99b", "Tilt vol.A": "#084594", "Tilt vol.B": "#6baed6", "Valves closed": "#bdbdbd"}
    legend_handles = [Patch(facecolor=base_colors[column], edgecolor="black", label=column) for column in ["Lift vol.A", "Lift vol.B", "Tilt vol.A", "Tilt vol.B", "Valves closed"]]

    fig = plt.figure(figsize=(11, 6))
    ax = fig.add_subplot(111)

    y = np.arange(len(plot_share_df))
    left = np.zeros(len(plot_share_df))

    for column in ["Lift vol.A", "Lift vol.B", "Tilt vol.A", "Tilt vol.B", "Valves closed"]:
        vals = plot_share_df[column].to_numpy()
        bars = ax.barh(y, vals, left=left, height=0.75, color=base_colors[column], edgecolor="black", linewidth=0.6, zorder=3)

        for i, val in enumerate(vals):
            if val <= 0.05:
                continue

            y_i = y[i]
            x_left = left[i]
            x_right = left[i] + val
            x_center = left[i] + val / 2
            pld = plot_share_df.iloc[i]["pld"]
            txt = f"{val:.1f}%"

            if column in ["Lift vol.B"] and pld ==10:
                ax.text(x_center+4, y_i, txt, ha="center", va="center", fontsize=fs, color="black", zorder=4)
            elif column in ["Lift vol.B", "Tilt vol.B"]:
                ax.text(x_center, y_i, txt, ha="center", va="center", fontsize=fs, color="black", zorder=4)

            elif column == "Lift vol.A":
                if pld == 400:
                    ax.text(x_center+1, y_i, txt, ha="center", va="center", fontsize=fs, color="white", zorder=4)
                else:
                    ax.annotate(txt, xy=(x_right, y_i), xytext=(x_right + 3.0, y_i), ha="left", va="center", fontsize=fs, color="black", arrowprops=dict(arrowstyle="->", lw=1.1, color="black", shrinkA=0, shrinkB=0), zorder=4)

            elif column == "Tilt vol.A":
                ax.annotate(txt, xy=(x_right, y_i), xytext=(x_right + 3.0, y_i), ha="left", va="center", fontsize=fs, color="black", arrowprops=dict(arrowstyle="->", lw=1.1, color="black", shrinkA=0, shrinkB=0), zorder=4)

            elif column == "Valves closed":
                ax.annotate(txt, xy=(x_left, y_i), xytext=(x_left - 3.0, y_i), ha="right", va="center", fontsize=fs, color="black", arrowprops=dict(arrowstyle="->", lw=1.1, color="black", shrinkA=0, shrinkB=0), zorder=4)

        left += vals

    ax.set_xlabel("Pilot share, %", fontsize=20)
    ax.set_ylabel("Case", fontsize=20)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_share_df["case"], fontsize=fs)
    ax.set_xticks(np.arange(0, 101, 10))
    ax.tick_params(axis="x", labelsize=fs)
    ax.set_axisbelow(True)
    ax.grid(True, axis="x")
    ax.set_xlim(0, 100)
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(f"figures/OUTPUT_{FILENAME}_pilot_share.pdf", format="pdf", bbox_inches="tight")
    plt.show()

    fig_legend = plt.figure(figsize=(12, 1.2))
    fig_legend.legend(handles=legend_handles, loc="center", ncol=5, fontsize=fs, frameon=False, columnspacing=2.2, handletextpad=0.6, handlelength=2.0)
    fig_legend.savefig(f"figures/LEGEND_{FILENAME}_pilot_share.pdf", bbox_inches="tight", pad_inches=0.05)
    plt.show()
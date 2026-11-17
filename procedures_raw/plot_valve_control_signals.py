from pathlib import Path
import numpy as np
from utils.data_import import import_results
from utils.result_parser import load_all_results, load_ref_thetas, load_masked_results, load_specific_results, load_ref_u
from utils.plotting import plot_variables, plot_series, plot_smthng
from utils.processing import *
import matplotlib.pyplot as plt
# import pandas as pd
from utils.plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots
import ast

from utils.paths import DATA_DIR, FIGURES_DIR, PROJECT_ROOT
RAWDATA_DIR = DATA_DIR
#REF_U_DIR = PROJECT_ROOT / "target_u"
REF_U_DIR = PROJECT_ROOT / "exp_pressures/validatio.txt"

if __name__ == "__main__":

    X_LABEL = "Time, s"
    Y_LABEL = r"$U_k$, V"
    TITLE = "Valve control signals"
    FILENAME = "U_by_lgt"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [0,30]
    p_set = [10, 400]
    r_set = [30]
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    # lift_u_ds, tilt_u_ds = load_ref_u(REF_U_DIR)
    # u_ds = realign_u(lift_u_ds, tilt_u_ds)
    valid_df = pd.read_csv(REF_U_DIR,sep="\t")
    u_ds = valid_df[["Time", "Lift_U", "Tilt_U"]].copy()
    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    for case_id in case_set:
        datasets[case_id] = align_to_reference(u_ds, datasets[case_id])

        datasets[case_id] = smooth_series(datasets[case_id], "Lift_U", key_smooth="Lift_U_smooth", window=50)
        datasets[case_id] = smooth_series(datasets[case_id], "Tilt_U", key_smooth="Tilt_U_smooth", window=50)
        u_ds[f"Lift_U {case_id}"] = datasets[case_id].Lift_U_smooth
        u_ds[f"Tilt_U {case_id}"] = datasets[case_id].Tilt_U_smooth

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plt.figure(figsize=(6.48*2, 10))

    for column in sorted(u_ds.columns):
        if column != "Time":
            style = "--" if column in ["Lift_U", "Tilt_U"] else "-"
            color = dict()
            il = 0.
            it = 0.

            if column not in ["Lift_U", "Tilt_U"]:
                case_id = ast.literal_eval(column.split(" ", 1)[1])

                if case_id[0] == 0:
                    style = "-."

                if case_id[1] == 400:
                    il = 0.6
                    it = 0.6

            if "Lift_U" in column:
                color = (il, 0.6, 0.)
            elif "Tilt_U" in column:
                color = (it, 0., 0.8)

            if column not in ["Lift_U", "Tilt_U"]:
                al = " " if case_id[0] == 0 else ""
                curve_label = f"L = {case_id[0]}%;  \t" + al + r"$m_{pld}$" + f" = {case_id[1]} kg"
                lw = 1
            else:
                curve_label = f"{column.split('_', 1)[0]} reference data"
                lw = 3

            plt.plot(u_ds["Time"], u_ds[column], label=curve_label, linestyle=style, color=color, linewidth=lw)

    plt.xlabel(X_LABEL, fontsize=20)
    plt.ylabel(Y_LABEL, fontsize=20)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    #plt.title(TITLE, fontsize=20)

    plt.grid(True)
    plt.legend(fontsize=20, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.33)

    plt.savefig(FIGURES_DIR / f"OUTPUT_{FILENAME}.pdf", format="pdf", bbox_inches="tight")
    plt.show()

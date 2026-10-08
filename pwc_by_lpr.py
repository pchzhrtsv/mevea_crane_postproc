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

PROJECT_ROOT = Path(__file__).resolve().parent
RAWDATA_DIR = (PROJECT_ROOT / "rawdata")

if __name__ == "__main__":

    param = "lgt"

    Y_LABEL = r"Fraction of total energy consumption, %"
    #TITLE = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0


    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()
    l_set = [i for i in range(0, 31, 3)] if param == "lgt" else [0]
    p_set = [i for i in range(40, 401, 40)] if param == "pld" else [400]
    r_set = [i for i in range(50, 401, 50)] if param == "rfp" else [40]

    if param == "lgt":
        X_LABEL = "Lightening, %"
        meta = f"p{p_set[0]}_r{r_set[0]}"
    elif param == "pld":
        X_LABEL = "Payload, kg"
        meta = f"l{l_set[0]}_r{r_set[0]}"
    elif param == "rfp":
        X_LABEL = "Reference pressure, bar"
        RAWDATA_DIR = (PROJECT_ROOT / "refpress_data")
        meta = f"l{l_set[0]}_p{p_set[0]}"

    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))
    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]
    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.DataFrame()
    res_tup_list = list()
    for case in case_set:
        lift_w, tilt_w = cylinders_pump_work(datasets[case])
        pump_w = pump_work(datasets[case])
        print(f"lift {lift_w}, tilt {tilt_w}, pump {pump_w}")
        res_tup_list.append((case, lift_w, tilt_w, pump_w))
    sorted_res = sorted(res_tup_list)
    plot_df["lgt"] = [sol[0][0] for sol in sorted_res]
    plot_df["pld"] = [sol[0][1]for sol in sorted_res]
    plot_df["rfp"] = [sol[0][2] / 10 for sol in sorted_res]
    plot_df["lift_w"] = [sol[1] for sol in sorted_res]
    plot_df["tilt_w"] = [sol[2] for sol in sorted_res]
    plot_df["pump_w"] = [sol[3] for sol in sorted_res]
    plot_df["Lift cylinder"] = plot_df["lift_w"]/plot_df["pump_w"]*100
    plot_df["Tilt cylinder"] = plot_df["tilt_w"]/plot_df["pump_w"]*100
    plot_df["Valve losses"] = (plot_df["pump_w"]-plot_df["tilt_w"]-plot_df["lift_w"])/plot_df["pump_w"]*100
    plot_df.to_csv(f"pwc_by_{param}_{meta}.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plt.figure(figsize=(8, 6))

    x = plot_df[param].to_numpy()
    y1 = plot_df["Lift cylinder"].to_numpy()
    y2 = plot_df["Tilt cylinder"].to_numpy()
    y3 = plot_df["Valve losses"].to_numpy()

    if len(x) > 1:
        width = 0.8 * np.min(np.diff(np.sort(x)))
    else:
        width = 0.8

    plt.bar(x, y1, width=width, color="blue", label="Lift cylinder")
    plt.bar(x, y2, width=width, bottom=y1, color="green", label="Tilt cylinder")
    plt.bar(x, y3, width=width, bottom=y1 + y2, color="red", label="Valve losses")

    plt.xlabel(X_LABEL, fontsize=18)
    plt.ylabel(Y_LABEL, fontsize=18)
    plt.ylim(0, 100)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    # plt.title(TITLE, fontsize=18)
    plt.grid(True, axis="y")
    for xi, v1, v2, v3 in zip(x, y1, y2, y3):
        if v1 > 2:
            plt.text(xi, v1/2, f"{v1:.1f}%", ha="center", va="center", fontsize=14, color="white")

        if v2 > 2:
            plt.text(xi, v1+v2/2, f"{v2:.1f}%", ha="center", va="center", fontsize=14, color="white")

        if v3 > 2:
            plt.text(xi, v1+v2+v3/2, f"{v3:.1f}%", ha="center", va="center", fontsize=14, color="white")

    plt.legend(fontsize=18, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, frameon=False)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.22)
    plt.savefig(f"figures/OUTPUT_pwc_by_{param}_{meta}.pdf", format="pdf", bbox_inches="tight")
    plt.show()
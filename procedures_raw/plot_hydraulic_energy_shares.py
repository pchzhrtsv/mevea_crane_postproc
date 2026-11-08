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


if __name__ == "__main__":

    param = "rfp"

    Y_LABEL = r"$\eta$, %"
    #TITLE = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$"
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0
    color_lift = "#1E5AA8"
    color_tilt = "#1F7A4D"
    color_loss = "#D08A00"
    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""
    all_params = ["rfp", "lgt", "pld"]
    edge_pairs = {
        "rfp": [(a,b,0) for a in [0,30] for b in [10,400]],
        "lgt": [(0,a,b) for a in [10,400] for b in [10,40]],
        "pld": [(a,0,b) for a in [0,30] for b in [10,40]],
    }
    for param in all_params:
        for pair in edge_pairs[param]:
            datasets = dict()
            l_set = [i for i in range(0, 31, 3)] if param == "lgt" else [pair[0]]
            p_set = [i for i in range(40, 401, 40)] if param == "pld" else [pair[1]]
            r_set = [i for i in range(50, 401, 50)] if param == "rfp" else [pair[2]]

            if param == "lgt":
                X_LABEL = "Lightening, %"
                meta = f"p{p_set[0]}_r{r_set[0]}"
                RAWDATA_DIR = DATA_DIR
            elif param == "pld":
                X_LABEL = "Payload, kg"
                meta = f"l{l_set[0]}_r{r_set[0]}"
                RAWDATA_DIR = DATA_DIR
            elif param == "rfp":
                X_LABEL = r"$\Delta p_\mathrm{LS}$, bar"
                RAWDATA_DIR = DATA_DIR
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
            plot_df.to_csv(CSV_DIR / f"pwc_by_{param}_{meta}.csv", index=False)

            """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

            fig = plt.figure(figsize=(6.48, 5))
            fs = 20
            ax = fig.add_subplot(111)

            x = plot_df[param].to_numpy()
            y1 = plot_df["Lift cylinder"].to_numpy()
            y2 = plot_df["Tilt cylinder"].to_numpy()
            y3 = plot_df["Valve losses"].to_numpy()

            if len(x) > 1:
                width = 0.8 * np.min(np.diff(np.sort(x)))
            else:
                width = 0.8

            ax.bar(x, y1, width=width, color=color_lift, label="Lift cylinder", zorder=3)
            ax.bar(x, y2, width=width, bottom=y1, color=color_tilt, label="Tilt cylinder", zorder=3)
            ax.bar(x, y3, width=width, bottom=y1 + y2, color=color_loss, label="Valve losses", zorder=3)

            ax.set_xlabel(X_LABEL, fontsize=fs)
            ax.set_ylabel(Y_LABEL, fontsize=fs)
            ax.set_ylim(0, 100)
            tick_interval_dict = {"rfp":1, "pld":3, "lgt":2}

            ax.set_xticks(x[::tick_interval_dict[param]])
            ax.tick_params(axis="both", labelsize=fs)

            ax.set_axisbelow(True)
            ax.grid(True, axis="y", zorder=0)

            for xi, v1, v2, v3 in zip(x, y1, y2, y3):
                if v1 > 2:
                    ax.text(xi, v1 / 2, f"{v1:.1f}%", ha="center", va="center", fontsize=fs, color="white",rotation=90)

                if v2 > 2:
                    ax.text(xi, v1 + v2 / 2, f"{v2:.1f}%", ha="center", va="center", fontsize=fs, color="white",rotation=90)

                if v3 > 2:
                    ax.text(xi, v1 + v2 + v3 / 2, f"{v3:.1f}%", ha="center", va="center", fontsize=fs, color="white",rotation=90)

            handles, labels = ax.get_legend_handles_labels()

            plt.tight_layout()
            plt.savefig(FIGURES_DIR / f"OUTPUT_pwc_by_{param}_{meta}.pdf", format="pdf", bbox_inches="tight")

            fig_legend = plt.figure(figsize=(6.48*2, 0.7))
            fig_legend.legend(handles, labels, loc="center", ncol=3, fontsize=10, frameon=False)
            fig_legend.savefig(FIGURES_DIR / f"OUTPUT_pwc_legend.pdf", format="pdf", bbox_inches="tight")

    plt.show()

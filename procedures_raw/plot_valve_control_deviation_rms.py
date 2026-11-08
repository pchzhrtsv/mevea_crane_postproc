from pathlib import Path
import numpy as np
from utils.result_parser import load_specific_results, load_ref_u
from utils.processing import *
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.colors import to_rgb

from utils.paths import CSV_DIR, DATA_DIR, FIGURES_DIR, PROJECT_ROOT
RAWDATA_DIR = DATA_DIR
#REF_U_DIR = PROJECT_ROOT / "target_u"
REF_U_DIR = PROJECT_ROOT / "exp_pressures/validatio.txt"

if __name__ == "__main__":

    X_LABEL = "Deviation metric"
    Y_LABEL = r"$\delta u_{\mathrm{PID}}$, V"
    FILENAME = "U_dev_by_lgt"

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    datasets = dict()

    l_set = [0, 10, 20, 30]
    p_set = [10, 400]
    r_set = [30]

    case_set = [(l, p, r) for l in l_set for p in p_set for r in r_set]

    datasets.update(load_specific_results(RAWDATA_DIR, case_set))

    #lift_u_ds, tilt_u_ds = load_ref_u(REF_U_DIR)
    valid_df = pd.read_csv(REF_U_DIR,sep="\t")
    # lift_u_ds = valid_df
    # tilt_u_ds = valid_df
    #
    # u_ds = realign_u(lift_u_ds, tilt_u_ds)
    u_ds = valid_df
    """||||||||||||||||||||||||||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||||||||||||||||||||||||||"""

    for case_id in case_set:
        datasets[case_id] = align_to_reference(u_ds, datasets[case_id])

        datasets[case_id] = smooth_series(
            datasets[case_id],
            "Lift_U",
            key_smooth="Lift_U_smooth",
            window=2
        )

        datasets[case_id] = smooth_series(
            datasets[case_id],
            "Tilt_U",
            key_smooth="Tilt_U_smooth",
            window=2
        )

    plot_df = pd.DataFrame()
    res_tup_list = list()

    for case_id in case_set:

        lift_dev = np.abs(
            datasets[case_id]["Lift_U_smooth"].to_numpy()
            - u_ds["Lift_U"].to_numpy()
        )

        tilt_dev = np.abs(
            datasets[case_id]["Tilt_U_smooth"].to_numpy()
            - u_ds["Tilt_U"].to_numpy()
        )

        lift_max = np.max(lift_dev)
        lift_mean = np.mean(lift_dev)
        lift_rms = np.sqrt(np.mean(lift_dev ** 2))

        tilt_max = np.max(tilt_dev)
        tilt_mean = np.mean(tilt_dev)
        tilt_rms = np.sqrt(np.mean(tilt_dev ** 2))

        res_tup_list.append(
            (
                case_id,
                lift_max,
                lift_mean,
                lift_rms,
                tilt_max,
                tilt_mean,
                tilt_rms
            )
        )

    sorted_res = sorted(res_tup_list)

    plot_df["lgt"] = [sol[0][0] for sol in sorted_res]
    plot_df["pld"] = [sol[0][1] for sol in sorted_res]
    plot_df["rfp"] = [sol[0][2] / 10 for sol in sorted_res]

    plot_df["Lift max deviation"] = [sol[1] for sol in sorted_res]
    plot_df["Lift mean deviation"] = [sol[2] for sol in sorted_res]
    plot_df["Lift RMS deviation"] = [sol[3] for sol in sorted_res]

    plot_df["Tilt max deviation"] = [sol[4] for sol in sorted_res]
    plot_df["Tilt mean deviation"] = [sol[5] for sol in sorted_res]
    plot_df["Tilt RMS deviation"] = [sol[6] for sol in sorted_res]

    plot_df.to_csv(CSV_DIR / f"{FILENAME}.csv", index=False)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    base_colors = {
        10: "#ff8c00",
        400: "#d62728"
    }

    saturation = {
        0: 1.0,
        10: 0.80,
        20: 0.60,
        30: 0.40
    }

    color_map = dict()

    for pld in p_set:
        rgb = np.array(to_rgb(base_colors[pld]))

        for lgt in l_set:
            s = saturation[lgt]
            color_map[(pld, lgt)] = tuple(
                1.0 - s * (1.0 - rgb)
            )

    legend_handles = [
        Patch(
            facecolor=color_map[(pld, lgt)],
            edgecolor="black",
            label=r"$m_{pld}$"f" = {pld} kg, L = {lgt}%"
        )
        for pld in p_set
        for lgt in l_set
    ]

    metrics = [
        r"$\max$",
        r"$\mathrm{MAE}$",
        r"$\mathrm{RMS}$"
    ]

    x = np.arange(len(metrics))
    width = 0.095

    for valve in ["Lift", "Tilt"]:

        fig = plt.figure(figsize=(6.48, 5))
        ax = fig.add_subplot(111)

        i = 0

        for pld in p_set:
            for lgt in l_set:

                row = plot_df[
                    (plot_df["pld"] == pld)
                    & (plot_df["lgt"] == lgt)
                ].iloc[0]

                if valve == "Lift":
                    vals = [
                        row["Lift max deviation"],
                        row["Lift mean deviation"],
                        row["Lift RMS deviation"]
                    ]

                else:
                    vals = [
                        row["Tilt max deviation"],
                        row["Tilt mean deviation"],
                        row["Tilt RMS deviation"]
                    ]

                offset = (i - 3.5) * width

                ax.bar(
                    x + offset,
                    vals,
                    width=width,
                    color=color_map[(pld, lgt)],
                    edgecolor="black",
                    linewidth=0.8,
                    zorder=3
                )

                i += 1

        ax.set_ylabel(Y_LABEL, fontsize=20)

        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=20)

        ax.tick_params(axis="y", labelsize=20)

        ax.set_axisbelow(True)
        ax.grid(True, axis="y", zorder=0)

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.23)

        plt.savefig(
            FIGURES_DIR / f"OUTPUT_{FILENAME}_{valve.lower()}.pdf",
            format="pdf",
            bbox_inches="tight"
        )

        fig_legend = plt.figure(figsize=(6.48 * 2, 1.5))

        fig_legend.legend(
            handles=legend_handles,
            loc="center",
            ncol=4,
            fontsize=10,
            frameon=False,
            columnspacing=2.9,
            handletextpad=0.5,
            handlelength=2.2
        )

        fig_legend.savefig(
            FIGURES_DIR / f"LEGEND_{FILENAME}_{valve.lower()}.pdf",
            bbox_inches="tight",
            pad_inches=0.05
        )

        plt.show()

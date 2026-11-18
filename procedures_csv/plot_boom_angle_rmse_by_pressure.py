from pathlib import Path
import ast
import pandas as pd
import matplotlib.pyplot as plt

from utils.paths import CSV_DIR, FIGURES_DIR


if __name__ == "__main__":

    X_LABEL = r"$\Delta p_{\mathrm{LS}}$, bar"
    Y_LABEL = r"$e_{\mathrm{RMS,2D}}$, rad"
    FILENAME = "rmse_by_rfp"

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.read_csv(CSV_DIR / f"{FILENAME}.csv")

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    fig, ax = plt.subplots(figsize=(12.96, 8))

    curve_map = {
        (0, 10): ("--", "tab:blue", "o", "none"),
        (30, 10): ("-", "tab:blue", "o", "full"),
        (0, 400): ("--", "tab:orange", "D", "none"),
        (30, 400): ("-", "tab:orange", "D", "full"),
    }

    for column in plot_df.columns:
        if column != "p_ref":
            case = ast.literal_eval(column)
            al = " " if case[0] == 0 else ""
            curve_label = f"L = {case[0]}%; \t" + al + r"$m_{pld}$ = "f"{case[1]} kg"

            ax.plot(
                plot_df["p_ref"],
                plot_df[column],
                label=curve_label,
                color=curve_map[case][1],
                linestyle=curve_map[case][0],
                marker=curve_map[case][2],
                linewidth=1,
                markersize=6,
                fillstyle=curve_map[case][3]
            )

    ax.set_xlabel(X_LABEL, fontsize=20)
    ax.set_ylabel(Y_LABEL, fontsize=20)

    ax.tick_params(axis="both", labelsize=20)

    ax.axhline(y=0, linewidth=1, color="black")

    ax.grid(True)
    ax.set_axisbelow(True)

    ax.legend(
        fontsize=20,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=2,
        frameon=False
    )

    plt.subplots_adjust(bottom=0.22)

    plt.savefig(
        FIGURES_DIR / f"OUTPUT_{FILENAME}.pdf",
        format="pdf",
        bbox_inches="tight"
    )

    plt.show()

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

from utils.paths import CSV_DIR, FIGURES_DIR

if __name__ == "__main__":

    X_LABEL = r"$\Delta p_{\mathrm{LS}}$, bar"
    Y_LABEL = r"$\delta W_{pump}$, %"

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    """|||||||||||||||||||||||||||||||||||||||||||||||||| READING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    plot_df = pd.read_csv(CSV_DIR / "delta_w_by_rfp.csv")

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    fig, ax = plt.subplots(figsize=(12.96, 8))
    curve_map = {
        "10": ("--", "tab:blue", 'o', "full"),
        "400": ("--", "tab:orange", 'D', "full"),
    }
    for column in plot_df.columns:
        if column != "p_ref":
            curve_label = r"$m_{pld}$"f" = {column} kg"
            ax.plot(plot_df["p_ref"], plot_df[column],
                    label=curve_label, linewidth=1,color=curve_map[column][1], linestyle=curve_map[column][0], marker=curve_map[column][2],fillstyle=curve_map[column][3], markersize=6)

    ax.set_xlabel(X_LABEL, fontsize=20)
    ax.set_ylabel(Y_LABEL, fontsize=20)

    ax.axhline(y=0, linewidth=1, color="black")

    ax.tick_params(axis="both", labelsize=20)
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
        FIGURES_DIR / "OUTPUT_delta_w_by_rfp.pdf",
        format="pdf",
        bbox_inches="tight"
    )
    plt.show()

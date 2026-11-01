from pathlib import Path
import ast
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent
CSV_DIR = PROJECT_ROOT / "csv_files"

if __name__ == "__main__":

    X_LABEL = r"$\Delta p_{\mathrm{LS}}$, bar"
    Y_LABEL = "RMSE, rad"
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
        (0, 400): ("--", "tab:orange", "o", "none"),
        (30, 400): ("-", "tab:orange", "o", "full"),
    }

    for column in plot_df.columns:
        if column != "p_ref":
            case = ast.literal_eval(column)

            curve_label = f"Lightweighting {case[0]}%; payload: {case[1]} kg"

            ax.plot(
                plot_df["p_ref"],
                plot_df[column],
                label=curve_label,
                color=curve_map[case][1],
                linestyle=curve_map[case][0],
                marker=curve_map[case][2],
                linewidth=2,
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
        PROJECT_ROOT / f"figures/OUTPUT_{FILENAME}.pdf",
        format="pdf",
        bbox_inches="tight"
    )

    plt.show()
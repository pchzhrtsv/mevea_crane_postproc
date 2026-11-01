from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

PROJECT_ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":

    FILENAME = "dW_by_LP"

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.xmargin"] = 0

    fs = 20

    refp_l = [10, 20, 30, 40]

    Z_MIN = -15
    Z_MAX = 5
    zero_pos = (0-Z_MIN)/(Z_MAX-Z_MIN)

    cmap = LinearSegmentedColormap.from_list(
        "green_yellow_red",
        [(0.0, "green"), (zero_pos, "yellow"), (1.0, "red")]
    )

    norm = Normalize(vmin=Z_MIN, vmax=Z_MAX)

    levels_fill = np.linspace(Z_MIN, Z_MAX, 201)
    levels_lines = np.arange(Z_MIN, Z_MAX+1, 1)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    for refp in refp_l:

        plot_df = pd.read_csv(PROJECT_ROOT / f"csv_files/{FILENAME}_{refp}.csv")

        surface_df = plot_df.pivot_table(index="L", columns="P", values="dW", aggfunc="mean")
        surface_df = surface_df.sort_index()
        surface_df = surface_df.sort_index(axis=1)

        P_values = surface_df.columns.to_numpy()
        L_values = surface_df.index.to_numpy()
        Z = surface_df.to_numpy()

        X, Y = np.meshgrid(P_values, L_values)
        Z = np.ma.masked_invalid(Z)

        fig = plt.figure(figsize=(6.48, 5))
        ax = fig.add_subplot(111)

        surf = ax.contourf(
            X,
            Y,
            Z,
            levels=levels_fill,
            cmap=cmap,
            norm=norm,
            extend="both"
        )

        cs = ax.contour(
            X,
            Y,
            Z,
            levels=levels_lines,
            colors="black",
            linewidths=0.6,
            alpha=0.75
        )

        nonzero_levels = [level for level in cs.levels if level != 0]

        ax.clabel(
            cs,
            levels=nonzero_levels,
            inline=True,
            fmt=lambda value: f"{value:.0f}%",
            fontsize=fs
        )

        ax.contour(
            X,
            Y,
            Z,
            levels=[0],
            colors="white",
            linewidths=3.0
        )

        cs_zero = ax.contour(
            X,
            Y,
            Z,
            levels=[0],
            colors="black",
            linewidths=1.8
        )

        ax.clabel(
            cs_zero,
            levels=[0],
            inline=True,
            fmt={0: "0%"},
            fontsize=fs
        )

        ax.set_xlabel("Payload, kg", labelpad=10, fontsize=fs)
        ax.set_ylabel("Lightweighting, %", labelpad=10, fontsize=fs)

        ax.tick_params(axis="x", labelsize=fs)
        ax.tick_params(axis="y", labelsize=fs)

        ax.set_xlim(P_values.min(), P_values.max())
        ax.set_ylim(L_values.min(), L_values.max())


        ax.grid(True, linewidth=0.4, alpha=0.4)

        plt.tight_layout()

        plt.savefig(
            f"figures/OUTPUT_{FILENAME}_{refp}_hm.pdf",
            format="pdf",
            bbox_inches="tight"
        )

        plt.show(block=False)
        plt.pause(0.5)
        plt.close(fig)

    """|||||||||||||||||||||||||||||||||||||||||||||||||| COLORBAR ||||||||||||||||||||||||||||||||||||||||||||||||||"""

    fig = plt.figure(figsize=(6.48, 10))

    ax = fig.add_axes([0.47, 0.10, 0.035, .92])

    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(
        sm,
        cax=ax,
        extend="both",
        extendrect=True
    )

    cbar.set_label(
        "Consumption change, %",
        fontsize=fs,
        labelpad=10
    )

    cbar.set_ticks(np.arange(Z_MIN, Z_MAX+1, 5))
    cbar.ax.tick_params(labelsize=fs)

    plt.savefig(
        f"figures/OUTPUT_{FILENAME}_colorbar.pdf",
        format="pdf",
        bbox_inches="tight"
    )

    plt.show(block=False)
    plt.pause(0.5)
    plt.close(fig)
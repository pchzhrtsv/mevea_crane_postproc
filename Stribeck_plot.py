from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":

    x = np.array([0.0, 0.0001, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 1.0])
    y = np.array([0.0, 1.0, 0.09, 0.4, 0.225, 0.2, 0.225, 0.25, 0.3, 0.45])

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"

    fig, ax = plt.subplots(figsize=(6.48, 4.5))

    ax.plot(x, y, linestyle="--", marker="o", markersize=7, markerfacecolor="none", linewidth=1.5, color="red")

    ax.set_xlabel(r"$\dot{x}$, m/s", fontsize=20)
    ax.set_ylabel(r"$f$ $(\dot{x})$", fontsize=20)

    ax.tick_params(axis="both", labelsize=20)
    ax.grid(True)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()
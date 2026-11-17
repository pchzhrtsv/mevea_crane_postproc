"""Plot signed model-minus-experiment angle differences in radians.

Use the validation plot's 1 ms reference resampling and compare only times
covered by both the simulation and the original experimental trajectory.
"""
import matplotlib.pyplot as plt

from procedures_raw.export_model_validation_metrics import align_signal_errors
from utils.paths import FIGURES_DIR, PROJECT_ROOT
from utils.processing import realign_thetas
from utils.result_parser import load_ref_thetas, load_result
from matplotlib.ticker import FuncFormatter

def main():
    simulation = load_result(PROJECT_ROOT / "exp_pressures" / "validatio.txt")
    lift_reference, tilt_reference = load_ref_thetas(PROJECT_ROOT / "target_thetas")
    reference = realign_thetas(lift_reference, tilt_reference)

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    for name, signal, original in (
        ("Lift", "Lift_theta", lift_reference),
        ("Tilt", "Tilt_theta", tilt_reference),
    ):
        time, difference = align_signal_errors(
            simulation, reference, signal,
            start_time=float(original["Time"].iloc[0]),
            end_time=float(original["Time"].iloc[-1]),
        )
        fig, ax = plt.subplots(figsize=(6.48, 4.86))
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _:
                          "0" if value == 0
                          else f"{value:.0e}".replace("e-0", "e-").replace("e+0", "e+"))
        )
        ax.plot(time, difference, color=(0.2, 0.2, 0.2), linewidth=1)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Time, s", fontsize=20)
        ax.set_ylabel(rf"$\Delta \theta_{{{name.lower()}}}$, rad", fontsize=20)
        ax.set_xlim(time[0], time[-1])
        ax.tick_params(labelsize=20)
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"VALIDATION_{name}_theta_difference.pdf")

    plt.show()


if __name__ == "__main__":
    main()

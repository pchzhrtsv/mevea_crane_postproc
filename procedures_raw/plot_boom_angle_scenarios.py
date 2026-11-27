"""Compare reference and simulated Lift/Tilt angles; save plots and legend."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.paths import COMMITABLE_DATA_DIR, FIGURES_DIR, PROJECT_ROOT
from utils.processing import align_to_reference, realign_thetas
from utils.result_parser import load_ref_thetas, load_specific_results


if __name__ == "__main__":

    # ||||||||||||||||||||||||| SETTINGS |||||||||||||||||||||||||||

    case_set = [(0, 10, 30), (30, 10, 30), (0, 400, 30), (30, 400, 30)]
    case_styles = [
        ("#1E5AA8", "-"),
        ("#C55415", "-."),
        ("#217A45", ":"),
        ("#7944A0", (0, (5, 1, 1, 1, 1, 1))),
    ]
    fs = 20
    fig_size = (6.48, 4.40)
    start_time = 0.0
    motion_start_time = 2.5
    plt.rcParams.update({
        "font.family": "Times New Roman", "font.size": fs,
        "mathtext.fontset": "stix", "axes.labelsize": fs,
        "xtick.labelsize": fs, "ytick.labelsize": fs, "legend.fontsize": fs,
    })

    # |||||||||||||||||||||||||| READING |||||||||||||||||||||||||||

    datasets = load_specific_results(COMMITABLE_DATA_DIR, case_set)
    lift_theta_ds, tilt_theta_ds = load_ref_thetas(
        PROJECT_ROOT / "target_thetas"
    )
    if lift_theta_ds is None or tilt_theta_ds is None:
        raise ValueError(
            "Both Lift and Tilt reference trajectories are required"
        )

    # ||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||

    reference = realign_thetas(lift_theta_ds, tilt_theta_ds)
    frames = [reference, *(datasets[case] for case in case_set)]
    columns = ["Time", "Lift_theta", "Tilt_theta"]
    for data in frames:
        if not np.isfinite(data[columns].to_numpy(dtype=float)).all():
            raise ValueError("Non-finite plot signals")
        if len(data) < 2 or not np.all(np.diff(data.Time.to_numpy()) > 0):
            raise ValueError("Plot times must be strictly increasing")

    # Use the common recorded interval; do not extrapolate reference angles.
    end_time = min(
        float(lift_theta_ds.Time.iloc[-1]),
        float(tilt_theta_ds.Time.iloc[-1]),
        *(float(data.Time.iloc[-1]) for data in frames),
    )
    if (
        start_time < max(data.Time.iloc[0] for data in frames)
        or end_time <= start_time
    ):
        raise ValueError("No common plot interval starting at 0 s")

    # Keep original samples and interpolate only at the interval boundaries.
    plot_datasets = []
    for data in frames:
        time = data.Time.to_numpy()
        time_grid = pd.DataFrame({"Time": np.concatenate([
            [start_time], time[(time > start_time) & (time < end_time)],
            [end_time],
        ])})
        plot_datasets.append(align_to_reference(time_grid, data[columns]))
    reference = plot_datasets[0]
    datasets = dict(zip(case_set, plot_datasets[1:]))

    case_labels = []
    for lightening, payload, pressure in case_set:
        case_labels.append(
            rf"$L={lightening}\%;\ "
            rf"m_{{\mathrm{{pld}}}}={payload}\ \mathrm{{kg}};"
            rf"\ \Delta p_{{\mathrm{{LS}}}}={pressure}\ \mathrm{{bar}}$"
        )

    # |||||||||||||||||||||||||| PLOTTING ||||||||||||||||||||||||||

    figures = {}
    for boom in ("Lift", "Tilt"):
        signal = f"{boom}_theta"
        fig, ax = plt.subplots(figsize=fig_size)
        reference_line, = ax.plot(
            reference.Time, reference[signal], color="black", linestyle="--",
            linewidth=2.2, label="Reference", zorder=1,
        )
        case_handles = []
        for case, (color, style), label in zip(
            case_set, case_styles, case_labels
        ):
            data = datasets[case]
            line, = ax.plot(
                data.Time, data[signal], color=color, linestyle=style,
                linewidth=1.6, label=label,
            )
            case_handles.append(line)

        # The vertical line marks the start of motion I at 2.5 s.
        motion_boundaries = (2.5, 8.5, 15.0, 21.0)
        for mb in motion_boundaries:
            ax.axvline(
                mb, color="black", linestyle="--", linewidth=1.2,
                zorder=0.5, label="_motion_boundary",
            )
        ax.set_xlabel("Time, s")
        ax.set_ylabel(rf"$\theta_{{\mathrm{{{boom.lower()}}}}}$, rad")
        ax.set_xlim(start_time, end_time)
        ax.grid(True, alpha=0.45)
        fig.subplots_adjust(left=0.19, right=0.97, top=0.97, bottom=0.17)
        figures[boom] = fig

    # ||||||||||||||||||||||||||| LEGEND |||||||||||||||||||||||||||

    # Each column contains 0% above 30%; Reference is in the rightmost column.
    legend_figure = plt.figure(figsize=(12.96, 1.5))
    legend_figure.legend(
        [*case_handles, reference_line], [*case_labels, "Reference"],
        loc="center", ncol=3, frameon=False, fontsize=fs,
        columnspacing=1.5, handlelength=2.2,
    )

    # ||||||||||||||||||||||||||| SAVING |||||||||||||||||||||||||||

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for boom, fig in figures.items():
        stem = f"OUTPUT_boom_angle_scenarios_{boom.lower()}"
        fig.savefig(FIGURES_DIR / f"{stem}.pdf", bbox_inches="tight")
        fig.savefig(FIGURES_DIR / f"{stem}.png", dpi=200, bbox_inches="tight")
    legend_figure.savefig(
        FIGURES_DIR / "LEGEND_boom_angle_scenarios.pdf", bbox_inches="tight",
    )
    legend_figure.savefig(
        FIGURES_DIR / "LEGEND_boom_angle_scenarios.png",
        dpi=200, bbox_inches="tight",
    )
    plt.show()

"""Compare reference and simulated P-port flows; save plots and legend."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.paths import COMMITABLE_DATA_DIR, FIGURES_DIR, PROJECT_ROOT
from utils.processing import align_to_reference
from utils.result_parser import load_result, load_specific_results


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
    fig_size = (6.48, 5.40)
    start_time = 0.0
    motion_boundaries = (2.5, 8.5, 15.0, 21.0)
    plt.rcParams.update({
        "font.family": "Times New Roman", "font.size": fs,
        "mathtext.fontset": "stix", "axes.labelsize": fs,
        "xtick.labelsize": fs, "ytick.labelsize": fs, "legend.fontsize": fs,
    })

    # |||||||||||||||||||||||||| READING |||||||||||||||||||||||||||

    datasets = load_specific_results(COMMITABLE_DATA_DIR, case_set)
    reference = load_result(PROJECT_ROOT / "exp_pressures" / "validatio.txt")

    # ||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||

    frames = [reference, *(datasets[case] for case in case_set)]
    columns = ["Time", "Lift_DV_QP", "Tilt_DV_QP"]
    for data in frames:
        if not np.isfinite(data[columns].to_numpy(dtype=float)).all():
            raise ValueError("Non-finite plot signals")
        if len(data) < 2 or not np.all(np.diff(data.Time.to_numpy()) > 0):
            raise ValueError("Plot times must be strictly increasing")

    end_time = min(float(data.Time.iloc[-1]) for data in frames)
    if (
        start_time < max(data.Time.iloc[0] for data in frames)
        or end_time <= start_time
    ):
        raise ValueError("No common plot interval starting at 0 s")

    # Keep original samples and interpolate only at the interval boundaries.
    # Preserve raw port signs and L/min units; do not smooth the flows.
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
        signal = f"{boom}_DV_QP"
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

        # Phase lines and alternating background, as in plot_pump_power_change.
        motion_times = [
            start_time,
            *(t for t in motion_boundaries if start_time < t < end_time),
            end_time,
        ]
        for t in motion_times[1:-1]:
            ax.axvline(
                t, color="black", linestyle="--", linewidth=1.2,
                zorder=0.5, label="_motion_boundary",
            )
        for i in range(len(motion_times) - 1):
            if i % 2 == 0:
                ax.axvspan(
                    motion_times[i], motion_times[i + 1], color="black",
                    alpha=0.035, zorder=0, label="_motion_shading",
                )
        ax.set_xlabel("Time, s")
        ax.set_ylabel(rf"$Q_{{P,\mathrm{{{boom.lower()}}}}}$, L/min")
        ax.set_xlim(start_time, end_time)
        ax.grid(True, alpha=0.45)
        fig.subplots_adjust(left=0.19, right=0.97, top=0.97, bottom=0.17)
        figures[boom] = fig

    # ||||||||||||||||||||||||||| LEGEND |||||||||||||||||||||||||||

    # Each column has 0% above 30%; Reference is in the rightmost column.
    legend_figure = plt.figure(figsize=(12.96, 1.5))
    legend_figure.legend(
        [*case_handles, reference_line], [*case_labels, "Reference"],
        loc="center", ncol=3, frameon=False, fontsize=fs,
        columnspacing=1.5, handlelength=2.2,
    )

    # ||||||||||||||||||||||||||| SAVING |||||||||||||||||||||||||||

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for boom, fig in figures.items():
        stem = f"OUTPUT_valve_supply_flow_scenarios_{boom.lower()}"
        fig.savefig(FIGURES_DIR / f"{stem}.pdf", bbox_inches="tight")
        fig.savefig(FIGURES_DIR / f"{stem}.png", dpi=200, bbox_inches="tight")
    legend_figure.savefig(
        FIGURES_DIR / "LEGEND_valve_supply_flow_scenarios.pdf",
        bbox_inches="tight",
    )
    legend_figure.savefig(
        FIGURES_DIR / "LEGEND_valve_supply_flow_scenarios.png",
        dpi=200, bbox_inches="tight",
    )
    plt.show()

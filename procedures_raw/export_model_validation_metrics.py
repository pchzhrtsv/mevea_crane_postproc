"""Export six simulation/experiment error metrics using the validation plots.

Use validatio.txt, press1..4.txt, and the two target_thetas trajectories.
Start comparison at exactly 2.5 s; keep the plot's 0.001 s angle resampling.
Compare only overlapping recorded time ranges, without extrapolation,
additional filtering, or time shifts. Error is simulation minus experiment.
"""
import numpy as np
import pandas as pd

from utils.paths import CSV_DIR, PROJECT_ROOT
from utils.processing import align_to_reference, realign_thetas
from utils.result_parser import load_ref_thetas, load_result


VALIDATION_DIR = PROJECT_ROOT / "exp_pressures"
ANGLE_DIR = PROJECT_ROOT / "target_thetas"
OUTPUT_FILE = CSV_DIR / "model_validation_metrics.csv"
SIMULATION_START_TIME = 2.5
OUTPUT_COLUMNS = [
    "Signal", "Unit", "RMSE", "Maximum absolute error", "Mean signed error",
]


def align_signal_errors(
    simulation: pd.DataFrame,
    experiment: pd.DataFrame,
    signal: str,
    experimental_signal: str | None = None,
    end_time: float | None = None,
    start_time: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return shared times and signed simulation-minus-reference errors.

    Time is in seconds; signal values must already use the requested units.
    Combine both sets of sample times within their overlap and interpolate
    linearly. The returned time/error arrays retain both sets of time knots.
    end_time can limit resampled references to their original measured range.
    start_time sets an exact lower bound, interpolating at it when necessary.
    Inputs must be finite and have at least two strictly increasing times.
    Neither input DataFrame is modified.
    """
    experimental_signal = experimental_signal or signal
    simulation = simulation[["Time", signal]]
    experiment = experiment[["Time", experimental_signal]]
    for label, dataset in (("Simulation", simulation), ("Experiment", experiment)):
        if not np.isfinite(dataset.to_numpy(dtype=float)).all():
            raise ValueError(f"{label} contains missing or non-finite values")
        time = dataset["Time"].to_numpy(dtype=float)
        if len(time) < 2 or not np.all(np.diff(time) > 0):
            raise ValueError(f"{label} needs strictly increasing time samples")

    sim_time = simulation["Time"].to_numpy(dtype=float)
    exp_time = experiment["Time"].to_numpy(dtype=float)
    start = max(float(sim_time[0]), float(exp_time[0]))
    end = min(float(sim_time[-1]), float(exp_time[-1]))
    if start_time is not None:
        if not np.isfinite(start_time):
            raise ValueError("Start time must be finite")
        start = max(start, start_time)
    if end_time is not None:
        if not np.isfinite(end_time):
            raise ValueError("End time must be finite")
        end = min(end, end_time)
    if end <= start:
        raise ValueError("Signals have no overlapping interval of positive length")

    time = np.unique(np.concatenate([
        [start, end],
        sim_time[(sim_time >= start) & (sim_time <= end)],
        exp_time[(exp_time >= start) & (exp_time <= end)],
    ]))
    grid = pd.DataFrame({"Time": time})
    sim_values = align_to_reference(grid, simulation)[signal].to_numpy()
    exp_values = align_to_reference(grid, experiment)[experimental_signal].to_numpy()
    error = sim_values - exp_values
    return time, error


def calculate_signal_metrics(
    simulation: pd.DataFrame,
    experiment: pd.DataFrame,
    signal: str,
    experimental_signal: str | None = None,
    end_time: float | None = None,
    start_time: float | None = None,
) -> dict[str, float]:
    """Return time-weighted RMSE, max absolute error, and signed bias.

    Align signals without extrapolation and integrate d**2 and d by the
    trapezoidal rule, dividing by the common interval's duration in seconds.
    Signal units are unchanged. Neither input DataFrame is modified.
    """
    time, error = align_signal_errors(
        simulation, experiment, signal, experimental_signal,
        end_time=end_time, start_time=start_time,
    )
    duration = time[-1] - time[0]
    return {
        "RMSE": float(np.sqrt(np.trapezoid(error**2, x=time) / duration)),
        "Maximum absolute error": float(np.max(np.abs(error))),
        "Mean signed error": float(np.trapezoid(error, x=time) / duration),
    }


def build_validation_metrics() -> pd.DataFrame:
    """Build the requested five-column table for two angles and four pressures.

    Angle references are the target_thetas curves labelled Experiment in
    plot_model_vs_experiment.py. Their original last sample bounds evaluation,
    excluding the constant tail introduced by realign_thetas up to 30 seconds.
    """
    simulation = load_result(VALIDATION_DIR / "validatio.txt")
    lift_reference, tilt_reference = load_ref_thetas(ANGLE_DIR)
    angle_reference = realign_thetas(lift_reference, tilt_reference)

    rows = []
    for label, signal, raw_reference in (
        ("Lift angle", "Lift_theta", lift_reference),
        ("Tilt angle", "Tilt_theta", tilt_reference),
    ):
        metrics = calculate_signal_metrics(
            simulation, angle_reference, signal,
            end_time=float(raw_reference["Time"].iloc[-1]),
            start_time=SIMULATION_START_TIME,
        )
        rows.append({"Signal": label, "Unit": "rad", **metrics})

    for label, signal, filename in (
        ("Lift chamber A pressure", "Lift_A_p", "press1.txt"),
        ("Lift chamber B pressure", "Lift_B_p", "press2.txt"),
        ("Tilt chamber A pressure", "Tilt_A_p", "press3.txt"),
        ("Tilt chamber B pressure", "Tilt_B_p", "press4.txt"),
    ):
        reference = load_result(VALIDATION_DIR / filename, sep=" ")
        metrics = calculate_signal_metrics(
            simulation, reference, signal, experimental_signal=f"{signal}_exp",
            start_time=SIMULATION_START_TIME,
        )
        rows.append({"Signal": label, "Unit": "bar", **metrics})

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main():
    summary = build_validation_metrics()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(summary.to_string(index=False))
    print(f"Saved metrics to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

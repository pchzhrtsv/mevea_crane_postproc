"""Export angular tracking-error metrics for every commitable_data scenario.

Error is simulated angle minus the target_thetas reference, in radians.
RMSE and mean signed error use trapezoidal time weighting over the analysis
interval. Maximum is max(abs(error)); mean signed error is integral(error) / T.
Start at exactly 2.5 s and stop at each reference's last original sample.
"""

import numpy as np
import pandas as pd
from tqdm import tqdm

from procedures_raw.export_hydraulic_energy_balance import CASE_PATTERN
from procedures_raw.export_model_validation_metrics import align_signal_errors
from utils.paths import COMMITABLE_DATA_DIR, CSV_DIR, PROJECT_ROOT
from utils.processing import realign_thetas
from utils.result_parser import load_ref_thetas, load_result


OUTPUT_FILE = CSV_DIR / "boom_angle_error_metrics.csv"
ANGLE_DIR = PROJECT_ROOT / "target_thetas"
START_TIME = 2.5
BOOM_SIGNALS = {"lift": "Lift_theta", "tilt": "Tilt_theta"}


def calculate_boom_angle_error_metrics(
    dataset: pd.DataFrame,
    reference: pd.DataFrame,
    reference_end_times: dict[str, float],
    start_time: float = START_TIME,
) -> dict[str, float]:
    """
        Return separate Lift/Tilt RMSE, absolute maximum, and mean signed error.
    """
    result = {}
    for boom, signal in BOOM_SIGNALS.items():
        time, error = align_signal_errors(
            dataset, reference, signal,
            start_time=start_time, end_time=reference_end_times[signal],
        )
        duration = time[-1] - time[0]
        result[f"{boom}_rmse_rad"] = float(
            np.sqrt(np.trapezoid(error**2, x=time) / duration)
        )
        result[f"{boom}_max_absolute_error_rad"] = float(np.max(np.abs(error)))
        result[f"{boom}_mean_signed_error_rad"] = float(
            np.trapezoid(error, x=time) / duration
        )
    return result


def main():

    # |||||||||||||||||||||||||| READING |||||||||||||||||||||||||||
    files = sorted(COMMITABLE_DATA_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No simulation TXT files found in {COMMITABLE_DATA_DIR}")
    lift_reference, tilt_reference = load_ref_thetas(ANGLE_DIR)
    if lift_reference is None or tilt_reference is None:
        raise ValueError("Both z1 (Lift) and z4 (Tilt) angle references are required")

    # ||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||
    reference_end_times = {
        "Lift_theta": float(lift_reference["Time"].iloc[-1]),
        "Tilt_theta": float(tilt_reference["Time"].iloc[-1]),
    }
    reference = realign_thetas(lift_reference, tilt_reference)

    # Read and process one scenario at a time.
    rows = []
    for file_path in tqdm(files, desc="Boom angle error metrics", unit="case"):
        match = CASE_PATTERN.fullmatch(file_path.stem)
        if match is None:
            raise ValueError(f"Unexpected dataset filename: {file_path.name}")
        parameters = {
            "lightweighting_percent": int(match["lightweighting"]),
            "rfp": int(match["rfp"]),
            "payload_kg": int(match["payload"]),
        }
        try:
            dataset = load_result(file_path)
            metrics = calculate_boom_angle_error_metrics(
                dataset, reference, reference_end_times, start_time=2.5
            )
            del dataset
        except (ValueError, KeyError) as error:
            raise ValueError(f"{file_path.name}: {error}") from error
        rows.append({**parameters, **metrics})

    summary = pd.DataFrame(rows).sort_values(
        ["lightweighting_percent", "rfp", "payload_kg"], ignore_index=True
    )

    # |||||||||||||||||||||||||| WRITING |||||||||||||||||||||||||||
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(summary)} angle-error scenarios to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

"""Compare valve supply flows and pressure/flow energy effects by motion.

Reference: exp_pressures/validatio.txt. Analyze every commitable_data case,
both valve P ports, and their sum. Energy is at the valve supply ports;
reference Pump_Q is unavailable, so this is not total pump output energy.
Use raw signals, exact motion boundaries, and trapezoidal integration.
See docs/valve_flow_energy_metrics.md for definitions and interpretation.
"""

import numpy as np
import pandas as pd
from tqdm import tqdm

from procedures_raw.export_hydraulic_energy_balance import CASE_PATTERN
from procedures_raw.export_hydraulic_energy_balance_by_motion import MOTIONS
from utils.paths import COMMITABLE_DATA_DIR, CSV_DIR, PROJECT_ROOT
from utils.processing import align_to_reference
from utils.result_parser import load_result


REFERENCE_FILE = PROJECT_ROOT / "exp_pressures" / "validatio.txt"
OUTPUT_FILE = CSV_DIR / "valve_flow_energy_by_motion.csv"
FLOW_SIGNALS = {"lift": "Lift_DV_QP", "tilt": "Tilt_DV_QP"}
REQUIRED_COLUMNS = ["Time", "VolPump_p", *FLOW_SIGNALS.values()]


def prepare_supply_signals(dataset: pd.DataFrame) -> pd.DataFrame:

    missing = sorted(set(REQUIRED_COLUMNS) - set(dataset.columns))
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    if not np.isfinite(dataset[REQUIRED_COLUMNS].to_numpy(dtype=float)).all():
        raise ValueError("Missing or non-finite supply signals")
    time = dataset["Time"].to_numpy(dtype=float)
    if len(time) < 2 or not np.all(np.diff(time) > 0):
        raise ValueError("At least two strictly increasing times are required")
    result = pd.DataFrame({"Time": time})
    result["pressure_bar"] = dataset["VolPump_p"].to_numpy() - 1.0
    for valve, signal in FLOW_SIGNALS.items():
        result[valve] = -dataset[signal].to_numpy()
    result["total"] = result["lift"] + result["tilt"]
    return result


def align_motion_signals(
    case: pd.DataFrame, reference: pd.DataFrame, start: float, end: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    time = np.unique(np.concatenate([
        [start, end],
        case.loc[(case.Time > start) & (case.Time < end), "Time"].to_numpy(),
        reference.loc[
            (reference.Time > start) & (reference.Time < end), "Time"
        ].to_numpy(),
    ]))
    grid = pd.DataFrame({"Time": time})
    return align_to_reference(grid, case), align_to_reference(grid, reference)


def relative_percent(numerator: float, denominator: float) -> float:
    return float(100 * numerator / denominator) if denominator != 0 else np.nan


def calculate_flow_energy_metrics(
    time: np.ndarray,
    pressure: np.ndarray,
    flow: np.ndarray,
    reference_pressure: np.ndarray,
    reference_flow: np.ndarray,
) -> dict[str, float]:
    duration = float(time[-1] - time[0])
    volume = float(np.trapezoid(flow, x=time) / 60)
    reference_volume = float(np.trapezoid(reference_flow, x=time) / 60)
    reference_rms = float(
        np.sqrt(np.trapezoid(reference_flow**2, x=time) / duration)
    )
    flow_rmse = float(
        np.sqrt(np.trapezoid((flow - reference_flow)**2, x=time) / duration)
    )
    mean_pressure = float(np.trapezoid(pressure, x=time) / duration)
    reference_mean_pressure = float(
        np.trapezoid(reference_pressure, x=time) / duration
    )
    energy = float(np.trapezoid(pressure * flow / 600, x=time))
    reference_energy = float(
        np.trapezoid(reference_pressure * reference_flow / 600, x=time)
    )
    flow_effect = float(np.trapezoid(
        (pressure + reference_pressure) / 2 * (flow - reference_flow) / 600,
        x=time,
    ))
    pressure_effect = float(np.trapezoid(
        (flow + reference_flow) / 2 * (pressure - reference_pressure) / 600,
        x=time,
    ))
    return {
        "net_volume_reference_l": reference_volume,
        "net_volume_case_l": volume,
        "net_volume_change_percent": relative_percent(
            volume - reference_volume, reference_volume
        ),
        "flow_nrmse_percent": relative_percent(flow_rmse, reference_rms),
        "mean_pressure_reference_bar": reference_mean_pressure,
        "mean_pressure_case_bar": mean_pressure,
        "mean_pressure_change_percent": relative_percent(
            mean_pressure - reference_mean_pressure, reference_mean_pressure
        ),
        "valve_supply_energy_reference_kj": reference_energy,
        "valve_supply_energy_case_kj": energy,
        "energy_change_percent": relative_percent(
            energy - reference_energy, reference_energy
        ),
        "flow_effect_kj": flow_effect,
        "pressure_effect_kj": pressure_effect,
        "flow_effect_pp": relative_percent(flow_effect, reference_energy),
        "pressure_effect_pp": relative_percent(pressure_effect, reference_energy),
        "pressure_dominance_percent": relative_percent(
            abs(pressure_effect), abs(flow_effect) + abs(pressure_effect)
        ),
        "decomposition_residual_kj": (
            energy - reference_energy - flow_effect - pressure_effect
        ),
    }


def summarize_prepared_case(
    case: pd.DataFrame, reference: pd.DataFrame
) -> pd.DataFrame:
    """Return 12 rows: four motions times Lift, Tilt, and total valve supply."""
    end_of_record = min(float(case.Time.iloc[-1]), float(reference.Time.iloc[-1]))
    rows = []
    for motion, start, end in MOTIONS:
        end = end_of_record if end is None else end
        actual, baseline = align_motion_signals(case, reference, start, end)
        time = actual.Time.to_numpy()
        for valve in ("lift", "tilt", "total"):
            metrics = calculate_flow_energy_metrics(
                time, actual.pressure_bar.to_numpy(), actual[valve].to_numpy(),
                baseline.pressure_bar.to_numpy(), baseline[valve].to_numpy(),
            )
            rows.append({
                "motion": motion, "start_time_s": start, "end_time_s": end,
                "valve": valve, **metrics,
            })
    return pd.DataFrame(rows)


def main():
    # |||||||||||||||||||||||||| READING |||||||||||||||||||||||||||
    files = sorted(COMMITABLE_DATA_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No simulation TXT files in {COMMITABLE_DATA_DIR}")
    reference_dataset = load_result(REFERENCE_FILE)

    # ||||||||||||||||||||||||| PROCESSING |||||||||||||||||||||||||
    reference = prepare_supply_signals(reference_dataset)
    del reference_dataset
    rows = []
    for path in tqdm(files, desc="Valve flow/pressure energy effects", unit="case"):
        match = CASE_PATTERN.fullmatch(path.stem)
        if match is None:
            raise ValueError(f"Unexpected scenario filename: {path.name}")
        parameters = {
            "lightweighting_percent": int(match["lightweighting"]),
            "rfp": int(match["rfp"]), "payload_kg": int(match["payload"]),
        }
        try:
            case = prepare_supply_signals(load_result(path))
            case_summary = summarize_prepared_case(case, reference)
        except (ValueError, KeyError) as error:
            raise ValueError(f"{path.name}: {error}") from error
        rows.extend(
            {**parameters, **row} for row in case_summary.to_dict(orient="records")
        )

    summary = pd.DataFrame(rows).sort_values(
        ["lightweighting_percent", "rfp", "payload_kg", "motion", "valve"],
        ignore_index=True,
    )

    # |||||||||||||||||||||||||| WRITING |||||||||||||||||||||||||||
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(summary)} valve/motion comparisons to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

"""Correlate 30%-minus-0% flow and pump-power changes for matched scenarios.

Match payload and R code, then analyze each of the four motions separately.
Align the 30% case to the 0% grid, calculate hydraulic pump power, remove
peaks (window 20), and subtract. Flow differences use the raw exported
Lift_DV_QP, Tilt_DV_QP, and Pump_Q signs, with no additional filtering.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from procedures_raw.export_hydraulic_energy_balance import CASE_PATTERN
from procedures_raw.export_hydraulic_energy_balance_by_motion import (
    MOTIONS, select_power_interval,
)
from utils.paths import COMMITABLE_DATA_DIR, CSV_DIR
from utils.processing import align_to_reference, clean_spikes
from utils.result_parser import load_result


OUTPUT_FILE = CSV_DIR / "lightweighting_flow_power_correlations.csv"
FLOW_SIGNALS = {
    "lift_dv_qp": "Lift_DV_QP",
    "tilt_dv_qp": "Tilt_DV_QP",
    "pump_q": "Pump_Q",
}
REQUIRED_COLUMNS = ["Time", "VolPump_p", *FLOW_SIGNALS.values()]


def prepare_pair_changes(
    baseline: pd.DataFrame, lightened: pd.DataFrame
) -> pd.DataFrame:
    """Return aligned flows and processed P_0/P_30/dP in kW.

    Validate source values and full time coverage before interpolation.
    Use the pump-power conversion factors from plot_pump_power_change.
    Neither source DataFrame is modified; all filters act on a new frame.
    """
    for label, data in (("0%", baseline), ("30%", lightened)):
        missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
        if missing:
            raise ValueError(f"{label} missing columns: {', '.join(missing)}")
        if not np.isfinite(data[REQUIRED_COLUMNS].to_numpy(dtype=float)).all():
            raise ValueError(f"{label} contains non-finite source signals")
        time = data.Time.to_numpy(dtype=float)
        if len(time) < 2 or not np.all(np.diff(time) > 0):
            raise ValueError(f"{label} needs strictly increasing time samples")
    if (baseline.Time.iloc[0] < lightened.Time.iloc[0]
            or baseline.Time.iloc[-1] > lightened.Time.iloc[-1]):
        raise ValueError("30% data must cover the 0% time grid")
    actual = align_to_reference(baseline, lightened[REQUIRED_COLUMNS])
    result = pd.DataFrame({"Time": baseline.Time.to_numpy()})
    result["P_0"] = (
        (baseline.VolPump_p.to_numpy() - 1) * baseline.Pump_Q.to_numpy()
        / 60000 * 1e5 / 1e3
    )
    result["P_30"] = (
        (actual.VolPump_p - 1) * actual.Pump_Q / 60000 * 1e5 / 1e3
    )
    for column in ("P_0", "P_30"):
        clean_spikes(result, column, key_clean=column, window=20)
    result["dP"] = result["P_30"] - result["P_0"]
    for name, signal in FLOW_SIGNALS.items():
        result[f"{name}_0"] = baseline[signal].to_numpy()
        result[f"{name}_30"] = actual[signal].to_numpy()
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Non-finite aligned or filtered pair signals")
    return result


def time_mean(time: np.ndarray, values: np.ndarray) -> float:
    """Return the trapezoidal time mean on a positive-duration interval."""
    return float(np.trapezoid(values, x=time) / (time[-1] - time[0]))


def percent_change(numerator: float, denominator: float) -> float:
    """Return a percentage, or NaN if its baseline denominator is zero."""
    return float(100 * numerator / denominator) if denominator != 0 else np.nan


def correlate_changes(
    time: np.ndarray, flow_delta: np.ndarray, power_delta: np.ndarray
) -> dict[str, float]:
    """Time-weighted Pearson r, single-predictor R-squared, and slope.

    Relate simultaneous signed delta-Q (L/min) to delta-P (kW), without lag
    optimization. R-squared is descriptive regression fit, not causal effect.
    Constant delta signals give undefined r/R-squared (NaN); constant delta-Q
    also gives an undefined regression slope.
    """
    dq = flow_delta - time_mean(time, flow_delta)
    dp = power_delta - time_mean(time, power_delta)
    q_variance = time_mean(time, dq**2)
    p_variance = time_mean(time, dp**2)
    covariance = time_mean(time, dq * dp)
    q_constant = np.ptp(flow_delta) == 0 or q_variance <= 0
    p_constant = np.ptp(power_delta) == 0 or p_variance <= 0
    slope = np.nan if q_constant else covariance / q_variance
    if q_constant or p_constant:
        correlation = np.nan
    else:
        correlation = float(np.clip(
            covariance / np.sqrt(q_variance * p_variance), -1.0, 1.0
        ))
    return {
        "pearson_r": correlation,
        "r_squared_percent": float(100 * correlation**2),
        "slope_kw_per_l_min": float(slope),
    }


def summarize_pair_changes(changes: pd.DataFrame) -> pd.DataFrame:
    """Return four motion rows; correlations concern changes, not signal levels."""
    rows = []
    for motion, start, end in MOTIONS:
        end = float(changes.Time.iloc[-1]) if end is None else end
        interval = select_power_interval(changes, start, end)
        time = interval.Time.to_numpy()
        p0, p30 = interval.P_0.to_numpy(), interval.P_30.to_numpy()
        dp = interval.dP.to_numpy()
        mean_p0, mean_p30 = time_mean(time, p0), time_mean(time, p30)
        row = {
            "motion": motion, "start_time_s": start, "end_time_s": end,
            "power_0_mean_kw": mean_p0, "power_30_mean_kw": mean_p30,
            "power_mean_change_percent": percent_change(
                mean_p30 - mean_p0, mean_p0
            ),
            "power_delta_rms_kw": float(np.sqrt(time_mean(time, dp**2))),
        }
        for name in FLOW_SIGNALS:
            q0 = interval[f"{name}_0"].to_numpy()
            q30 = interval[f"{name}_30"].to_numpy()
            dq = q30 - q0
            mean_q0, mean_q30 = time_mean(time, q0), time_mean(time, q30)
            metrics = {
                "mean_0_l_min": mean_q0,
                "mean_30_l_min": mean_q30,
                "mean_change_percent": percent_change(
                    mean_q30 - mean_q0, mean_q0
                ),
                "delta_rms_percent": percent_change(
                    np.sqrt(time_mean(time, dq**2)),
                    np.sqrt(time_mean(time, q0**2)),
                ),
                **correlate_changes(time, dq, dp),
            }
            row.update({f"{name}_{key}": value for key, value in metrics.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def find_scenario_pairs(
    source_dir: Path = COMMITABLE_DATA_DIR,
) -> dict:
    """Find 0%/30% files by payload/R; exclude intermediate lightening cases."""
    pairs = {}
    for path in Path(source_dir).glob("*.txt"):
        match = CASE_PATTERN.fullmatch(path.stem)
        if match is None:
            raise ValueError(f"Unexpected scenario filename: {path.name}")
        lightening = int(match["lightweighting"])
        if lightening not in (0, 30):
            continue
        key = (int(match["rfp"]), int(match["payload"]))
        group = pairs.setdefault(key, {})
        if lightening in group:
            raise ValueError(f"Duplicate {lightening}% scenario for {key}")
        group[lightening] = path
    if not pairs:
        raise FileNotFoundError(f"No 0%/30% scenario pairs in {source_dir}")
    return pairs


def build_correlation_summary(
    source_dir: Path = COMMITABLE_DATA_DIR,
) -> pd.DataFrame:
    """Match 0%/30% at each payload/R; 10%/20% do not enter these pairs."""
    pairs = find_scenario_pairs(source_dir)
    rows = []
    for (rfp, payload), pair in tqdm(
        sorted(pairs.items()), desc="Paired flow/power correlations", unit="pair"
    ):
        if set(pair) != {0, 30}:
            raise ValueError(f"Incomplete 0%/30% pair: R{rfp}, P{payload}")
        try:
            changes = prepare_pair_changes(load_result(pair[0]), load_result(pair[30]))
            summary = summarize_pair_changes(changes)
        except (ValueError, KeyError) as error:
            raise ValueError(f"R{rfp}, P{payload}: {error}") from error
        rows.extend(
            {"rfp": rfp, "payload_kg": payload, **row}
            for row in summary.to_dict(orient="records")
        )
    return pd.DataFrame(rows).sort_values(
        ["rfp", "payload_kg", "motion"], ignore_index=True
    )


def main():
    summary = build_correlation_summary()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(summary)} paired motion correlations to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

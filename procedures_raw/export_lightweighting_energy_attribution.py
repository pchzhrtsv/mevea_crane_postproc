"""Attribute paired 0%/30% pump-energy changes to flow and pressure.

Use the same pump-power calculation and 50/200 filtering as
plot_pump_power_change.py, including two mixed pressure/flow combinations.
The symmetric two-order allocation closes exactly even with nonlinear spike
filtering. Also report direct paired angle differences and flow deviations.
No trajectory-equivalence threshold or automatic confidence label is imposed.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from procedures_raw.export_hydraulic_energy_balance_by_motion import (
    MOTIONS, select_power_interval,
)
from procedures_raw.export_lightweighting_flow_power_correlations import (
    FLOW_SIGNALS, find_scenario_pairs, percent_change, prepare_pair_changes,
    time_mean,
)
from utils.paths import COMMITABLE_DATA_DIR, CSV_DIR
from utils.processing import align_to_reference, clean_spikes, smooth_series
from utils.result_parser import load_result


OUTPUT_FILE = CSV_DIR / "lightweighting_energy_attribution.csv"
ANGLE_SIGNALS = {"lift": "Lift_theta", "tilt": "Tilt_theta"}


def process_mixed_power(pressure: np.ndarray, flow: np.ndarray) -> np.ndarray:
    """Return kW from gauge bar and L/min, with the reference 50/200 pipeline."""
    power = pd.DataFrame({"power": pressure * flow / 60000 * 1e5 / 1e3})
    clean_spikes(power, "power", key_clean="power", window=50)
    smooth_series(power, "power", key_smooth="power", window=200)
    return power["power"].to_numpy()


def prepare_energy_attribution(
    baseline: pd.DataFrame, lightened: pd.DataFrame
) -> pd.DataFrame:
    """Return full-record power effects and paired flow/angle signals.

    P_ab means processed power using pressure from case a and pump flow from
    case b. Actual P_0/P_30 come from the existing comparison procedure.
    Preserve original data; interpolation and filters operate on new frames.
    """
    changes = prepare_pair_changes(baseline, lightened)
    columns = ["Time", "VolPump_p", *ANGLE_SIGNALS.values()]
    for label, data in (("0%", baseline), ("30%", lightened)):
        if not np.isfinite(data[columns].to_numpy(dtype=float)).all():
            raise ValueError(f"{label} has non-finite angle/pressure signals")
    actual = align_to_reference(baseline, lightened[columns])
    p0 = baseline.VolPump_p.to_numpy() - 1.0
    p30 = actual.VolPump_p.to_numpy() - 1.0
    q0 = changes.pump_q_0.to_numpy()
    q30 = changes.pump_q_30.to_numpy()
    power_01 = process_mixed_power(p0, q30)
    power_10 = process_mixed_power(p30, q0)
    power_00 = changes.P_0.to_numpy()
    power_11 = changes.P_30.to_numpy()
    changes["flow_effect_kw"] = (
        (power_01 - power_00) + (power_11 - power_10)
    ) / 2
    changes["pressure_effect_kw"] = (
        (power_10 - power_00) + (power_11 - power_01)
    ) / 2
    changes["raw_flow_effect_kw"] = (
        (p0 + p30) / 2 * (q30 - q0) / 600
    )
    changes["raw_pressure_effect_kw"] = (
        (q0 + q30) / 2 * (p30 - p0) / 600
    )
    changes["pressure_0_bar"] = p0
    changes["pressure_30_bar"] = p30
    for boom, signal in ANGLE_SIGNALS.items():
        changes[f"{boom}_angle_delta_rad"] = (
            actual[signal].to_numpy() - baseline[signal].to_numpy()
        )
    if not np.isfinite(changes.to_numpy(dtype=float)).all():
        raise ValueError("Non-finite processed energy-attribution signals")
    return changes


def summarize_energy_attribution(changes: pd.DataFrame) -> pd.DataFrame:
    """Return four phase rows with signed energy effects and trajectory checks.

    Contributions in percentage points use processed baseline pump energy.
    The magnitude ratio uses absolute *net* effects, so absolute effect
    integrals and paired angle errors are supplied to expose cancellation.
    """
    rows = []
    for motion, start, end in MOTIONS:
        end = float(changes.Time.iloc[-1]) if end is None else end
        interval = select_power_interval(changes, start, end)
        time = interval.Time.to_numpy()

        def integral(column, absolute=False):
            values = interval[column].to_numpy()
            return float(np.trapezoid(np.abs(values) if absolute else values, x=time))

        energy_0 = integral("P_0")
        energy_30 = integral("P_30")
        flow_effect = integral("flow_effect_kw")
        pressure_effect = integral("pressure_effect_kw")
        row = {
            "motion": motion, "start_time_s": start, "end_time_s": end,
            "pump_energy_0_kj": energy_0, "pump_energy_30_kj": energy_30,
            "pump_energy_change_kj": energy_30 - energy_0,
            "pump_energy_change_percent": percent_change(
                energy_30 - energy_0, energy_0
            ),
            "flow_effect_kj": flow_effect,
            "pressure_effect_kj": pressure_effect,
            "flow_effect_pp": percent_change(flow_effect, energy_0),
            "pressure_effect_pp": percent_change(pressure_effect, energy_0),
            "flow_effect_magnitude_percent": percent_change(
                abs(flow_effect), abs(flow_effect) + abs(pressure_effect)
            ),
            "flow_effect_absolute_pp": percent_change(
                integral("flow_effect_kw", absolute=True), energy_0
            ),
            "pressure_effect_absolute_pp": percent_change(
                integral("pressure_effect_kw", absolute=True), energy_0
            ),
            "decomposition_residual_kj": (
                energy_30 - energy_0 - flow_effect - pressure_effect
            ),
            "raw_flow_effect_kj": integral("raw_flow_effect_kw"),
            "raw_pressure_effect_kj": integral("raw_pressure_effect_kw"),
        }
        mean_p0 = time_mean(time, interval.pressure_0_bar.to_numpy())
        mean_p30 = time_mean(time, interval.pressure_30_bar.to_numpy())
        row.update({
            "pressure_mean_0_bar": mean_p0,
            "pressure_mean_30_bar": mean_p30,
            "pressure_mean_change_percent": percent_change(
                mean_p30 - mean_p0, mean_p0
            ),
        })
        for name in FLOW_SIGNALS:
            q0 = interval[f"{name}_0"].to_numpy()
            q30 = interval[f"{name}_30"].to_numpy()
            mean_q0, mean_q30 = time_mean(time, q0), time_mean(time, q30)
            row.update({
                f"{name}_mean_0_l_min": mean_q0,
                f"{name}_mean_30_l_min": mean_q30,
                f"{name}_mean_change_percent": percent_change(
                    mean_q30 - mean_q0, mean_q0
                ),
                f"{name}_delta_nrmse_percent": percent_change(
                    np.sqrt(time_mean(time, (q30 - q0)**2)),
                    np.sqrt(time_mean(time, q0**2)),
                ),
            })
        for boom in ANGLE_SIGNALS:
            delta = interval[f"{boom}_angle_delta_rad"].to_numpy()
            row[f"{boom}_angle_pair_rmse_rad"] = float(
                np.sqrt(time_mean(time, delta**2))
            )
            row[f"{boom}_angle_pair_max_absolute_error_rad"] = float(
                np.max(np.abs(delta))
            )
        rows.append(row)
    return pd.DataFrame(rows)


def build_energy_attribution_summary(
    source_dir: Path = COMMITABLE_DATA_DIR,
) -> pd.DataFrame:
    """Build paired 0%/30% attribution for identical payload/R, per motion."""
    rows = []
    for (rfp, payload), pair in tqdm(
        sorted(find_scenario_pairs(source_dir).items()),
        desc="Paired pressure/flow energy attribution", unit="pair",
    ):
        if set(pair) != {0, 30}:
            raise ValueError(f"Incomplete 0%/30% pair: R{rfp}, P{payload}")
        try:
            changes = prepare_energy_attribution(
                load_result(pair[0]), load_result(pair[30])
            )
            summary = summarize_energy_attribution(changes)
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
    summary = build_energy_attribution_summary()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(summary)} paired motion attributions to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

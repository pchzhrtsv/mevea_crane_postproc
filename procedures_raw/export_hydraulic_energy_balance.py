"""Export signed hydraulic energy balances for all commitable_data cases.

Use the full recorded interval and hydraulic powers with spike filtering
(20 samples).
Pressures are in bar, flows in L/min, time in seconds, and energy in kJ.
The filename's R value is exported unchanged as rfp.
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd
from tqdm import tqdm

from utils.paths import COMMITABLE_DATA_DIR, CSV_DIR
from utils.processing import clean_spikes
from utils.result_parser import load_result


OUTPUT_FILE = CSV_DIR / "hydraulic_energy_balance.csv"
CASE_PATTERN = re.compile(r"L(?P<lightweighting>\d+)_P(?P<payload>\d+)_R(?P<rfp>\d+)")
ENERGY_COMPONENTS = {
    "lift_cylinder": "P_hyd_Lift",
    "tilt_cylinder": "P_hyd_Tilt",
    "storage": "P_storage_sum",
    "valve_throttling": "P_DV_sum",
    "residual": "P_gap",
}
REQUIRED_COLUMNS = [
    "Time", "VolPump_p", "Pump_Q",
    "Lift_A_p", "Lift_B_p", "Lift_A_Q", "Lift_B_Q",
    "Lift_DV_QP", "Lift_DV_QA", "Lift_DV_QB",
    "Tilt_A_p", "Tilt_B_p", "Tilt_A_Q", "Tilt_B_Q",
    "Tilt_DV_QP", "Tilt_DV_QA", "Tilt_DV_QB",
]


def calculate_hydraulic_powers(dataset: pd.DataFrame) -> pd.DataFrame:
    """Return filtered hydraulic powers in kW without changing dataset.

    Require finite input values and at least two strictly increasing times.
    Cylinder power includes both chambers. Storage is signed power from
    flow imbalance in the pump line and all four cylinder lines.
    """
    missing = sorted(set(REQUIRED_COLUMNS) - set(dataset.columns))
    if missing:
        raise ValueError(f"Missing input columns: {', '.join(missing)}")
    values = dataset[REQUIRED_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Input contains missing or non-finite values")
    time = dataset["Time"].to_numpy(dtype=float)
    if len(time) < 2 or not np.all(np.diff(time) > 0):
        raise ValueError("Need at least two strictly increasing time samples")

    ds = dataset
    powers = pd.DataFrame({"Time": ds["Time"]})
    p_tank = 1.0

    powers["P_pump"] = (ds.VolPump_p - p_tank) * ds.Pump_Q / 600
    powers["P_hyd_Lift"] = -(
        (ds.Lift_A_p - p_tank) * ds.Lift_A_Q
        + (ds.Lift_B_p - p_tank) * ds.Lift_B_Q
    ) / 600
    powers["P_hyd_Tilt"] = -(
        (ds.Tilt_A_p - p_tank) * ds.Tilt_A_Q
        + (ds.Tilt_B_p - p_tank) * ds.Tilt_B_Q
    ) / 600

    valve_lift = -(
        (ds.VolPump_p - p_tank) * ds.Lift_DV_QP
        + (ds.Lift_A_p - p_tank) * ds.Lift_DV_QA
        + (ds.Lift_B_p - p_tank) * ds.Lift_DV_QB
    ) / 600
    valve_tilt = -(
        (ds.VolPump_p - p_tank) * ds.Tilt_DV_QP
        + (ds.Tilt_A_p - p_tank) * ds.Tilt_DV_QA
        + (ds.Tilt_B_p - p_tank) * ds.Tilt_DV_QB
    ) / 600
    # The reference filters the raw valve sum, not a sum of filtered valves.
    powers["P_DV_sum"] = valve_lift + valve_tilt

    powers["P_storage_Pump"] = (ds.VolPump_p - p_tank) * (
        ds.Pump_Q + ds.Lift_DV_QP + ds.Tilt_DV_QP
    ) / 600
    powers["P_storage_Lift_A"] = (ds.Lift_A_p - p_tank) * (
        ds.Lift_DV_QA + ds.Lift_A_Q
    ) / 600
    powers["P_storage_Lift_B"] = (ds.Lift_B_p - p_tank) * (
        ds.Lift_DV_QB + ds.Lift_B_Q
    ) / 600
    powers["P_storage_Tilt_A"] = (ds.Tilt_A_p - p_tank) * (
        ds.Tilt_DV_QA + ds.Tilt_A_Q
    ) / 600
    powers["P_storage_Tilt_B"] = (ds.Tilt_B_p - p_tank) * (
        ds.Tilt_DV_QB + ds.Tilt_B_Q
    ) / 600

    storage_columns = [
        "P_storage_Pump", "P_storage_Lift_A", "P_storage_Lift_B",
        "P_storage_Tilt_A", "P_storage_Tilt_B",
    ]
    for column in list(powers.columns):
        if column == "Time":
            continue
        clean_spikes(powers, column, key_clean=column, window=20)

    # Sum storage after filtering each line, as in the reference procedure.
    powers["P_storage_sum"] = powers[storage_columns].sum(axis=1)
    powers["P_sum_total"] = (
        powers["P_hyd_Lift"] + powers["P_hyd_Tilt"]
        + powers["P_DV_sum"] + powers["P_storage_sum"]
    )
    powers["P_gap"] = powers["P_pump"] - powers["P_sum_total"]
    if not np.isfinite(powers.to_numpy(dtype=float)).all():
        raise ValueError("Filtering produced missing or non-finite powers")
    return powers


def calculate_energy_balance(dataset: pd.DataFrame) -> dict[str, float]:
    powers = calculate_hydraulic_powers(dataset)

    from procedures_raw.export_hydraulic_energy_balance_by_motion import (
        select_power_interval,
    )

    interval = select_power_interval(powers, 2.5, float(powers["Time"].iloc[-1]))
    return integrate_energy_balance(interval)


def integrate_energy_balance(powers: pd.DataFrame) -> dict[str, float]:
    """Integrate already filtered kW powers over their time interval in seconds.

    Return signed energies in kJ and shares of the interval's pump energy.
    The input is a complete power balance or an interpolated time slice of it;
    no additional filtering is performed here.
    """
    time = powers["Time"].to_numpy()
    pump_energy = float(np.trapezoid(powers["P_pump"], x=time))
    if pump_energy == 0:
        raise ValueError("Pump energy is zero; percentage shares are undefined")

    result = {"pump_energy_kj": pump_energy}
    for component, column in ENERGY_COMPONENTS.items():
        energy = float(np.trapezoid(powers[column], x=time))
        result[f"{component}_energy_kj"] = energy
        result[f"{component}_share_percent"] = 100 * energy / pump_energy
    return result


def build_energy_summary(source_dir: Path = COMMITABLE_DATA_DIR) -> pd.DataFrame:
    """Read L<percent>_P<kg>_R<code>.txt files one at a time.

    Return one row per input file, sorted by lightweighting, rfp, and payload.
    Filename parameters are preserved; rfp is not rescaled.
    """
    files = sorted(Path(source_dir).glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No simulation TXT files found in {source_dir}")

    rows = []
    for file_path in tqdm(files, desc="Hydraulic energy balance", unit="case"):
        match = CASE_PATTERN.fullmatch(file_path.stem)
        if match is None:
            raise ValueError(f"Unexpected dataset filename: {file_path.name}")
        parameters = {
            "lightweighting_percent": int(match["lightweighting"]),
            "rfp": int(match["rfp"]),
            "payload_kg": int(match["payload"]),
        }
        try:
            energy = calculate_energy_balance(load_result(file_path))
        except (ValueError, KeyError) as error:
            raise ValueError(f"{file_path.name}: {error}") from error
        rows.append({**parameters, **energy})

    return pd.DataFrame(rows).sort_values(
        ["lightweighting_percent", "rfp", "payload_kg"], ignore_index=True
    )


def main():
    summary = build_energy_summary()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(summary)} cases to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

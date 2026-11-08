"""Export hydraulic energy balances for four motions of every source case.

    Motion 1: 2.5--8.5 s; motion 2: 8.5--15 s;
    motion 3: 15--21 s; motion 4: 21 s through the last recorded sample.

Filter full-record powers once, using export_hydraulic_energy_balance, then
integrate each motion with exact, linearly interpolated boundary values.
Energy and percentages keep their signs. Percentages use each motion's
own pump energy; the filename's R code is exported unchanged.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from procedures_raw.export_hydraulic_energy_balance import (
    CASE_PATTERN,
    calculate_hydraulic_powers,
    integrate_energy_balance,
)
from utils.paths import COMMITABLE_DATA_DIR, CSV_DIR
from utils.processing import align_to_reference
from utils.result_parser import load_result


OUTPUT_FILE = CSV_DIR / "hydraulic_energy_balance_by_motion.csv"
MOTIONS = (
    (1, 2.5, 8.5),
    (2, 8.5, 15.0),
    (3, 15.0, 21.0),
    (4, 21.0, None),
)


def select_power_interval(
    powers: pd.DataFrame, start_time: float, end_time: float
) -> pd.DataFrame:
    """Select a recorded interval, adding interpolated boundary powers.

    Require finite boundaries, positive duration, and full coverage by powers.
    Keep original interior samples without re-filtering or extrapolation.
    Shared boundaries preserve additivity of trapezoidal energy integrals.
    """
    time = powers["Time"].to_numpy(dtype=float)
    if not np.isfinite([start_time, end_time]).all() or end_time <= start_time:
        raise ValueError("Motion boundaries must be finite and increasing")
    if start_time < time[0] or end_time > time[-1]:
        raise ValueError(
            f"Motion interval {start_time}..{end_time} s is outside "
            f"the recorded interval {time[0]}..{time[-1]} s"
        )
    interval_time = np.concatenate([
        [start_time], time[(time > start_time) & (time < end_time)], [end_time],
    ])
    return align_to_reference(pd.DataFrame({"Time": interval_time}), powers)


def calculate_motion_energy_balances(dataset: pd.DataFrame) -> pd.DataFrame:
    """Return four motion balances for a source dataset without modifying it.

    Use the existing full-record filtering and signed-energy formulas.
    Include exact interval bounds in seconds and shares of each motion's pump.
    """
    powers = calculate_hydraulic_powers(dataset)
    last_time = float(powers["Time"].iloc[-1])
    rows = []
    for motion, start_time, end_time in MOTIONS:
        end_time = last_time if end_time is None else end_time
        try:
            interval = select_power_interval(powers, start_time, end_time)
            balance = integrate_energy_balance(interval)
        except ValueError as error:
            raise ValueError(f"Motion {motion}: {error}") from error
        rows.append({
            "motion": motion,
            "start_time_s": start_time,
            "end_time_s": end_time,
            **balance,
        })
    return pd.DataFrame(rows)


def build_motion_energy_summary(
    source_dir: Path = COMMITABLE_DATA_DIR,
) -> pd.DataFrame:
    """Read each L<percent>_P<kg>_R<code>.txt and return four rows per case."""
    files = sorted(Path(source_dir).glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No simulation TXT files found in {source_dir}")

    rows = []
    for file_path in tqdm(files, desc="Hydraulic energy by motion", unit="case"):
        match = CASE_PATTERN.fullmatch(file_path.stem)
        if match is None:
            raise ValueError(f"Unexpected dataset filename: {file_path.name}")
        parameters = {
            "lightweighting_percent": int(match["lightweighting"]),
            "rfp": int(match["rfp"]),
            "payload_kg": int(match["payload"]),
        }
        try:
            balances = calculate_motion_energy_balances(load_result(file_path))
        except (ValueError, KeyError) as error:
            raise ValueError(f"{file_path.name}: {error}") from error
        rows.extend(
            {**parameters, **balance}
            for balance in balances.to_dict(orient="records")
        )

    return pd.DataFrame(rows).sort_values(
        ["lightweighting_percent", "rfp", "payload_kg", "motion"],
        ignore_index=True,
    )


def main():
    summary = build_motion_energy_summary()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(summary)} motion balances to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

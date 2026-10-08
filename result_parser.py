from pathlib import Path
import re
import pandas as pd
from tqdm import tqdm
import time

def load_result(file_path: Path, sep="\t") -> pd.DataFrame:
    return pd.read_csv(
        file_path,
        sep=sep,
    )

def digits(x): return int(re.sub(r"\D", "", x))

def load_all_results(directory: Path) -> dict:
    datasets = {}

    for file_path in directory.glob("*.txt"):

        # lightening, payload, reference = map(
        #     str,
        #     file_path.stem.split("_"),
        # )

        loc_args = tuple(map(str, file_path.stem.split("_"),))

        datasets[tuple([digits(loc_arg) for loc_arg in loc_args])] = load_result(file_path)
    if datasets.keys():
        print(f"{len(datasets.keys())} datasets loaded")
    return datasets

def load_masked_results(directory: Path, case_mask: tuple) -> dict:
    datasets = {}

    for file_path in directory.glob("*.txt"):
        loc_args = tuple(map(str, file_path.stem.split("_"),))
        loc_args = tuple([digits(loc_arg) for loc_arg in loc_args])
        if case_mask[0] in (loc_args[0], None) and case_mask[1] in (loc_args[1], None):
            datasets[loc_args] = load_result(file_path)
    return datasets

def load_specific_results(directory: Path, cases: list) -> dict:
    datasets = {}
    total_cases = len(cases)
    with tqdm(total=total_cases, desc="Dataframes loading", unit="df") as pbar:
        for file_path in directory.glob("*.txt"):
            loc_args = tuple(map(str, file_path.stem.split("_"),))
            loc_args = tuple([digits(loc_arg) for loc_arg in loc_args])
            if loc_args in cases:
                datasets[loc_args] = load_result(file_path)
                pbar.update(1)
    return datasets

def load_ref_thetas(directory: Path) -> dict:
    lift_theta_ds = None
    tilt_theta_ds = None
    for file_path in directory.glob("*.txt"):
        if "z1" in file_path.stem:
            lift_theta_ds = load_result(file_path, sep=" ")
        elif "z4" in file_path.stem:
            tilt_theta_ds = load_result(file_path, sep=" ")
        else:
            raise ValueError("Theta reference file not recognized")
    return lift_theta_ds, tilt_theta_ds

def load_ref_u(directory: Path) -> dict:
    lift_u_ds = None
    tilt_u_ds = None
    for file_path in directory.glob("*.txt"):
        if "UL" in file_path.stem:
            lift_u_ds = load_result(file_path, sep=" ")
        elif "UT" in file_path.stem:
            tilt_u_ds = load_result(file_path, sep=" ")
        else:
            raise ValueError("Theta reference file not recognized")
    return lift_u_ds, tilt_u_ds
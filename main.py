from pathlib import Path
import numpy as np
from data_import import import_results
from result_parser import load_all_results, load_ref_thetas, load_masked_results
from plotting import plot_variables, plot_series, plot_smthng
from processing import *
import matplotlib.pyplot as plt
# import pandas as pd
from plot_blocks import pump_power_on_ref_pressure, light_impact_consumption_on_ref_pressure, pos_rms_on_ref_pressure, \
    consumption_on_lightweight, power_plots, booms_positions, pressure_plots

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = (PROJECT_ROOT.parent / "Mevea-frontend")
SOURCE_DIR = (FRONTEND_ROOT / "rawdata")
RAWDATA_DIR = (PROJECT_ROOT / "rawdata")
POSTDATA_DIR = (PROJECT_ROOT / "postdata")
REFPRESS_DIR = (PROJECT_ROOT / "ref_pressure_dataset")
TESTDATA_DIR = (PROJECT_ROOT / "test_data")
REFTHETA_DIR = (PROJECT_ROOT / "target_thetas")

WORK_DIR = (PROJECT_ROOT / f"tempo_test")

def main():
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"

    #import_results(source_dir=SOURCE_DIR, target_dir=WORK_DIR)

    #raw_datasets = load_all_results(RAWDATA_DIR)
    # ref_datasets = load_all_results(REFPRESS_DIR)
    # lift_theta_ds, tilt_theta_ds = load_ref_thetas(REFTHETA_DIR)
    # thetas_ds = realign_thetas(lift_theta_ds, tilt_theta_ds)


    r1 = load_all_results(PROJECT_ROOT / "rawdata_1")
    r2 = load_all_results(PROJECT_ROOT / "rawdata_2")
    r3 = load_all_results(PROJECT_ROOT / "rawdata_3")
    power_plots(r1, cases=[(0,400,35),(30,400,35)])
    power_plots(r2, cases=[(0,400,35),(30,400,35)])
    power_plots(r3, cases=[(0,400,35),(30,400,35)])
    # ref = load_all_results(REFPRESS_DIR)
    # power_plots(ref, cases=[(0, 400, 35), (30, 400, 35)])
    some_datasets = dict()
    global_case_masks = [(y, x, 35) for x in [400] for y in [0,30]]
    for x in global_case_masks:
        some_datasets.update(load_masked_results(RAWDATA_DIR, x))

    cutted_datasets = start_from(some_datasets, 2.4)
    power_plots(cutted_datasets, cases=[(0,400,35),(30,400,35)])
    # consumption_on_lightweight(cutted_datasets, global_case_masks, relative=True)
    # cutted_datasets = start_from(ref_datasets, 2.4)
    # power_plots(cutted_datasets, cases=[(0,10,10),(30,10,10),(0,400,10),(30,400,10)],colors=[(1.,0.,0.,0.5), (1.,0.,0.), (0.,0.0,1.,0.5), (0.,0.0,1.),])

    #power_plots(cutted_datasets, cases=cases, colors=[(1.,0.,0.,0.5), (0.,1.0,0.,0.5), (0.,0.,1.,0.5), (1.,0.,0.), (0.,1.0,0.), (0.,0.,1.),])
    #pressure_plots(cutted_datasets, cases, cylinder="Tilt", colors=[(1.,0.,0.,0.5), (0.,1.0,0.,0.5), (0.,0.,1.,0.5), (1.,0.,0.), (0.,1.0,0.), (0.,0.,1.),])
    #booms_positions(cutted_datasets, cases=cases, thetas_ds=thetas_ds)
    #power_plots(cutted_datasets, cases=[(x, y, 35) for x in [0, 30] for y in [10,400]])

    # light_impact_consumption_on_ref_pressure(cutted_datasets, [(None,10,None),(None,400,None)], relative=True)

    # pos_rms_on_ref_pressure(cutted_datasets, thetas_ds, [(0, 10, None), (30, 10, None), (0, 400, None), (30, 400, None)])

    consumption_on_lightweight(cutted_datasets, [(None, x, 35) for x in [380,390,400]], relative=True)

if __name__ == "__main__":
    main()
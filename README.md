# Mevea simulation post-processing

Independent Python scripts for analyzing Lift and Tilt hydraulic simulations, comparing them with reference data, and generating CSV tables and figures.

## Directories

| Directory | Contents |
| --- | --- |
| `procedures_raw/` | Analysis, plotting, and CSV export from source data. |
| `procedures_csv/` | Plots generated from processed CSV tables. |
| `utils/` | Shared paths, data loaders, processing, and plotting functions. |
| `commitable_data/` | Included simulation cases and the default source for `DATA_DIR`. |
| `rawdata/` | Full simulation dataset used by the raw pump-energy heatmap. |
| `refpress_data/` | Simulation cases for the reference-pressure sweeps. |
| `powerbalance_data/` | Simulation exports for the hydraulic power balance. |
| `exp_pressures/` | Experimental pressure measurements and the validation simulation. |
| `target_thetas/`, `target_u/` | Reference angle trajectories and valve control signals. |
| `csv_files/`, `figures/` | Output directories for CSV tables and figures. |
| `postdata/` | Additional processed data. |

**`rawdata/` and `refpress_data/` are excluded from the repository. Request these datasets separately from the developer and place them in the project root.** Input and output paths are defined in [`utils/paths.py`](utils/paths.py).

## Run a procedure

Use Python **3.13.5**, the version configured for this project in PyCharm. From the project root, run the following in that environment. `requirements.txt` pins the direct dependencies to the versions installed in the project environment.

```shell
python -m pip install -r requirements.txt
python -m procedures_raw.plot_model_vs_experiment
```

## Procedures using source data

| Procedure in `procedures_raw/` | Purpose |
| --- | --- |
| `export_boom_angle_error_metrics.py` | Exports Lift and Tilt angle errors for each scenario. |
| `export_hydraulic_energy_balance.py` | Exports the hydraulic energy balance for each scenario. |
| `export_hydraulic_energy_balance_by_motion.py` | Exports the hydraulic energy balance for each motion. |
| `export_lightweighting_energy_attribution.py` | Quantifies pressure and flow contributions to pump energy changes between paired 0% and 30% lightweighting cases. |
| `export_lightweighting_flow_power_correlations.py` | Correlates flow changes with pump power changes between paired 0% and 30% lightweighting cases. |
| `export_model_validation_metrics.py` | Exports model validation errors for boom angles and chamber pressures. |
| `export_valve_flow_energy_by_motion.py` | Exports valve supply flow deviations and pressure and flow contributions to energy changes by motion. |
| `plot_boom_angle_rmse_by_pressure.py` | Computes and plots boom angle RMSE across reference pressures using `refpress_data/`. |
| `plot_boom_angle_scenarios.py` | Compares Lift and Tilt angle trajectories against the reference for selected scenarios. |
| `plot_chamber_pressure_by_motion.py` | Summarizes chamber pressures and identifies the leading load-sensing chamber by motion. |
| `plot_model_experiment_angle_difference.py` | Plots differences between simulated and experimental boom angles. |
| `plot_model_vs_experiment.py` | Compares simulated and experimental boom angles and chamber pressures. |
| `plot_power_balance_hydraulic.py` | Computes and plots the hydraulic power balance using `powerbalance_data/`. |
| `plot_pump_energy_change_by_motion.py` | Plots the change in pump energy by motion. |
| `plot_pump_energy_change_by_pressure.py` | Computes and plots pump energy changes across reference pressures using `refpress_data/`. |
| `plot_pump_energy_change_heatmap.py` | Computes and plots pump energy changes across payload and lightweighting levels using `rawdata/`. |
| `plot_pump_power_change.py` | Plots the change in pump power due to lightweighting. |
| `plot_reference_angles_and_control.py` | Plots the reference angles and valve control signals. |
| `plot_valve_control_deviation_rms.py` | Summarizes valve control deviations, including RMS. |
| `plot_valve_control_signals.py` | Compares valve control signals against their references. |
| `plot_valve_supply_flows.py` | Compares Lift and Tilt valve supply flows against the validation reference. |

## Procedures using CSV tables

| Procedure in `procedures_csv/` | Purpose |
| --- | --- |
| `plot_boom_angle_rmse_by_pressure.py` | Plots boom angle RMSE across reference pressures. |
| `plot_pump_energy_change_by_pressure.py` | Plots pump energy changes across reference pressures. |
| `plot_pump_energy_change_heatmap.py` | Plots pump energy changes across payload and lightweighting levels. |

import pandas as pd
import numpy as np
from fontTools.misc.plistlib import totree
from matplotlib.font_manager import list_fonts

from processing import *
from plotting import *
import matplotlib.pyplot as plt

def pump_power_on_ref_pressure(dss,  lgt=None, pld=None, rfp=None):

    cases = list(dss.keys())
    if lgt is not None:
        cases = [case for case in cases if case[0] == lgt]
    if pld is not None:
        cases = [case for case in cases if case[1] == pld]
    if rfp is not None:
        cases = [case for case in cases if case[2] == rfp]


    pump_consumption_ds = pd.DataFrame()
    ds_ref = dss[cases[0]]
    pump_consumption_ds["Time"] = ds_ref["Time"]
    for ds_id in cases:
        aligned_ds = align_to_reference(ds_ref, dss[ds_id])
        aligned_ds = clean_spikes(aligned_ds, "Pump_P", key_clean = "Pump_P_clean", window = 20)
        pump_consumption_ds[f"Lightening {ds_id[0]} %; Payload {ds_id[1]} kg; Ref.pressure {ds_id[2]} bar"] = aligned_ds["Pump_P_clean"]
    plot_series(pump_consumption_ds, pump_consumption_ds.columns.drop("Time").tolist(), ylabel="P, kW", title = "Pump power")

def pos_rms_on_ref_pressure(dss, ds_ref, cases):
    plt.figure(figsize=(16.5, 10.8))
    dss = adjust_cases_id(dss)
    for case in cases:
        pos_rms_on_ref_pressure_single(dss, ds_ref, case)
    plt.show()

def pos_rms_on_ref_pressure_single(dss, ds_ref, arg_case):
    lgt = None
    pld = None
    if arg_case is not None:
        lgt = arg_case[0]
        pld = arg_case[1]
    cases = list(dss.keys())
    if lgt is not None:
        cases = [case for case in cases if case[0] == lgt]
    if pld is not None:
        cases = [case for case in cases if case[1] == pld]
    # if rfp is not None:
    #     cases = [case for case in cases if case[2] == rfp]

    #rms_ds = pd.DataFrame()
    #ds_ref = dss[cases[0]]
    #rms_ds["Time"] = ds_ref["Time"]

    unsrt_rmss = list()

    for ds_id in cases:
        ds_real = dss[ds_id]
        aligned_ds = align_to_reference(ds_ref, ds_real)


        lift_rmse = np.sqrt(np.mean((aligned_ds["Lift_theta"] - ds_ref["Lift_theta"]) ** 2))

        tilt_rmse = np.sqrt(np.mean((aligned_ds["Tilt_theta"] - ds_ref["Tilt_theta"]) ** 2))

        combined_rmse = np.sqrt(lift_rmse ** 2 + tilt_rmse ** 2)
        unsrt_rmss.append((ds_id[2],combined_rmse))

    ref_presses = [rms[0] for rms in sorted(unsrt_rmss)]
    rmss = [rms[1] for rms in sorted(unsrt_rmss)]

    ylabel = r"RMSE, rad"
    title = f"RMS angular boom position error"
    total_power_ds = pd.DataFrame()
    total_power_ds[f"{lgt}% lightening, {pld}kg payload"] = rmss
    total_power_ds["Reference pressure, bar"] = ref_presses
    plot_smthng(total_power_ds, "Reference pressure, bar", [f"{lgt}% lightening, {pld}kg payload"], title = title, ylabel=ylabel, singleshot=False)


def light_impact_consumption_on_ref_pressure(dss, cases, relative=False):
    plt.figure(figsize=(16.5, 10.8))
    dss = adjust_cases_id(dss)
    for case in cases:
        light_impact_consumption_on_ref_pressure_single(dss, case, relative)
    plt.show()

def light_impact_consumption_on_ref_pressure_single(dss, arg_case, relative=False):

    '''
    case[0] - lightening
    case[1] - payload
    case[2] - ref.pressure
    '''
    pld = arg_case[1]
    cases = list(dss.keys())
    max_lgt = np.max([case[0] for case in cases])
    min_lgt = np.min([case[0] for case in cases])

    if pld is not None:
        cases = [case for case in cases if case[1] == pld]

    minuend_cases = [case for case in cases if case[0] == max_lgt]
    subtrahend_cases = [case for case in cases if case[0] == min_lgt]

    power_ds = pd.DataFrame()
    ref_id = (np.min([case[0] for case in cases]), np.min([case[1] for case in cases]), np.min([case[2] for case in cases]))
    ds_ref = dss[ref_id]
    power_ds["Time"] = ds_ref["Time"]

    unsrt_energy= list()

    for ds_id_min in minuend_cases:
        ds_id_sub = (min_lgt, ds_id_min[1], ds_id_min[2] )
        if ds_id_sub in subtrahend_cases:
            aligned_minuend = align_to_reference(ds_ref, dss[ds_id_min])
            aligned_subtrahend = align_to_reference(ds_ref, dss[ds_id_sub])

            ds_case_label = f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar"
            ds_case_label_divisor = f"Payload {ds_id_sub[1]} kg; Ref.pressure {ds_id_sub[2]} bar, div"
            power_ds[ds_case_label] = (aligned_minuend["Pump_P"] - aligned_subtrahend["Pump_P"])
            power_ds[ds_case_label_divisor] = aligned_subtrahend["Pump_P"]

            if relative:
                seria = power_ds[f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar"]
                seria_div = power_ds[f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar, div"]
                unsrt_energy.append((ds_id_min[2], np.trapezoid(seria, x=power_ds["Time"])/np.trapezoid(seria_div, x=power_ds["Time"])*100))
            else:
                seria = power_ds[f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar"]
                unsrt_energy.append((ds_id_min[2],np.trapezoid(seria, x=power_ds["Time"])))


    ref_presses = [rms[0] for rms in sorted(unsrt_energy)]
    energy = [rms[1] for rms in sorted(unsrt_energy)]

    # key_list = power_ds.columns.drop("Time").tolist()
    # key_list.sort(key=lambda x: x != f"Payload {ref_id[1]} kg; Ref.pressure {ref_id[2]} bar")
    #
    # ref_presses = list(set([case[2] for case in cases]))
    # ref_presses.sort()

    # energy = list()
    #
    # for rp in ref_presses:
    #     for ds_id_min in [case for case in minuend_cases if case[2] == rp]:
    #         if relative:
    #             seria = power_ds[f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar"]
    #             seria_div = power_ds[f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar, div"]
    #             energy.append(np.trapezoid(seria, x=power_ds["Time"])/np.trapezoid(seria_div, x=power_ds["Time"])*100)
    #         else:
    #             seria = power_ds[f"Payload {ds_id_min[1]} kg; Ref.pressure {ds_id_min[2]} bar"]
    #             energy.append(np.trapezoid(seria, x=power_ds["Time"]))

    ylabel = r"$\frac{W_{30\%}-W_{0\%}}{W_{0\%}}$,  %" if relative else r"$W_{0\%}-W_{30\%}$, kJ"
    title = f"Relative reduction of energy consumption for 30% and 0% lightening cases, payload = {pld}kg" if relative else f"Energy consumption difference between 30% and 0% lightening cases, payload = {pld}kg"
    total_power_ds = pd.DataFrame()
    total_power_ds[f"{pld}kg payload"] = energy
    total_power_ds["Reference pressure, bar"] = ref_presses
    plot_smthng(total_power_ds, "Reference pressure, bar", [f"{pld}kg payload"], title = title, ylabel=ylabel, singleshot=False)

def consumption_on_lightweight(dss, case_masks, relative=False):
    total_ds = pd.DataFrame()
    plt.figure(figsize=(16.5, 10.8))
    dss = adjust_cases_id(dss)
    i=1
    for case_mask in case_masks:
        total_ds = consumption_on_lightweight_single(dss, case_mask, total_ds, relative)
        print(f"Processing: {i}/{len(case_masks)}.")
        i+=1
    total_ds.to_csv("consumption_on_lightweight_35bar.csv", index=False)
    # plt.show()

def consumption_on_lightweight_single(dss, case_mask, total_ds, relative=True):

    global_cases = list(dss.keys())
    local_cases = [case for case in global_cases if
                   case_mask[0] in (case[0], None) and case_mask[1] in (case[1], None) and case_mask[2] in (case[2],
                                                                                                       None)]

    ref_id = (np.min([case[0] for case in local_cases]), np.min([case[1] for case in local_cases]), np.min([case[2] for case in local_cases]))
    zero = ref_id[0]
    zero_setup = (zero, case_mask[1], case_mask[2])
    ds_ref = dss[ref_id]

    unsrt_pairs = list()

    for ds_id_min in local_cases:
        aligned_minuend = align_to_reference(ds_ref, dss[ds_id_min])
        aligned_subtrahend = align_to_reference(ds_ref, dss[zero_setup])

        divident = (pump_work(aligned_minuend) - pump_work(aligned_subtrahend))
        divisor = pump_work(aligned_subtrahend)

        unsrt_x = ds_id_min[0]
        unsrt_y = divident/divisor*100 if relative else divident
        unsrt_pairs.append((unsrt_x, unsrt_y))

    x = [sol[0] for sol in sorted(unsrt_pairs)]
    y = [sol[1] for sol in sorted(unsrt_pairs)]

    ylabel = r"$\frac{\Delta{W}}{W_{0\%}}$,  %" if relative else r"$W_{x\%}-W_{0\%}$, kJ"
    title = f"Relative reduction of energy consumption for x% and 0% lightening cases" if relative else f"Energy consumption difference between x% and 0% lightening cases"
    total_ds[f"{case_mask[1]} kg ; {case_mask[2]} bar"] = y
    total_ds["Lightening, %"] = x
    plot_smthng(total_ds, "Lightening, %", [f"{case_mask[1]} kg ; {case_mask[2]} bar"], title = title, ylabel=ylabel, singleshot=False)
    return total_ds

def power_plots(dss, cases, styles=None, colors=None):
    dss = adjust_cases_id(dss)
    #plt.figure(figsize=(16.5, 10.8))
    cds_pp = pd.DataFrame()
    ref_case = cases[0]
    ref_ds = dss[ref_case]
    cds_pp["Time"] = ref_ds.Time
    for case in cases:
        if case != ref_case:
            dss[case] = align_to_reference(dss[ref_case], dss[case])
        cds_pp[case] = pump_power(dss[case])
        cds_pp = clean_spikes(cds_pp, case, key_clean=case, window=20)
    if not styles:
        styles = ["--" if x[0]==0 else "-" for x in cases]
    plot_smthng(cds_pp, "Time", cases, loc_labels=[f"{x[0]}%, {x[1]}kg, {x[2] if x[2] else 35}bar" for x in cases], title = r"$P = Q_{\mathrm{pump}}(t)\cdot(p_{\mathrm{pump}}(t)-p_{\mathrm{tank}})$", ylabel="P, kW", singleshot=True, styles=styles, colors=colors)

def pressure_plots(dss, cases, colors=None, styles=None, cylinder="Lift"):
    dss = adjust_cases_id(dss)
    plt.figure(figsize=(16.5, 10.8))
    cds_pA = pd.DataFrame()
    cds_pB = pd.DataFrame()
    ref_case = cases[0]
    ref_ds = dss[ref_case]
    cds_pA["Time"] = ref_ds.Time
    cds_pB["Time"] = ref_ds.Time
    for case in cases:
        if case != ref_case:
            dss[case] = align_to_reference(dss[ref_case], dss[case])
        cds_pA[case] = dss[case][f"{cylinder}_A_p"]
        cds_pB[case] = dss[case][f"{cylinder}_B_p"]
        cds_pA = clean_spikes(cds_pA, case, key_clean=case, window=20)
        cds_pB = clean_spikes(cds_pB, case, key_clean=case, window=20)
    if not styles:
        styles = ["--" if x[0]==0 else "-" for x in cases]
    plot_smthng(cds_pA, "Time", cases, loc_labels=[f"{x[0]}%, {x[1]}kg, {x[2] if x[2] else 35}bar, A chamber" for x in cases], title=f"Pressure in {cylinder} cylinder chambers", ylabel="p, bar", singleshot=False, styles=styles, colors=colors)
    plot_smthng(cds_pB, "Time", cases, loc_labels=[f"{x[0]}%, {x[1]}kg, {x[2] if x[2] else 35}bar, B chamber" for x in cases], title = f"Pressure in {cylinder} cylinder chambers", ylabel="p, bar", singleshot=True, styles=styles, colors=colors)


def booms_positions(datasets,cases, thetas_ds):
    for case in cases:
        plt.figure(figsize=(16.5, 10.8))
        cds = datasets[case]

        plot_smthng(cds, "Time", ["Lift_theta"], loc_labels=[f"Lift boom; case {case}"],
                    singleshot=False)
        plot_smthng(thetas_ds, "Time", ["Lift_theta"], loc_labels=["Lift boom; target position"], singleshot=False,
                    styles=["--"])
        plot_smthng(cds, "Time", ["Tilt_theta"], loc_labels=[f"Tilt boom; case {case}"],
                    singleshot=False)
        plot_smthng(thetas_ds, "Time", ["Tilt_theta"], loc_labels=["Tilt boom; target position"], singleshot=False,
                    styles=["--"])
        plt.xlabel("Time, s")
        plt.ylabel(r"$\Theta$, rad")
        plt.show()

def adjust_cases_id(dss):

    cases = list(dss.keys())

    min_case_len = np.min([len(case) for case in cases])

    if min_case_len <2:
        raise ValueError("Not enough case args to plot")
    if min_case_len == 2:
        old_cases = cases
        cases = [(case[0], case[1], 35) for case in old_cases]
        for case in cases:
            dss[case] = dss.pop((case[0], case[1]))
    return dss

    lgts = [case[0] for case in arg_cases]
    plds = [case[1] for case in arg_cases]
    rfps = [case[2] for case in arg_cases]

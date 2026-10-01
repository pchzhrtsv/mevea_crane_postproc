import pandas as pd
import numpy as np


def align_to_reference(reference: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    if "Time" not in reference.columns:
        raise KeyError("'Time' not found in reference")
    if "Time" not in target.columns:
        raise KeyError("'Time' not found in target")
    result = pd.DataFrame({"Time": reference["Time"].to_numpy()})
    target_time = target["Time"].to_numpy()
    reference_time = reference["Time"].to_numpy()
    for column in target.columns:
        if column == "Time":
            continue
        result[column] = np.interp(reference_time, target_time, target[column].to_numpy())
    return result

def realign_thetas(lift_theta_ds, tilt_theta_ds, time_step=0.001):
    output_ds = pd.DataFrame()
    output_ds["Time"] = np.arange(0, 30, time_step)
    output_ds["Lift_theta"] = align_to_reference(output_ds, lift_theta_ds)["Lift_theta"]
    output_ds["Tilt_theta"] = align_to_reference(output_ds, tilt_theta_ds)["Tilt_theta"]
    return output_ds

def cylinders_pump_power(df: pd.DataFrame) -> tuple[float, float]:
    power_lift_flowin_A = np.heaviside(df["Lift_U"],0)
    power_lift_flowin_B = np.heaviside(-df["Lift_U"], 0)
    power_tilt_flowin_A = np.heaviside(df["Tilt_U"],0)
    power_tilt_flowin_B = np.heaviside(-df["Tilt_U"], 0)
    lift_p  = -(df["Lift_A_p"] * df["Lift_A_Q"]*power_lift_flowin_A + df["Lift_B_p"] * df["Lift_B_Q"]*power_lift_flowin_B)*1e5 /6e4
    tilt_p = -(df["Tilt_A_p"] * df["Tilt_A_Q"]*power_tilt_flowin_A + df["Tilt_B_p"] * df["Tilt_B_Q"]*power_tilt_flowin_B)*1e5 /6e4
    return df


def cylinders_pump_work(df: pd.DataFrame) -> tuple[float, float]:
    power_lift, power_tilt = cylinders_pump_power(df)
    lift_w = np.trapezoid(power_lift, x=df["Time"])
    tilt_w = np.trapezoid(power_tilt, x=df["Time"])
    return lift_w, tilt_w

def leak_loss(df: pd.DataFrame) -> float:
    normal_coef_lift = 0.4
    normal_coef_tilt = 0.7

    lift_close_sign =  (df["Lift_U"]< 1e-2) & ((-df["Lift_U"])< 1e-2)
    tilt_close_sign = (df["Tilt_U"] < 1e-2) & ((-df["Tilt_U"]) < 1e-2)
    lift_A_leak_q = normal_coef_lift * np.sqrt((df["Lift_A_p"]-1) * lift_close_sign*1e5/1e7)
    lift_B_leak_q = normal_coef_lift * np.sqrt((df["Lift_B_p"]-1) * lift_close_sign*1e5/1e7)
    tilt_A_leak_q = normal_coef_tilt * np.sqrt((df["Tilt_A_p"]-1) * tilt_close_sign*1e5/1e7)
    tilt_B_leak_q = normal_coef_tilt * np.sqrt((df["Tilt_B_p"]-1) * tilt_close_sign*1e5/1e7)


    leak_lift = lift_A_leak_q+lift_B_leak_q
    leak_tilt = tilt_A_leak_q+tilt_B_leak_q
    print(np.trapezoid(leak_lift, x=df["Time"]))
    print(np.trapezoid(leak_tilt, x=df["Time"]))
    print(np.trapezoid(df["Lift_DV_QT"]*lift_close_sign, x=df["Time"]))
    print(np.trapezoid(df["Tilt_DV_QT"]*tilt_close_sign, x=df["Time"]))

    lift_loss = lift_A_leak_q*(df["Lift_A_p"]-1)*1e5/6e4 + lift_B_leak_q*(df["Lift_B_p"]-1)*1e5/6e4
    tilt_loss = tilt_A_leak_q*(df["Tilt_A_p"]-1)*1e5/6e4 + tilt_B_leak_q*(df["Tilt_B_p"]-1)*1e5/6e4
    Leak_loss = lift_loss + tilt_loss
    #plot_series(time=df["Time"], series=Leak_loss)

    return np.trapezoid(Leak_loss, x=df["Time"])

def hydraulic_pump_work_constpress(df: pd.DataFrame, press = 139e5) -> float:
    power_pump = (df["Lift_DV_QP"]) + (df["Tilt_DV_QP"])* press / 6e4
    work_pump = np.trapezoid(power_pump, x=df["Time"])
    return work_pump

def pump_power(df: pd.DataFrame):
    return df["Pump_Q"]*(df["VolPump_p"]-1)*1e5/6e4/1e3

def pump_work(df: pd.DataFrame) -> float:
    return np.trapezoid(pump_power(df), x=df["Time"])

def aux_pump_work(df: pd.DataFrame) -> float:
    return np.trapezoid(df["Pump_P"], x=df["Time"])


def clean_spikes(df, key, key_clean = "value_clean", window = 10):
    s = df[key]
    median = s.rolling(window=window, center=True).median()
    diff = (s - median).abs()
    mad = diff.rolling(window=window, center=True).median()
    mask = diff > 3 * mad
    df[key_clean] = s.mask(mask)
    df[key_clean] = df[key_clean].interpolate()
    return df

def smooth_series(df, key, key_smooth = "value_smooth", window=10):
    s = df[key]
    s_smooth = s.rolling(window=window, center=True, min_periods=1).mean()
    df[key_smooth] = s_smooth
    return df

def start_from(dss, time):
    for df in dss.keys():
        df_inst = dss[df]
        dss[df] = df_inst[df_inst["Time"] >= time].reset_index(drop=True)
    return dss
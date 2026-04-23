import numpy as np
import pandas as pd

# Settings
sampling_rate = 1000  # Hz
duration = 5          # seconds
n = sampling_rate * duration  # 5000 samples
t = np.linspace(0, duration, n, endpoint=False)

# Signals with embedded frequencies
cylinder_pressure = (
    60 + 
    10 * np.sin(2 * np.pi * 50 * t) +   # 50 Hz
    5  * np.sin(2 * np.pi * 100 * t) +   # 100 Hz harmonic
    np.random.normal(0, 0.5, n)
)

brake_power = (
    47 +
    3 * np.sin(2 * np.pi * 20 * t) +     # 20 Hz
    np.random.normal(0, 0.2, n)
)

air_fuel_ratio = (
    14.5 +
    0.5 * np.sin(2 * np.pi * 30 * t) +   # 30 Hz
    np.random.normal(0, 0.05, n)
)

boost_pressure = (
    2.0 +
    0.3 * np.sin(2 * np.pi * 60 * t) +   # 60 Hz
    np.random.normal(0, 0.02, n)
)

exhaust_temp = (
    520 +
    20 * np.sin(2 * np.pi * 10 * t) +    # 10 Hz
    np.random.normal(0, 1.0, n)
)

rpm = (
    2200 +
    50 * np.sin(2 * np.pi * 25 * t) +    # 25 Hz
    np.random.normal(0, 2.0, n)
)

injection_timing = (
    12 +
    1 * np.sin(2 * np.pi * 50 * t) +     # 50 Hz
    np.random.normal(0, 0.05, n)
)

vibration = (
    0.5 * np.sin(2 * np.pi * 50 * t) +   # 50 Hz
    0.3 * np.sin(2 * np.pi * 120 * t) +  # 120 Hz
    0.2 * np.sin(2 * np.pi * 300 * t) +  # 300 Hz
    np.random.normal(0, 0.05, n)
)

# Build dataframe
df = pd.DataFrame({
    "time":              np.round(t, 6),
    "cylinder_pressure": np.round(cylinder_pressure, 4),
    "brake_power":       np.round(brake_power, 4),
    "air_fuel_ratio":    np.round(air_fuel_ratio, 4),
    "boost_pressure":    np.round(boost_pressure, 4),
    "exhaust_temp":      np.round(exhaust_temp, 4),
    "rpm":               np.round(rpm, 4),
    "injection_timing":  np.round(injection_timing, 4),
    "vibration":         np.round(vibration, 4),
})

df.to_csv("Model_matching.csv", index=False)
print(f"Generated Model_matching.csv with {n} rows")
print(f"Sampling rate: {sampling_rate} Hz")
print(f"Nyquist limit: {sampling_rate // 2} Hz")
print("Embedded frequencies per signal:")
print("  cylinder_pressure : 50 Hz, 100 Hz")
print("  brake_power       : 20 Hz")
print("  air_fuel_ratio    : 30 Hz")
print("  boost_pressure    : 60 Hz")
print("  exhaust_temp      : 10 Hz")
print("  rpm               : 25 Hz")
print("  injection_timing  : 50 Hz")
print("  vibration         : 50 Hz, 120 Hz, 300 Hz")
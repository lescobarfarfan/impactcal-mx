"""Frozen CLIMADA hazards on shared centroids (DC-CAL-HAZ-*).

Builds and persists (HDF5 + _procedencia.json): TropCyclone (viento),
TCSurgeBathtub (marejada), TCRain (lluvia ciclónica), RiverFlood (fluvial).
Calibration only ever reads frozen hazards — never regenerates on the fly.
"""

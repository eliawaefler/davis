
g_chat = "https://grok.com/chat/67fafe81-f981-406c-8d98-7977133c1b0c"
link1 = "data.stadt-zuerich.ch"
link2 = "opentransportdata.swiss"

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timezone

# 1. Daten einlesen
# Wetterdaten
wetter_df = pd.read_csv('wetter/zurich_23.csv')
# mobilität Zürich
mobility_df = pd.read_csv('mobility_zurich/zurich_mobility.csv')

# 2. Zeitstempel vorbereiten
# Wetterdaten: dt_iso in datetime umwandeln und auf Stunde runden
wetter_df['dt_iso'] = pd.to_datetime(wetter_df['dt_iso'].str.replace(' +0000 UTC', '', regex=False), format='%Y-%m-%d %H:%M:%S')
wetter_df['date_hour'] = wetter_df['dt_iso'].dt.floor('H')

# Mobilitätsdaten: DATUM in datetime umwandeln
mobility_df['DATUM'] = pd.to_datetime(mobility_df['DATUM'], format='%Y-%m-%dT%H:%M')
mobility_df['date_hour'] = mobility_df['DATUM'].dt.floor('H')

# 3. Daten kombinieren (Merge auf date_hour)
combined_df = pd.merge(
    mobility_df,
    wetter_df,
    how='left',
    on='date_hour',
    suffixes=('_mobility', '_weather')
)

# Entferne Hilfsspalte
combined_df = combined_df.drop(columns=['date_hour'])

# 4. Deskriptive Statistik
# Numerische Variablen
numerical_cols = [
    'temp', 'visibility', 'dew_point', 'feels_like', 'temp_min', 'temp_max',
    'pressure', 'humidity', 'wind_speed', 'wind_gust', 'clouds_all',
    'VELO_IN', 'VELO_OUT', 'FUSS_IN', 'FUSS_OUT'
]
numerical_stats = combined_df[numerical_cols].describe()

# Kategoriale Variablen
categorical_cols = ['weather_main', 'weather_description', 'FK_STANDORT']
categorical_stats = {}
for col in categorical_cols:
    categorical_stats[col] = combined_df[col].value_counts()

# Korrelationsmatrix für numerische Variablen
correlation_matrix = combined_df[numerical_cols].corr()

# 5. Ergebnisse ausgeben
print("=== Deskriptive Statistik: Numerische Variablen ===")
print(numerical_stats)
print("\n=== Deskriptive Statistik: Kategoriale Variablen ===")
for col, stats in categorical_stats.items():
    print(f"\n{col}:\n{stats}")
print("\n=== Korrelationsmatrix ===")
print(correlation_matrix)

# 6. Optional: Speichere kombinierte Daten in CSV
#combined_df.to_csv('combined_weather_mobility_2023.csv', index=False)

# 7. Zeitreihenplot

# 1. Daten auf tägliche Mittelwerte aggregieren
daily_df = combined_df.groupby(combined_df['DATUM'].dt.date).agg({
    'temp': 'mean',
    'VELO_IN': 'mean'
}).reset_index()

# 2. Schneller Plot mit Plotly
fig = px.line(daily_df, x='DATUM', y=['temp', 'VELO_IN'], title='Temperatur und Fahrradfahrten 2023')
fig.update_layout(xaxis_title='Datum', yaxis_title='Werte')
fig.show()



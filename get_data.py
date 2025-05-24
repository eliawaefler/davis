import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
import time


"""
nur für Zürich 
bern manueller download, wetter gekauft.
"""


# Konfiguration
ZURICH_DATA_URLS = [
    "https://data.stadt-zuerich.ch/dataset/ted_taz_verkehrszaehlungen_werte_fussgaenger_velo/download/2023_verkehrszaehlungen_werte_fussgaenger_velo.csv",
    # Füge weitere URLs für 2024 hinzu, falls verfügbar
]

#BERN_DATA_URL = "https://data.bern.ch/api/3/action/datastore_search?resource_id=publibike-bern-2023"
WEATHER_API_KEY = "bef504195bf494577612d988c49970ae" # Ersetze mit deinem API-Schlüssel
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
OUTPUT_DIR = Path("mobility_zurich")
OUTPUT_FILE = "mobility_zurich/zurich_mobility.csv"
BERN_MAIN = "https://www.bern.ch/themen/stadt-recht-und-politik/bern-in-zahlen/katost/11mobver/11mobver-xls"

# Städte-Koordinaten für Wetterdaten
CITIES = {
    "Zurich": {"lat": 47.3769, "lon": 8.5417},
    "Bern": {"lat": 46.9481, "lon": 7.4474}
}

# Schweizer Feiertage (vereinfacht, für 2023–2024)
SWISS_HOLIDAYS = [
    "2023-01-01", "2023-04-07", "2023-04-10", "2023-05-18", "2023-08-01",
    "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-09", "2024-08-01"
]

def ensure_output_dir():
    """Erstellt das Ausgabeverzeichnis, falls es nicht existiert."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_mobility_data_zurich(urls):
    """Lädt Mobilitätsdaten für Zürich aus mehreren CSV-Dateien."""
    dfs = []
    for url in urls:
        try:
            df = pd.read_csv(url)
            # Filtern auf E-Bike/E-Scooter, falls Spalte vorhanden
            if "fahrzeugtyp" in df.columns:
                df = df[df["fahrzeugtyp"].str.contains("E-Bike|E-Scooter", case=False, na=False)]
            df["stadt"] = "Zurich"
            dfs.append(df)
        except Exception as e:
            print(f"Fehler beim Laden der Zürich-Daten von {url}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def fetch_mobility_data_bern(url):
    """Lädt Mobilitätsdaten für Bern via API."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        records = data["result"]["records"]
        df = pd.DataFrame(records)
        # Filtern auf E-Bike/E-Scooter, falls Spalte vorhanden
        if "fahrzeugtyp" in df.columns:
            df = df[df["fahrzeugtyp"].str.contains("E E-Bike|E-Scooter", case=False, na=False)]
        df["stadt"] = "Bern"
        return df
    except Exception as e:
        print(f"Fehler beim Laden der Bern-Daten: {e}")
        return pd.DataFrame()

def fetch_weather_data(city, lat, lon, start_date, end_date):
    """Holt historische Wetterdaten für eine Stadt."""
    weather_data = []
    current_date = start_date
    while current_date <= end_date:
        timestamp = int(current_date.timestamp())
        params = {
            "lat": lat,
            "lon": lon,
            "dt": timestamp,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        try:
            response = requests.get(WEATHER_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            for hourly in data.get("hourly", []):
                weather_data.append({
                    "stadt": city,
                    "zeitstempel": pd.to_datetime(hourly["dt"], unit="s"),
                    "temperatur": hourly["temp"],
                    "niederschlag": hourly.get("rain", {}).get("1h", 0),
                    "luftfeuchtigkeit": hourly["humidity"],
                    "windgeschwindigkeit": hourly["wind_speed"]
                })
            time.sleep(1)  # API-Limit vermeiden
        except Exception as e:
            print(f"Fehler beim Laden der Wetterdaten für {city} am {current_date}: {e}")
        current_date += timedelta(days=1)
    return pd.DataFrame(weather_data)

def clean_and_merge_data(mobility_df, weather_df):
    """Bereinigt und merged Mobilitäts- und Wetterdaten."""
    if mobility_df.empty or weather_df.empty:
        print("Keine Daten zum Bereinigen/Mergen verfügbar.")
        return pd.DataFrame()

    # Standardisieren der Zeitstempel
    if "zeitstempel" in mobility_df.columns:
        mobility_df["zeitstempel"] = pd.to_datetime(mobility_df["zeitstempel"], errors="coerce")
    elif "startzeit" in mobility_df.columns:
        mobility_df["zeitstempel"] = pd.to_datetime(mobility_df["startzeit"], errors="coerce")
    else:
        print("Keine Zeitstempel-Spalte gefunden.")
        return pd.DataFrame()

    weather_df["zeitstempel"] = pd.to_datetime(weather_df["zeitstempel"])

    # Stundenrundung für Merge
    mobility_df["zeitstempel_hour"] = mobility_df["zeitstempel"].dt.floor("H")
    weather_df["zeitstempel_hour"] = weather_df["zeitstempel"].dt.floor("H")

    # Merge auf Stadt und Stunde
    merged_df = pd.merge(
        mobility_df,
        weather_df,
        how="left",
        on=["stadt", "zeitstempel_hour"]
    )

    # Dimensionen hinzufügen
    merged_df["wochentag"] = merged_df["zeitstempel"].dt.day_name()
    merged_df["stunde"] = merged_df["zeitstempel"].dt.hour
    merged_df["feiertag"] = merged_df["zeitstempel"].dt.date.astype(str).isin(SWISS_HOLIDAYS).astype(int)

    # Bereinigung: Fehlende Werte
    merged_df["temperatur"] = merged_df["temperatur"].fillna(merged_df["temperatur"].mean())
    merged_df["niederschlag"] = merged_df["niederschlag"].fillna(0)
    merged_df["luftfeuchtigkeit"] = merged_df["luftfeuchtigkeit"].fillna(merged_df["luftfeuchtigkeit"].mean())
    merged_df["windgeschwindigkeit"] = merged_df["windgeschwindigkeit"].fillna(merged_df["windgeschwindigkeit"].mean())

    # Entferne temporäre Spalte
    merged_df = merged_df.drop(columns=["zeitstempel_hour"], errors="ignore")

    return merged_df

def main():
    """Hauptfunktion zum Abrufen und Speichern der Daten."""
    ensure_output_dir()

    # Zeitraum definieren (2023–2024)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)

    # Mobilitätsdaten laden
    print("Lade Mobilitätsdaten für Zürich...")
    zurich_df = fetch_mobility_data_zurich(ZURICH_DATA_URLS)
    print(zurich_df)
    print("Lade Mobilitätsdaten für Bern...")
    #bern_df = fetch_mobility_data_bern(BERN_DATA_URL)
    #print(bern_df)

    # Mobilitätsdaten kombinieren
    #mobility_df = pd.concat([zurich_df, bern_df], ignore_index=True)
    final_df = zurich_df
    # Wetterdaten laden
    """
    weather_dfs = []
    for city, coords in CITIES.items():
        print(f"Lade Wetterdaten für {city}...")
        weather_df = fetch_weather_data(city, coords["lat"], coords["lon"], start_date, end_date)
        weather_dfs.append(weather_df)
    weather_df = pd.concat(weather_dfs, ignore_index=True)
    
    # Daten bereinigen und mergen
    print("Bereinige und merge Daten...")
    final_df = clean_and_merge_data(mobility_df, weather_df)
    """
    # Ergebnis speichern
    if not final_df.empty:
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Daten erfolgreich gespeichert in {OUTPUT_FILE}")
    else:
        print("Keine Daten zum Speichern verfügbar.")

if __name__ == "__main__":
    main()
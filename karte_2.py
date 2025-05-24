import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import osmnx as ox

# Pfade zu den Shapefiles im /karte-Ordner
kantone_shp_path = "C:/Users/eliaw/PycharmProjects/CAS_Stat_DaVi/arbeit/karte/swissBOUNDARIES3D_1_5_TLM_KANTONSGEBIET.shp"
gemeinden_shp_path = "C:/Users/eliaw/PycharmProjects/CAS_Stat_DaVi/arbeit/karte/swissBOUNDARIES3D_1_5_TLM_HOHEITSGEBIET.shp"

# --- Karte 2: Gemeinden im Kanton Bern mit Stadtteilen ---
# Geodaten für Gemeinden laden (swissBOUNDARIES3D)
try:
    gdf = gpd.read_file(gemeinden_shp_path)
except Exception as e:
    print(f"Fehler beim Laden der Gemeindedaten: {e}")
    raise

# Debugging: Spalten der Gemeindedaten anzeigen
print("\nSpalten im Gemeinden-Shapefile:")
print(gdf.columns)

# Filtere Gemeinden im Kanton Bern (Kantonscode 2.0)
bern_gdf = gdf[gdf['KANTONSNUM'] == 2.0]

# Liste von Gemeinden im Raum Bern (erweitert)
bern_area = [
    'Bern', 'Köniz', 'Ostermundigen', 'Muri bei Bern', 'Bolligen', 'Ittigen',
    'Wohlen bei Bern', 'Belp', 'Kehrsatz', 'Zollikofen', 'Kirchlindach', 'Bremgarten bei Bern'
]
bern_gdf = bern_gdf[bern_gdf['NAME'].isin(bern_area)]

# Debugging: Gefilterte Gemeinden anzeigen
print("\nGefilterte Gemeinden:")
print(bern_gdf[['NAME', 'KANTONSNUM']])

# OSM-Daten für Stadtteile in Bern und Umgebung laden
place_name = "Bern, Switzerland"
try:
    # Lade Stadtteile (suburbs/neighbourhoods) aus OSM
    stadtteile_gdf = ox.features_from_place("Bern, Switzerland", tags={'place': ['suburb', 'neighbourhood']})

    # Filtere auf relevante Stadtteile (z.B. Wabern, Altstadt)
    stadtteile_gdf = stadtteile_gdf[stadtteile_gdf['name'].isin(['Wabern', 'Altstadt', 'Bümpliz', 'Bethlehem', 'Breitenrain', 'Mattenhof'])]
except Exception as e:
    print(f"Fehler beim Laden der OSM-Daten: {e}")
    stadtteile_gdf = None

# Plot-Einstellungen für Bern-Karte
plt.figure(figsize=(12, 10))

# Plot Gemeinden
colors = ['#ff4d4d', '#99ccff']  # Rot für Bern, Blau für andere Gemeinden
cmap = ListedColormap(colors)
bern_gdf['highlight'] = bern_gdf['NAME'].apply(lambda x: 'Bern' if x == 'Bern' else 'Andere Gemeinden')
bern_gdf.plot(column='highlight', cmap=cmap, linewidth=0.8, edgecolor='black', legend=False, ax=plt.gca())

# Plot Stadtteile (falls verfügbar)
if stadtteile_gdf is not None and not stadtteile_gdf.empty:
    stadtteile_gdf.plot(ax=plt.gca(), color='none', edgecolor='purple', linewidth=1.5, linestyle='--', alpha=0.7)

# Gemeindenamen auf der Karte anzeigen
for idx, row in bern_gdf.iterrows():
    centroid = row['geometry'].centroid
    plt.text(centroid.x, centroid.y, row['NAME'], fontsize=8, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

# Stadtteilnamen auf der Karte anzeigen (falls verfügbar)
if stadtteile_gdf is not None and not stadtteile_gdf.empty:
    for idx, row in stadtteile_gdf.iterrows():
        if row['geometry'].geom_type in ['Polygon', 'MultiPolygon']:
            centroid = row['geometry'].centroid
            plt.text(centroid.x, centroid.y, row['name'], fontsize=7, ha='center', va='center', color='purple', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

# Titel und Beschriftungen
plt.title('Gemeinden und Stadtteile im Kanton Bern\nHinweis: Wabern und Altstadt sind Stadtteile von Köniz bzw. Bern', fontsize=16, pad=10)
plt.xlabel('Längengrad (CH1903+ / LV95)', fontsize=12)
plt.ylabel('Breitengrad (CH1903+ / LV95)', fontsize=12)

# Legende manuell erstellen
legend_labels = ['Bern', 'Andere Gemeinden', 'Stadtteile (OSM)']
patches = [
    mpatches.Patch(color='#ff4d4d', label='Bern'),
    mpatches.Patch(color='#99ccff', label='Andere Gemeinden'),
    mpatches.Patch(color='purple', linestyle='--', label='Stadtteile (OSM)')
]
plt.legend(handles=patches, loc='upper left', fontsize=10)

# Plot speichern
output_path_bern = '/arbeit/karte/bern_gemeinden_karte.png'
plt.savefig(output_path_bern, bbox_inches='tight', dpi=300)
plt.close()

# Bestätigung
print(f"Bern-Gemeinden-Karte wurde erfolgreich als '{output_path_bern}' gespeichert.")
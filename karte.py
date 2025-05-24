
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap

# Pfade zu den Shapefiles im /karte-Ordner
kantone_shp_path = "C:/Users/eliaw/PycharmProjects/CAS_Stat_DaVi/arbeit/karte/swissBOUNDARIES3D_1_5_TLM_KANTONSGEBIET.shp"
gemeinden_shp_path = "C:/Users/eliaw/PycharmProjects/CAS_Stat_DaVi/arbeit/karte/swissBOUNDARIES3D_1_5_TLM_HOHEITSGEBIET.shp"

# --- Karte 1: Ganze Schweiz mit allen Kantonen ---
# Geodaten für Kantone laden
try:
    kantone_gdf = gpd.read_file(kantone_shp_path)
except Exception as e:
    print(f"Fehler beim Laden der Kantonsdaten: {e}")
    raise

# Debugging: Spalten der Kantonsdaten anzeigen
print("Spalten im Kantons-Shapefile:")
print(kantone_gdf.columns)

# Liste von Hex-Farbcodes für die 26 Kantone
hex_colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
    '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8', '#ffbb78',
    '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7',
    '#dbdb8d', '#9edae5', '#393b79', '#637939', '#8c6d31', '#843c39',
    '#7b4173', '#5254a3'
]

# Plot-Einstellungen für Schweiz-Karte
plt.figure(figsize=(12, 10))
kantone_gdf.plot(column='NAME', cmap=ListedColormap(hex_colors[:len(kantone_gdf)]), linewidth=0.8, edgecolor='black', legend=False)

# Titel und Beschriftungen
plt.title('Kantone der Schweiz', fontsize=16, pad=10)
plt.xlabel('Längengrad (CH1903+ / LV95)', fontsize=12)
plt.ylabel('Breitengrad (CH1903+ / LV95)', fontsize=12)

# Legende für Kantone (manuell erstellt)
kantons_names = kantone_gdf['NAME'].unique()
patches = [mpatches.Patch(color=hex_colors[i], label=kantons_names[i]) for i in range(len(kantons_names))]
plt.legend(handles=patches, loc='upper left', fontsize=8, title='Kantone')

# Plot speichern
output_path_schweiz = 'C:/Users/eliaw/PycharmProjects/CAS_Stat_DaVi/arbeit/schweiz_kantone_karte.png'
plt.savefig(output_path_schweiz, bbox_inches='tight', dpi=300)
plt.close()

# Bestätigung
print(f"Schweiz-Karte wurde erfolgreich als '{output_path_schweiz}' gespeichert.")

# --- Karte 2: Gemeinden im Kanton Bern ---
# Geodaten für Gemeinden laden
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

# Erstelle eine Spalte für die Visualisierung (Bern hervorheben)
bern_gdf['highlight'] = bern_gdf['NAME'].apply(lambda x: 'Bern' if x == 'Bern' else 'Andere Gemeinden')

# Plot-Einstellungen für Bern-Karte
plt.figure(figsize=(12, 10))
colors = ['#ff4d4d', '#99ccff']  # Rot für Bern, Blau für andere Gemeinden
cmap = ListedColormap(colors)
bern_gdf.plot(column='highlight', cmap=cmap, linewidth=0.8, edgecolor='black', legend=False)

# Gemeindenamen auf der Karte anzeigen
for idx, row in bern_gdf.iterrows():
    # Berechne den Mittelpunkt der Geometrie für die Textplatzierung
    centroid = row['geometry'].centroid
    plt.text(centroid.x, centroid.y, row['NAME'], fontsize=8, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

# Titel und Beschriftungen
plt.title('Gemeinden im Kanton Bern (Bern hervorgehoben)\nHinweis: Wabern ist Teil von Köniz', fontsize=16, pad=10)
plt.xlabel('Längengrad (CH1903+ / LV95)', fontsize=12)
plt.ylabel('Breitengrad (CH1903+ / LV95)', fontsize=12)

# Legende manuell erstellen
legend_labels = ['Bern', 'Andere Gemeinden']
patches = [mpatches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(legend_labels))]
plt.legend(handles=patches, loc='upper left', fontsize=10)

# Plot speichern
output_path_bern = '/arbeit/karte/bern_gemeinden_karte.png'
plt.savefig(output_path_bern, bbox_inches='tight', dpi=300)
plt.close()

# Bestätigung
print(f"Bern-Gemeinden-Karte wurde erfolgreich als '{output_path_bern}' gespeichert.")
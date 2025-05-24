import zipfile
import os
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import pandas as pd
import shapefile
import shapefile
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import numpy as np



def display_shapefile_contents(filepath):
    """
    Opens a shapefile and displays its contents (geometry and attributes).

    Args:
        filepath (str): Path to the .shp file

    Returns:
        None: Prints the shapes and records to the console
    """
    try:
        # Read the shapefile
        sf = shapefile.Reader(filepath)

        # Get the shapes (geometry) and records (attributes)
        shapes = sf.shapes()
        records = sf.records()
        fields = sf.fields[1:]  # Skip the first field (DeletionFlag)

        # Print field names (attribute names)
        field_names = [field[0] for field in fields]
        print("Fields (Attributes):", field_names)

        # Print each shape and its corresponding record
        for i, (shape, record) in enumerate(zip(shapes, records)):
            print(f"\nShape {i + 1}:")
            print("  Type:", shape.shapeTypeName)
            print("  Points:", shape.points)  # Coordinates of the shape
            print("  Attributes:", dict(zip(field_names, record)))

        # Close the shapefile
        sf.close()

    except Exception as e:
        print(f"Error reading shapefile: {str(e)}")



def extract_zip(zip_path, extract_to):
    """
    Extract a .zip file to a specified directory.

    Args:
        zip_path (str): Path to the .zip file
        extract_to (str): Directory to extract files to
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def create_clickable_map(zip_path, output_html='map.html'):
    """
    Create a clickable map from a .zip file containing shapefiles.

    Args:
        zip_path (str): Path to the .zip file
        output_html (str): Path to save the output HTML map
    """
    # Step 1: Extract the .zip file
    extract_dir = "extracted_shapefiles"
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    extract_zip(zip_path, extract_dir)

    # Step 2: Find and load the shapefile
    shp_file = None
    for file in os.listdir(extract_dir):
        if file.endswith('.shp'):
            shp_file = os.path.join(extract_dir, file)
            break

    if not shp_file:
        raise FileNotFoundError("No .shp file found in the extracted directory")

    # Read the shapefile using geopandas
    gdf = gpd.read_file(shp_file)

    # Step 3: Inspect and preprocess the GeoDataFrame
    print("Columns in GeoDataFrame:", gdf.columns.tolist())
    print("Data types:\n", gdf.dtypes)
    print("Sample data:\n", gdf.head())

    # Convert Timestamp columns to strings
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)

    # Step 4: Create a folium map
    # Calculate the center of the map based on the geometries
    center = gdf.geometry.centroid
    map_center = [center.y.mean(), center.x.mean()]

    # Initialize the map
    m = folium.Map(location=map_center, zoom_start=10)

    # Step 5: Add the shapefile data to the map
    def style_function(feature):
        return {
            'fillColor': 'blue',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5,
        }

    # Add GeoJSON layer with clickable features
    # Adjust 'fields' based on actual column names (excluding geometry)
    available_columns = [col for col in gdf.columns if col != 'geometry']
    tooltip_fields = ['NAME'] if 'NAME' in available_columns else available_columns[:1]
    popup_fields = available_columns[:2]  # Use first two non-geometry columns

    folium.GeoJson(
        gdf,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=[f"{field}:" for field in tooltip_fields],
            localize=True
        ),
        popup=folium.GeoJsonPopup(
            fields=popup_fields,
            aliases=[f"{field}:" for field in popup_fields],
            localize=True
        )
    ).add_to(m)

    # Step 6: Save the map to an HTML file
    m.save(output_html)
    print(f"Map saved to {output_html}")


def visualize_shapefile(filepath):
    """
    Opens a shapefile, displays its contents, and visualizes the geometries using matplotlib.
    Adjusted for large coordinates and MULTIPOLYGON shapes.

    Args:
        filepath (str): Path to the .shp file

    Returns:
        None: Prints the contents and displays a plot of the shapes
    """
    try:
        # Read the shapefile
        sf = shapefile.Reader(filepath)

        # Get the shapes (geometry) and records (attributes)
        shapes = sf.shapes()
        records = sf.records()
        fields = sf.fields[1:]  # Skip the first field (DeletionFlag)

        # Print field names (attribute names)
        field_names = [field[0] for field in fields]
        print("Fields (Attributes):", field_names)

        # Print each shape and its corresponding record
        for i, (shape, record) in enumerate(zip(shapes, records)):
            print(f"\nShape {i + 1}:")
            print("  Type:", shape.shapeTypeName)
            print("  Points (first few):", shape.points[:5])  # Print first few points to avoid clutter
            print("  Attributes:", dict(zip(field_names, record)))

        # Set up the plot
        fig, ax = plt.subplots(figsize=(10, 10))

        # To handle large coordinates, compute the bounding box for normalization
        all_points = []
        for shape in shapes:
            all_points.extend(shape.points)
        if not all_points:
            raise ValueError("No points found in shapefile")

        all_points = np.array(all_points)
        min_x, min_y = all_points.min(axis=0)
        max_x, max_y = all_points.max(axis=0)

        # Normalize coordinates to a smaller range (e.g., 0 to 1000) for plotting
        scale_x = 1000 / (max_x - min_x) if max_x != min_x else 1
        scale_y = 1000 / (max_y - min_y) if max_y != min_y else 1
        scale = min(scale_x, scale_y)  # Use the smaller scale to preserve aspect ratio

        # Plot each shape based on its type
        patches = []
        for shape in shapes:
            if shape.shapeTypeName == "POINT":
                # Plot points
                x, y = shape.points[0]
                x = (x - min_x) * scale
                y = (y - min_y) * scale
                ax.plot(x, y, 'o', color='blue',
                        label='Point' if 'Point' not in ax.get_legend_handles_labels()[1] else "")

            elif shape.shapeTypeName in ["POLYLINE", "POLYGON", "MULTIPOLYGON"]:
                # Handle parts (for MULTIPOLYGON or POLYGON with holes)
                parts = shape.parts
                points = shape.points
                if shape.shapeTypeName == "POLYLINE":
                    # Plot lines
                    x, y = zip(*[((pt[0] - min_x) * scale, (pt[1] - min_y) * scale) for pt in points])
                    ax.plot(x, y, color='red',
                            label='Polyline' if 'Polyline' not in ax.get_legend_handles_labels()[1] else "")
                else:
                    # Plot polygons or multipolygons
                    for i in range(len(parts)):
                        start = parts[i]
                        end = parts[i + 1] if i + 1 < len(parts) else len(points)
                        poly_points = [((pt[0] - min_x) * scale, (pt[1] - min_y) * scale) for pt in points[start:end]]
                        if len(poly_points) > 2:  # Ensure enough points to form a polygon
                            poly = Polygon(poly_points, closed=True, edgecolor='black', facecolor='green', alpha=0.5)
                            patches.append(poly)

        # Add polygons to the plot if any
        if patches:
            p = PatchCollection(patches, match_original=True)
            ax.add_collection(p)
            ax.set_label('Polygon')

        # Set equal aspect ratio to preserve shape
        ax.set_aspect('equal')

        # Adjust plot settings
        ax.set_xlabel("Normalized X Coordinate")
        ax.set_ylabel("Normalized Y Coordinate")
        ax.set_title("Map of Switzerland (swissBOUNDARIES3D)")
        #ax.legend()

        # Set plot limits based on normalized coordinates
        ax.set_xlim(-50, 1050)  # Add padding
        ax.set_ylim(-50, 1050)

        # Save the plot (Pyodide-compatible)
        plt.savefig('switzerland_map.png')

        # Close the shapefile
        sf.close()

    except Exception as e:
        print(f"Error processing shapefile: {str(e)}")


# Example usage
if __name__ == "__main__":
    zip_path = 'karte/karte.zip'  # Replace with your .zip file path

    # Example usage (commented out since we can't do file I/O in this environment)
    # display_shapefile_contents(r"C:\Users\eliaw\PycharmProjects\CAS_Stat_DaVi\arbeit\extracted_shapefiles\swissBOUNDARIES3D_1_5_TLM_BEZIRKSGEBIET.shp")
    visualize_shapefile(r"C:\Users\eliaw\PycharmProjects\CAS_Stat_DaVi\arbeit\extracted_shapefiles\swissBOUNDARIES3D_1_5_TLM_BEZIRKSGEBIET.shp")

    #create_clickable_map(zip_path, 'swiss_boundaries_map.html')
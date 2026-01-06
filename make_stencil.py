import trimesh
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import io

def generate_stencil(
    text, 
    font_path=None,  # Path to a .ttf file. If None, uses system default (careful with islands!)
    font_size=50, 
    stencil_thickness=1.0, 
    margin=10,
    output_filename="stencil.stl"
):
    print(f"Generating stencil for: '{text}'...")

    # 1. Create the Text Path using Matplotlib
    # We use TextPath to get the outline of the font characters
    prop = FontProperties(fname=font_path) if font_path else None
    tpath = TextPath((0, 0), text, size=font_size, prop=prop)
    
    # Get the bounding box of the text to size our plastic plate
    extents = tpath.get_extents()
    text_width = extents.width
    text_height = extents.height
    
    # 2. Convert TextPath to Shapely Polygons
    # This involves iterating through the vertices and codes from matplotlib
    polys = []
    codes = tpath.codes
    verts = tpath.vertices
    
    # Simple parser to turn matplotlib paths into shapely polygons
    # Note: This handles standard simple glyphs. Complex curves are approximated.
    path_polygons = []
    curr_poly = []
    
    for i, code in enumerate(codes):
        if code == tpath.MOVETO:
            if curr_poly:
                path_polygons.append(curr_poly)
            curr_poly = [verts[i]]
        elif code == tpath.LINETO:
            curr_poly.append(verts[i])
        elif code == tpath.CLOSEPOLY:
            curr_poly.append(curr_poly[0])
            path_polygons.append(curr_poly)
            curr_poly = []
        elif code == tpath.CURVE3 or code == tpath.CURVE4:
            # Simplification: Treat curves as lines for the stencil cutout 
            # (Higher vertex density in textpath usually makes this look fine)
            curr_poly.append(verts[i])
            
    if curr_poly:
        path_polygons.append(curr_poly)

    # Convert lists of points to Shapely Polygons
    # We use buffer(0) to fix any self-intersecting geometry quirks
    shapely_polys = [Polygon(p).buffer(0) for p in path_polygons]
    text_shape = unary_union(shapely_polys)

    # 3. Create the Base Plate (The Plastic Sheet)
    # Define dimensions based on text size + margins
    plate_w = text_width + (margin * 2)
    plate_h = text_height + (margin * 2)
    
    # Center the box around the text (which starts at 0,0)
    # Text bounds are x: 0 to width, y: 0 to height (approx)
    min_x, min_y = extents.xmin, extents.ymin
    
    box_min_x = min_x - margin
    box_min_y = min_y - margin
    box_max_x = min_x + text_width + margin
    box_max_y = min_y + text_height + margin
    
    plate_coords = [
        (box_min_x, box_min_y),
        (box_max_x, box_min_y),
        (box_max_x, box_max_y),
        (box_min_x, box_max_y)
    ]
    plate_poly = Polygon(plate_coords)

    # 4. The Magic: 2D Boolean Subtraction
    # Subtract the text from the plate
    stencil_2d = plate_poly.difference(text_shape)

    # 5. Extrude to 3D
    print("Extruding mesh...")
    mesh = trimesh.creation.extrude_polygon(stencil_2d, height=stencil_thickness)

    # 6. Export
    mesh.export(output_filename)
    print(f"Done! Saved to {output_filename}")
    print(f"Dimensions: {mesh.extents}")

# --- CONFIGURATION ---
NAME_TO_PRINT = "SUMMER"

# IMPORTANT: Use a Stencil font to prevent the middle of 'O', 'A', 'P' from falling out.
# Download a font like 'Allerta Stencil' or 'Stardos Stencil' from Google Fonts.
# Put the .ttf file in the same folder as this script.
FONT_PATH = "AllertaStencil-Regular.ttf" 

# If you don't have the font yet, set FONT_PATH = None to test, 
# but remember the 'islands' will be loose!

if __name__ == "__main__":
    # Note: If you don't have the specific font file, comment out the font_path argument
    # to use the default system font (but be warned about the islands!)
    
    try:
        generate_stencil(
            NAME_TO_PRINT, 
            font_path=FONT_PATH,
            font_size=40,
            stencil_thickness=0.8  # 0.8mm is usually flexible but sturdy
        )
    except Exception as e:
        print(f"Error: {e}")
        print("Did you download the font? If not, set FONT_PATH = None in the script.")
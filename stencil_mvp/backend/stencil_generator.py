import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import translate
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MPLPolygon
import io


def generate_stencil_geometry(text, font_path, font_size, width, height, margin, thickness):
    """
    Generate a 3D stencil mesh from text input.
    
    Args:
        text: Text string to generate stencil for
        font_path: Path to .ttf font file
        font_size: Font size in points
        width: Plate width in mm
        height: Plate height in mm
        margin: Margin around text in mm
        thickness: Plate thickness in mm
    
    Returns:
        trimesh.Trimesh: 3D mesh of the stencil
    """
    # 1. Create TextPath
    prop = FontProperties(fname=font_path) if font_path else None
    tpath = TextPath((0, 0), text, size=font_size, prop=prop)
    
    # 2. Convert to Shapely Polygons
    codes = tpath.codes
    verts = tpath.vertices
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
            # Approximation: treat curves as lines
            curr_poly.append(verts[i])
    
    if curr_poly:
        path_polygons.append(curr_poly)
    
    # Convert to Shapely Polygons and union them
    shapely_polys = [Polygon(p).buffer(0) for p in path_polygons if len(p) >= 3]
    if not shapely_polys:
        raise ValueError("No valid polygons generated from text")
    
    text_shape = unary_union(shapely_polys)
    
    # 3. Create Plate
    plate_poly = Polygon([(0, 0), (width, 0), (width, height), (0, height)])
    
    # 4. Center text in the plate
    text_bounds = text_shape.bounds  # (minx, miny, maxx, maxy)
    text_w = text_bounds[2] - text_bounds[0]
    text_h = text_bounds[3] - text_bounds[1]
    
    text_center_x = text_bounds[0] + text_w / 2
    text_center_y = text_bounds[1] + text_h / 2
    plate_center_x = width / 2
    plate_center_y = height / 2
    
    offset_x = plate_center_x - text_center_x
    offset_y = plate_center_y - text_center_y
    
    text_shape_centered = translate(text_shape, xoff=offset_x, yoff=offset_y)
    
    # 5. Boolean Difference (subtract text from plate)
    stencil_2d = plate_poly.difference(text_shape_centered)
    
    # Handle MultiPolygon case
    if isinstance(stencil_2d, MultiPolygon):
        # Use the largest polygon if we have multiple
        stencil_2d = max(stencil_2d.geoms, key=lambda p: p.area)
    
    # 6. Extrude to 3D
    mesh = trimesh.creation.extrude_polygon(stencil_2d, height=thickness)
    
    return mesh


def generate_stencil_2d_geometry(text, font_path, font_size, width, height, margin):
    """
    Generate 2D stencil geometry (without 3D extrusion) for preview.
    Returns the same geometry components as generate_stencil_geometry but without the mesh.
    """
    # 1. Create TextPath
    prop = FontProperties(fname=font_path) if font_path else None
    tpath = TextPath((0, 0), text, size=font_size, prop=prop)
    
    # 2. Convert to Shapely Polygons
    codes = tpath.codes
    verts = tpath.vertices
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
            # Approximation: treat curves as lines
            curr_poly.append(verts[i])
    
    if curr_poly:
        path_polygons.append(curr_poly)
    
    # Convert to Shapely Polygons and union them
    shapely_polys = [Polygon(p).buffer(0) for p in path_polygons if len(p) >= 3]
    if not shapely_polys:
        raise ValueError("No valid polygons generated from text")
    
    text_shape = unary_union(shapely_polys)
    
    # 3. Create Plate
    plate_poly = Polygon([(0, 0), (width, 0), (width, height), (0, height)])
    
    # 4. Center text in the plate
    text_bounds = text_shape.bounds  # (minx, miny, maxx, maxy)
    text_w = text_bounds[2] - text_bounds[0]
    text_h = text_bounds[3] - text_bounds[1]
    
    text_center_x = text_bounds[0] + text_w / 2
    text_center_y = text_bounds[1] + text_h / 2
    plate_center_x = width / 2
    plate_center_y = height / 2
    
    offset_x = plate_center_x - text_center_x
    offset_y = plate_center_y - text_center_y
    
    text_shape_centered = translate(text_shape, xoff=offset_x, yoff=offset_y)
    
    # 5. Boolean Difference (subtract text from plate)
    stencil_2d = plate_poly.difference(text_shape_centered)
    
    # Handle MultiPolygon case
    if isinstance(stencil_2d, MultiPolygon):
        # Use the largest polygon if we have multiple
        stencil_2d = max(stencil_2d.geoms, key=lambda p: p.area)
    
    return stencil_2d, text_shape_centered, plate_poly


def generate_preview_image(text, font_path, font_size, width, height, margin):
    """
    Generate a 2D preview image of the stencil from above.
    Returns PNG image bytes.
    """
    # Get 2D geometry
    stencil_2d, text_shape_centered, plate_poly = generate_stencil_2d_geometry(
        text, font_path, font_size, width, height, margin
    )
    
    # Create figure with white background
    fig, ax = plt.subplots(1, 1, figsize=(10, 6), facecolor='white')
    ax.set_aspect('equal')
    ax.set_facecolor('white')
    
    # Draw the plate outline
    plate_coords = list(plate_poly.exterior.coords)
    plate_patch = MPLPolygon(plate_coords, facecolor='#e0e0e0', edgecolor='#333', linewidth=2, alpha=0.3)
    ax.add_patch(plate_patch)
    
    # Draw the stencil (what remains after cutting out text)
    if isinstance(stencil_2d, MultiPolygon):
        for geom in stencil_2d.geoms:
            coords = list(geom.exterior.coords)
            patch = MPLPolygon(coords, facecolor='#4a90e2', edgecolor='#2c5aa0', linewidth=1.5)
            ax.add_patch(patch)
            # Handle holes
            for interior in geom.interiors:
                hole_coords = list(interior.coords)
                hole = MPLPolygon(hole_coords, facecolor='white', edgecolor='#2c5aa0', linewidth=1)
                ax.add_patch(hole)
    else:
        coords = list(stencil_2d.exterior.coords)
        patch = MPLPolygon(coords, facecolor='#4a90e2', edgecolor='#2c5aa0', linewidth=1.5)
        ax.add_patch(patch)
        # Handle holes (the cutout text areas)
        for interior in stencil_2d.interiors:
            hole_coords = list(interior.coords)
            hole = MPLPolygon(hole_coords, facecolor='white', edgecolor='#2c5aa0', linewidth=1)
            ax.add_patch(hole)
    
    # Draw text cutouts in a different color to show what's being cut out
    if isinstance(text_shape_centered, MultiPolygon):
        for geom in text_shape_centered.geoms:
            coords = list(geom.exterior.coords)
            text_patch = MPLPolygon(coords, facecolor='white', edgecolor='#d32f2f', linewidth=1.5, linestyle='--', alpha=0.7)
            ax.add_patch(text_patch)
    else:
        coords = list(text_shape_centered.exterior.coords)
        text_patch = MPLPolygon(coords, facecolor='white', edgecolor='#d32f2f', linewidth=1.5, linestyle='--', alpha=0.7)
        ax.add_patch(text_patch)
    
    # Set axis limits with some padding
    ax.set_xlim(-5, width + 5)
    ax.set_ylim(-5, height + 5)
    ax.invert_yaxis()  # Match typical image coordinates
    
    # Add labels
    ax.set_xlabel('Width (mm)', fontsize=10)
    ax.set_ylabel('Height (mm)', fontsize=10)
    ax.set_title(f'Stencil Preview: "{text}"', fontsize=12, fontweight='bold', pad=10)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    
    return buf.getvalue()


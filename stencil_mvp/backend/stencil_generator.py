import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import translate
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties


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


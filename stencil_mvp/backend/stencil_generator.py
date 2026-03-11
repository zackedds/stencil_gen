import math
import trimesh
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from shapely.affinity import translate
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPLPolygon, Circle as MPLCircle
import numpy as np
import io


def get_supported_characters(font_path):
    """
    Test which characters the font can actually render into valid geometry.
    Returns a string of all supported characters.
    """
    import string
    candidates = (
        string.ascii_uppercase + string.ascii_lowercase + string.digits
        + "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        + "€£¥¢—–×÷¡¿"
        + "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖÙÚÛÜÝÞ"
        + "àáâãäåçèéêëìíîïðñòóôõöùúûüýþÿ"
    )
    prop = FontProperties(fname=font_path) if font_path else None
    supported = [' ']

    # Baseline: geometry for just "AA" (used to detect if a char adds geometry)
    try:
        baseline = TextPath((0, 0), "AA", size=40, prop=prop)
        baseline_codes = len(baseline.codes) if baseline.codes is not None else 0
    except Exception:
        baseline_codes = 0

    for ch in candidates:
        try:
            # First try the character alone
            tp = TextPath((0, 0), ch, size=40, prop=prop)
            if tp.codes is not None and len(tp.codes) > 0:
                ext = tp.get_extents()
                if ext.width > 0 and ext.height > 0:
                    supported.append(ch)
                    continue
        except Exception:
            pass

        # Some chars crash alone but work embedded in strings.
        # Test by embedding between two A's and checking if geometry changes.
        try:
            tp = TextPath((0, 0), "A" + ch + "A", size=40, prop=prop)
            if tp.codes is not None and len(tp.codes) > baseline_codes:
                supported.append(ch)
        except Exception:
            continue

    return "".join(supported)


def _text_to_shapely(text, font_path, font_size):
    """Convert text string to a Shapely geometry using matplotlib TextPath."""
    prop = FontProperties(fname=font_path) if font_path else None
    tpath = TextPath((0, 0), text, size=font_size, prop=prop)

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
        elif code in (tpath.CURVE3, tpath.CURVE4):
            curr_poly.append(verts[i])

    if curr_poly:
        path_polygons.append(curr_poly)

    shapely_polys = [Polygon(p).buffer(0) for p in path_polygons if len(p) >= 3]
    if not shapely_polys:
        raise ValueError("No valid polygons generated from text")

    return unary_union(shapely_polys)


def calculate_text_dimensions(text, font_path, font_size):
    """Calculate the dimensions of rendered text. Returns (width, height)."""
    prop = FontProperties(fname=font_path) if font_path else None
    tpath = TextPath((0, 0), text, size=font_size, prop=prop)
    extents = tpath.get_extents()
    return extents.width, extents.height


def calculate_optimal_plate_size(text, font_path, font_size, margin):
    """Calculate plate dimensions to fit text with margins. Returns (width, height)."""
    text_width, text_height = calculate_text_dimensions(text, font_path, font_size)
    width = text_width + (margin * 2)
    height = text_height + (margin * 2)
    width = ((int(width) // 5) + 1) * 5
    height = ((int(height) // 5) + 1) * 5
    return width, height


def calculate_font_for_plate(text, font_path, width, height, margin):
    """
    Calculate the optimal font size to fit text within given plate dimensions.
    Uses binary search to find the largest font that fits.
    Returns the optimal font_size.
    """
    available_width = width - (margin * 2)
    available_height = height - (margin * 2)

    if available_width <= 0 or available_height <= 0:
        return 10.0

    lo, hi = 4.0, 200.0
    best = lo

    for _ in range(30):
        mid = (lo + hi) / 2
        tw, th = calculate_text_dimensions(text, font_path, mid)
        if tw <= available_width and th <= available_height:
            best = mid
            lo = mid + 0.1
        else:
            hi = mid - 0.1

    return round(best, 1)


def _rounded_rect(width, height, radius, skip_top_left=False):
    """
    Build a rectangle with rounded corners.
    skip_top_left=True leaves the top-left corner sharp (for hanging tab).
    """
    if radius <= 0:
        return Polygon([(0, 0), (width, 0), (width, height), (0, height)])

    r = min(radius, width / 2, height / 2)
    pts = []
    n = 8  # points per quarter arc

    # Bottom-left corner (0, 0)
    for i in range(n + 1):
        angle = math.pi + (math.pi / 2) * (i / n)
        pts.append((r + r * math.cos(angle), r + r * math.sin(angle)))

    # Bottom-right corner (width, 0)
    for i in range(n + 1):
        angle = 3 * math.pi / 2 + (math.pi / 2) * (i / n)
        pts.append((width - r + r * math.cos(angle), r + r * math.sin(angle)))

    # Top-right corner (width, height)
    for i in range(n + 1):
        angle = 0 + (math.pi / 2) * (i / n)
        pts.append((width - r + r * math.cos(angle), height - r + r * math.sin(angle)))

    # Top-left corner (0, height) — sharp if skip_top_left
    if skip_top_left:
        pts.append((0, height))
    else:
        for i in range(n + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / n)
            pts.append((r + r * math.cos(angle), height - r + r * math.sin(angle)))

    return Polygon(pts)


def _make_hanging_tab(width, height, hole_diameter):
    """
    Create a hanging tab that protrudes from the top-left corner of the plate.
    Returns (tab_solid, hole_cutout):
      - tab_solid: the circular tab shape extending beyond the plate corner
      - hole_cutout: the hole punched through the tab center
    The tab center sits at the corner so half the tab extends outward.
    """
    radius = hole_diameter / 2
    tab_radius = radius + 3.0  # tab is 3mm wider than hole on each side
    # Place center at the top-left corner of the plate
    cx = 0
    cy = height
    tab_solid = Point(cx, cy).buffer(tab_radius, resolution=48)
    hole_cutout = Point(cx, cy).buffer(radius, resolution=48)
    return tab_solid, hole_cutout


def generate_stencil_geometry(text, font_path, font_size, width, height, margin,
                              thickness, hanging_hole=False, hole_diameter=5.0,
                              corner_radius=0.0):
    """
    Generate a 3D stencil mesh from text input.
    Returns trimesh.Trimesh.
    """
    text_shape = _text_to_shapely(text, font_path, font_size)

    plate_poly = _rounded_rect(width, height, corner_radius,
                               skip_top_left=(hanging_hole and hole_diameter > 0))

    # Add hanging tab (extends beyond plate corner) before cutting text
    if hanging_hole and hole_diameter > 0:
        tab_solid, hole_cutout = _make_hanging_tab(width, height, hole_diameter)
        plate_poly = plate_poly.union(tab_solid)

    # Center text in the plate (use original plate bounds for centering)
    tb = text_shape.bounds
    text_cx = tb[0] + (tb[2] - tb[0]) / 2
    text_cy = tb[1] + (tb[3] - tb[1]) / 2
    offset_x = width / 2 - text_cx
    offset_y = height / 2 - text_cy
    text_centered = translate(text_shape, xoff=offset_x, yoff=offset_y)

    # Subtract text from plate
    stencil_2d = plate_poly.difference(text_centered)

    # Punch the hole through the tab
    if hanging_hole and hole_diameter > 0:
        stencil_2d = stencil_2d.difference(hole_cutout)

    # Handle MultiPolygon — keep all pieces for proper stencil
    if isinstance(stencil_2d, MultiPolygon):
        meshes = []
        for geom in stencil_2d.geoms:
            try:
                m = trimesh.creation.extrude_polygon(geom, height=thickness)
                meshes.append(m)
            except Exception:
                continue
        if not meshes:
            raise ValueError("Failed to generate 3D geometry")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = trimesh.creation.extrude_polygon(stencil_2d, height=thickness)

    return mesh


def generate_stencil_2d_geometry(text, font_path, font_size, width, height, margin,
                                  hanging_hole=False, hole_diameter=5.0,
                                  corner_radius=0.0):
    """Generate 2D stencil geometry for preview. Returns (stencil_2d, text_centered, plate_poly, hole_cutout)."""
    text_shape = _text_to_shapely(text, font_path, font_size)

    plate_poly = _rounded_rect(width, height, corner_radius,
                               skip_top_left=(hanging_hole and hole_diameter > 0))

    hole_cutout = None
    if hanging_hole and hole_diameter > 0:
        tab_solid, hole_cutout = _make_hanging_tab(width, height, hole_diameter)
        plate_poly = plate_poly.union(tab_solid)

    tb = text_shape.bounds
    text_cx = tb[0] + (tb[2] - tb[0]) / 2
    text_cy = tb[1] + (tb[3] - tb[1]) / 2
    offset_x = width / 2 - text_cx
    offset_y = height / 2 - text_cy
    text_centered = translate(text_shape, xoff=offset_x, yoff=offset_y)

    stencil_2d = plate_poly.difference(text_centered)

    if hole_cutout is not None:
        stencil_2d = stencil_2d.difference(hole_cutout)

    return stencil_2d, text_centered, plate_poly, hole_cutout


def generate_preview_image(text, font_path, font_size, width, height, margin,
                           hanging_hole=False, hole_diameter=5.0, corner_radius=0.0):
    """Generate a clean 2D preview image. Returns PNG bytes."""
    stencil_2d, text_centered, plate_poly, hole_geom = generate_stencil_2d_geometry(
        text, font_path, font_size, width, height, margin, hanging_hole, hole_diameter,
        corner_radius
    )

    # Figure sizing — keep aspect ratio proportional to plate
    aspect = width / height
    fig_h = 5
    fig_w = max(fig_h * aspect, 4)
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h), facecolor='#fafafa')
    ax.set_aspect('equal')
    ax.set_facecolor('#fafafa')

    def _draw_polygon(geom, facecolor, edgecolor, lw=1.5):
        if isinstance(geom, MultiPolygon):
            for g in geom.geoms:
                _draw_polygon(g, facecolor, edgecolor, lw)
            return
        coords = list(geom.exterior.coords)
        patch = MPLPolygon(coords, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(patch)
        for interior in geom.interiors:
            hole_coords = list(interior.coords)
            hole_patch = MPLPolygon(hole_coords, facecolor='#fafafa', edgecolor=edgecolor, linewidth=lw * 0.7)
            ax.add_patch(hole_patch)

    # Draw the stencil body
    _draw_polygon(stencil_2d, '#5b7db1', '#3a5a8c', 1.5)

    # Get text bounds for dimension callout
    tb = text_centered.bounds  # (minx, miny, maxx, maxy)
    text_w = tb[2] - tb[0]
    text_h = tb[3] - tb[1]

    # Padding for dimension lines
    pad = max(width, height) * 0.14
    stencil_bounds = stencil_2d.bounds
    ax.set_xlim(min(-pad * 1.1, stencil_bounds[0] - pad * 0.5),
                max(width + pad * 0.4, stencil_bounds[2] + pad * 0.4))
    ax.set_ylim(min(-pad * 1.0, stencil_bounds[1] - pad * 0.5),
                max(height + pad * 1.1, stencil_bounds[3] + pad * 0.5))

    dim_color = '#777'
    dim_lw = 0.8
    arrow_props = dict(arrowstyle='<->', color=dim_color, lw=dim_lw)
    ext_props = dict(color=dim_color, lw=0.4, linestyle='-')

    # --- Plate width dimension (bottom) ---
    dim_y = -pad * 0.45
    ax.annotate('', xy=(0, dim_y), xytext=(width, dim_y), arrowprops=arrow_props)
    ax.plot([0, 0], [0, dim_y + pad * 0.05], **ext_props)
    ax.plot([width, width], [0, dim_y + pad * 0.05], **ext_props)
    ax.text(width / 2, dim_y - pad * 0.12, f'{width:.0f}mm',
            ha='center', va='top', fontsize=8, color=dim_color, fontweight='bold')

    # --- Plate height dimension (left) ---
    dim_x = -pad * 0.45
    ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, height), arrowprops=arrow_props)
    ax.plot([0, dim_x + pad * 0.05], [0, 0], **ext_props)
    ax.plot([0, dim_x + pad * 0.05], [height, height], **ext_props)
    ax.text(dim_x - pad * 0.12, height / 2, f'{height:.0f}mm',
            ha='right', va='center', fontsize=8, color=dim_color, fontweight='bold',
            rotation=90)

    # --- Text width dimension (top, inside plate area) ---
    text_dim_color = '#e07020'
    text_arrow = dict(arrowstyle='<->', color=text_dim_color, lw=1.0)
    text_ext = dict(color=text_dim_color, lw=0.5, linestyle='-')
    text_dim_y = height + pad * 0.35
    ax.annotate('', xy=(tb[0], text_dim_y), xytext=(tb[2], text_dim_y),
                arrowprops=text_arrow)
    ax.plot([tb[0], tb[0]], [tb[3], text_dim_y - pad * 0.03], **text_ext)
    ax.plot([tb[2], tb[2]], [tb[3], text_dim_y - pad * 0.03], **text_ext)
    ax.text((tb[0] + tb[2]) / 2, text_dim_y + pad * 0.08,
            f'text: {text_w:.0f}mm',
            ha='center', va='bottom', fontsize=8, color=text_dim_color,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                      edgecolor=text_dim_color, alpha=0.9, linewidth=0.6))

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#fafafa',
                pad_inches=0.15)
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()

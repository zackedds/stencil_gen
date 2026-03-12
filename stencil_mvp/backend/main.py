from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from urllib.parse import quote
from stencil_generator import (
    generate_stencil_geometry,
    generate_preview_image,
    generate_svg,
    calculate_optimal_plate_size,
    calculate_font_for_plate,
    get_supported_characters,
)

app = FastAPI(title="3D Stencil Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FONT_PATH = Path(__file__).parent / "fonts" / "AllertaStencil-Regular.ttf"


def _check_font():
    if not FONT_PATH.exists():
        raise HTTPException(status_code=500, detail="Font file not found.")


class StencilRequest(BaseModel):
    text: str
    width: float = 100.0
    height: float = 50.0
    thickness: float = 0.8
    font_size: float = 40.0
    margin: float = 10.0
    hanging_hole: bool = False
    hole_diameter: float = 5.0
    corner_radius: float = 0.0


class DimensionsRequest(BaseModel):
    text: str
    font_size: float = 40.0
    margin: float = 10.0


class FitTextRequest(BaseModel):
    text: str
    width: float
    height: float
    margin: float = 10.0


@app.get("/")
def root():
    return {"message": "3D Stencil Generator API"}


@app.get("/supported-characters")
def supported_characters():
    """Return the set of characters the stencil font can render."""
    _check_font()
    chars = get_supported_characters(str(FONT_PATH))
    return {"characters": chars}


@app.post("/calculate-dimensions")
async def calculate_dimensions(request: DimensionsRequest):
    """Calculate optimal plate dimensions for given text and font size."""
    _check_font()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        width, height = calculate_optimal_plate_size(
            text=request.text.strip(),
            font_path=str(FONT_PATH),
            font_size=request.font_size,
            margin=request.margin,
        )
        return {"width": width, "height": height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fit-text")
async def fit_text(request: FitTextRequest):
    """Calculate optimal font size to fit text within given plate dimensions."""
    _check_font()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        font_size = calculate_font_for_plate(
            text=request.text.strip(),
            font_path=str(FONT_PATH),
            width=request.width,
            height=request.height,
            margin=request.margin,
        )
        return {"font_size": font_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preview")
async def preview_stencil(request: StencilRequest):
    """Generate a 2D preview image of the stencil."""
    _check_font()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        image_bytes = generate_preview_image(
            text=request.text.strip(),
            font_path=str(FONT_PATH),
            font_size=request.font_size,
            width=request.width,
            height=request.height,
            margin=request.margin,
            hanging_hole=request.hanging_hole,
            hole_diameter=request.hole_diameter,
            corner_radius=request.corner_radius,
        )
        return Response(content=image_bytes, media_type="image/png",
                        headers={"Cache-Control": "no-cache"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-stl")
async def generate_stl(request: StencilRequest):
    """Generate a 3D printable STL file."""
    _check_font()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        mesh = generate_stencil_geometry(
            text=request.text.strip(),
            font_path=str(FONT_PATH),
            font_size=request.font_size,
            width=request.width,
            height=request.height,
            margin=request.margin,
            thickness=request.thickness,
            hanging_hole=request.hanging_hole,
            hole_diameter=request.hole_diameter,
            corner_radius=request.corner_radius,
        )
        stl_bytes = mesh.export(file_type="stl")
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in request.text.strip())
        if not safe_name:
            safe_name = "stencil"
        # Use RFC 5987 encoding for broad browser compatibility
        encoded_name = quote(f"stencil_{safe_name}.stl")
        return Response(
            content=stl_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=\"stencil_{safe_name}.stl\"; filename*=UTF-8''{encoded_name}",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-svg")
async def generate_svg_endpoint(request: StencilRequest):
    """Generate an SVG file with laser-cutter-ready red hairline cut lines."""
    _check_font()
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        svg_str = generate_svg(
            text=request.text.strip(),
            font_path=str(FONT_PATH),
            font_size=request.font_size,
            width=request.width,
            height=request.height,
            margin=request.margin,
            hanging_hole=request.hanging_hole,
            hole_diameter=request.hole_diameter,
            corner_radius=request.corner_radius,
        )
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in request.text.strip())
        if not safe_name:
            safe_name = "stencil"
        encoded_name = quote(f"stencil_{safe_name}.svg")
        return Response(
            content=svg_str,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=\"stencil_{safe_name}.svg\"; filename*=UTF-8''{encoded_name}",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

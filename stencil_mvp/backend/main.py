from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from stencil_generator import generate_stencil_geometry, generate_preview_image

app = FastAPI(title="3D Stencil Generator API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StencilRequest(BaseModel):
    text: str
    width: float = 100.0  # mm
    height: float = 50.0  # mm
    thickness: float = 0.8  # mm
    font_size: float = 40.0
    margin: float = 10.0


@app.get("/")
def root():
    return {"message": "3D Stencil Generator API"}


@app.post("/preview")
async def preview_stencil(request: StencilRequest):
    """
    Generate a 2D preview image of the stencil from above.
    """
    try:
        # Validate text input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get font path (relative to this file)
        font_path = Path(__file__).parent / "fonts" / "AllertaStencil-Regular.ttf"
        
        if not font_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Font file not found at {font_path}. Please ensure the font file is in the fonts/ directory."
            )
        
        # Generate preview image
        image_bytes = generate_preview_image(
            text=request.text.strip(),
            font_path=str(font_path),
            font_size=request.font_size,
            width=request.width,
            height=request.height,
            margin=request.margin
        )
        
        # Return as PNG image
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache"
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")


@app.post("/generate-stl")
async def generate_stl(request: StencilRequest):
    """
    Generate a 3D printable STL file from text input.
    """
    try:
        # Validate text input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get font path (relative to this file)
        font_path = Path(__file__).parent / "fonts" / "AllertaStencil-Regular.ttf"
        
        if not font_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Font file not found at {font_path}. Please ensure the font file is in the fonts/ directory."
            )
        
        # Generate the mesh
        mesh = generate_stencil_geometry(
            text=request.text.strip(),
            font_path=str(font_path),
            font_size=request.font_size,
            width=request.width,
            height=request.height,
            margin=request.margin,
            thickness=request.thickness
        )
        
        # Export to STL bytes
        stl_bytes = mesh.export(file_type="stl")
        
        # Return as downloadable file
        return Response(
            content=stl_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="stencil_{request.text.strip()}.stl"'
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating stencil: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


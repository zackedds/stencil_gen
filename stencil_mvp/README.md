# 3D Printable Stencil Generator MVP

A web-based tool to generate 3D printable STL files for spray painting stencils. Type a name or text, adjust settings, and download a ready-to-print STL file.

## Features

- **Text Input**: Enter any text to generate a stencil
- **Customizable Settings**: Adjust plate dimensions, thickness, font size, and margins
- **Stencil Font**: Uses Allerta Stencil font to prevent letter "islands" from falling out
- **Direct STL Download**: Get your 3D printable file instantly

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **3D Processing**: Trimesh, Shapely, Matplotlib

## Setup Instructions

### Prerequisites

- Python 3.8+ 
- Node.js 16+ and npm

### Backend Setup

**Quick Setup (Recommended):**

1. Navigate to the backend directory:
```bash
cd stencil_mvp/backend
```

2. Run the setup script (automatically handles everything):
```bash
./setup.sh
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Start the FastAPI server:
```bash
python main.py
```

**Manual Setup:**

1. Install GEOS (required for Shapely):
```bash
brew install geos
```

2. Navigate to the backend directory:
```bash
cd stencil_mvp/backend
```

3. Create a virtual environment with Python 3.11 (recommended for better wheel support):
```bash
python3.11 -m venv venv
# Or use python3.12 if 3.11 is not available
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Set environment variables for GEOS (macOS):
```bash
export GEOS_CONFIG=/opt/homebrew/bin/geos-config
export CPPFLAGS="-I/opt/homebrew/include"
export LDFLAGS="-L/opt/homebrew/lib"
```

5. Upgrade pip and install dependencies:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

6. Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd stencil_mvp/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Start both the backend and frontend servers
2. Open `http://localhost:5173` in your browser
3. Enter your text (e.g., "ALEX")
4. Adjust the sliders for plate dimensions, thickness, font size, and margin
5. Click "Download STL" to generate and download your 3D printable file
6. Print the STL file on your 3D printer and use it for spray painting!

## Project Structure

```
stencil_mvp/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── stencil_generator.py # Core geometry generation logic
│   ├── fonts/               # Font files directory
│   │   └── AllertaStencil-Regular.ttf
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   └── App.css          # Styles
│   └── package.json         # Node dependencies
└── README.md
```

## API Endpoint

### POST `/generate-stl`

Generates a 3D STL file from text input.

**Request Body:**
```json
{
  "text": "ALEX",
  "width": 100.0,
  "height": 50.0,
  "thickness": 0.8,
  "font_size": 40.0,
  "margin": 10.0
}
```

**Response:** STL file (binary)

## Notes

- The tool uses a stencil font to ensure letters like 'O', 'A', and 'P' remain connected
- Recommended thickness: 0.8mm (flexible but sturdy)
- The generated STL files are ready for 3D printing
- No database or file storage - files are generated on-demand

## Troubleshooting

### Dependency Installation Issues

**Problem: `geos_c.h` file not found (Shapely build error)**
- **Solution**: Install GEOS via Homebrew: `brew install geos`
- Then set environment variables before installing:
  ```bash
  export GEOS_CONFIG=/opt/homebrew/bin/geos-config
  export CPPFLAGS="-I/opt/homebrew/include"
  export LDFLAGS="-L/opt/homebrew/lib"
  ```

**Problem: Rust not found (pydantic-core build error)**
- **Solution**: Use Python 3.11 or 3.12 instead of 3.14 (better pre-built wheel support)
- Recreate venv: `rm -rf venv && python3.11 -m venv venv`

**Problem: ModuleNotFoundError after installation**
- **Solution**: Make sure you've activated the virtual environment: `source venv/bin/activate`

### Runtime Issues

- **Font not found error**: Ensure `AllertaStencil-Regular.ttf` is in `backend/fonts/`
- **CORS errors**: Make sure the backend is running and CORS is enabled
- **Import errors**: Verify all Python dependencies are installed correctly


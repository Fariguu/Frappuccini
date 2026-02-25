import geopandas as gpd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default path for the Shapefile in the apps/backend/data directory
SHAPEFILE_PATH = os.getenv("SHAPEFILE_PATH", os.path.join(os.path.dirname(__file__), "data", "Stradario.shp"))

@app.get("/api")
async def root():
    return {"message": "Hello from FastAPI"}

@app.get("/api/stradario")
async def get_stradario():
    if not os.path.exists(SHAPEFILE_PATH):
        return {"error": f"Shapefile not found at {SHAPEFILE_PATH}. Please provide the correct path."}
    
    try:
        # Load Shapefile
        gdf = gpd.read_file(SHAPEFILE_PATH, engine="pyogrio")
        
        # Convert CRS to WGS84 for web maps
        gdf = gdf.to_crs(epsg=4326)
        
        # Convert to GeoJSON
        return json.loads(gdf.to_json())
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from the backend!"}

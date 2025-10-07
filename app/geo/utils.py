from typing import Dict, List, Any, Optional
from geoalchemy2.shape import to_shape
from shapely.geometry import Point, Polygon, mapping
from shapely.geometry.base import BaseGeometry
import json


def geometry_to_geojson(geometry) -> Optional[Dict[str, Any]]:
    """
    Convert a PostGIS geometry to GeoJSON format
    """
    if geometry is None:
        return None
    
    try:
        # Convert WKB to Shapely geometry
        shapely_geom = to_shape(geometry)
        return mapping(shapely_geom)
    except Exception as e:
        print(f"Error converting geometry to GeoJSON: {e}")
        return None


def point_to_geojson(lat: float, lng: float) -> Dict[str, Any]:
    """
    Create a GeoJSON point from latitude and longitude
    """
    point = Point(lng, lat)  # Note: GeoJSON uses [lng, lat] order
    return mapping(point)


def polygon_to_geojson(coordinates: List[List[float]]) -> Dict[str, Any]:
    """
    Create a GeoJSON polygon from coordinate list
    """
    # Ensure the polygon is properly closed (first and last coordinates are the same)
    if coordinates and coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    
    polygon = Polygon(coordinates)
    return mapping(polygon)


def create_geojson_feature(
    geometry: Dict[str, Any], 
    properties: Optional[Dict[str, Any]] = None,
    feature_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a GeoJSON feature with geometry and properties
    """
    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties or {}
    }
    
    if feature_id is not None:
        feature["id"] = feature_id
    
    return feature


def create_geojson_feature_collection(
    features: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a GeoJSON feature collection
    """
    return {
        "type": "FeatureCollection",
        "features": features
    }


def validate_geojson_polygon(geojson_data: Dict[str, Any]) -> bool:
    """
    Validate that a GeoJSON represents a valid polygon with correct ring orientation
    """
    try:
        if geojson_data.get("type") != "Polygon":
            return False
        
        coordinates = geojson_data.get("coordinates")
        if not coordinates:
            return False
        
        # For a valid polygon:
        # 1. It should have at least one ring (exterior)
        if len(coordinates) < 1:
            return False
        
        # 2. Each ring should be a list of coordinates
        for ring in coordinates:
            if not isinstance(ring, list) or len(ring) < 4:
                return False  # A ring must have at least 4 points (closed)
            
            # 3. First and last coordinates of each ring should be the same (closed ring)
            if ring[0] != ring[-1]:
                return False
        
        # 4. Validate using Shapely
        polygon = Polygon(coordinates[0], holes=coordinates[1:] if len(coordinates) > 1 else [])
        return polygon.is_valid
    
    except Exception:
        return False


def validate_geojson_point(geojson_data: Dict[str, Any]) -> bool:
    """
    Validate that a GeoJSON represents a valid point
    """
    try:
        if geojson_data.get("type") != "Point":
            return False
        
        coordinates = geojson_data.get("coordinates")
        if not coordinates or len(coordinates) != 2:
            return False
        
        lng, lat = coordinates[0], coordinates[1]
        
        # Basic coordinate validation
        if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
            return False
        
        if lat < -90 or lat > 90 or lng < -180 or lng > 180:
            return False
        
        return True
    
    except Exception:
        return False
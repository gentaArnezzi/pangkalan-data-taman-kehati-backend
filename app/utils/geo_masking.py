from __future__ import annotations
import hashlib
from typing import Tuple, Optional, Dict, Any

# ≈ meters per degree at equator (good enough for masking)
_M_PER_DEG = 111_320.0

_ADMIN_ROLES = {"super_admin", "admin_taman"}

def _jitter_deg(resource_id: Optional[str], max_jitter_m: float) -> Tuple[float, float]:
    """
    Deterministic tiny offset in degrees based on resource_id.
    If no resource_id, return zero jitter (caller may round instead).
    """
    if not resource_id:
        return 0.0, 0.0
    h = hashlib.sha256(resource_id.encode("utf-8")).digest()
    # map two bytes to [-1, 1]
    jx = (int.from_bytes(h[0:2], "big") / 65535.0) * 2 - 1
    jy = (int.from_bytes(h[2:4], "big") / 65535.0) * 2 - 1
    max_deg = max_jitter_m / _M_PER_DEG
    return jx * max_deg, jy * max_deg

def mask_coordinates(
    lat: float,
    lon: float,
    role: str,
    resource_id: Optional[str] = None,
    precision: int = 5,
    max_jitter_m: float = 30.0,
) -> Tuple[float, float]:
    """
    If role is admin/super_admin -> return original.
    Else -> apply small deterministic jitter if resource_id given; otherwise round.
    """
    if role in _ADMIN_ROLES:
        return lat, lon

    jlat, jlon = _jitter_deg(resource_id, max_jitter_m)
    if jlat == 0.0 and jlon == 0.0:
        # fallback: simple rounding mask (~1.1m per 5th decimal)
        return round(lat, precision), round(lon, precision)
    return round(lat + jlat, precision), round(lon + jlon, precision)

def mask_geojson_point(
    feature: Dict[str, Any],
    role: str,
    resource_id: Optional[str] = None,
    precision: int = 5,
    max_jitter_m: float = 30.0,
) -> Dict[str, Any]:
    """
    Mask a GeoJSON Feature with Point geometry in-place-ish and return it.
    """
    if not feature or feature.get("type") != "Feature":
        return feature
    geom = feature.get("geometry") or {}
    if geom.get("type") != "Point":
        return feature
    coords = geom.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return feature
    lon, lat = float(coords[0]), float(coords[1])
    mlat, mlon = mask_coordinates(lat, lon, role, resource_id, precision, max_jitter_m)
    feature = dict(feature)  # shallow copy
    feature["geometry"] = dict(geom)
    feature["geometry"]["coordinates"] = [mlon, mlat]
    return feature

# --- Role-based masking presets (exported) ---
# precision: decimal places to round lat/lon (5 ≈ ~1.1 m at equator)
# max_jitter_m: max deterministic jitter radius in meters
PRECISION_LEVELS = {
    "super_admin": {"precision": 7, "max_jitter_m": 0.0},   # effectively raw
    "admin_taman": {"precision": 7, "max_jitter_m": 0.0},   # effectively raw
    "viewer":      {"precision": 5, "max_jitter_m": 30.0},  # ~1m rounding + ≤30m jitter
    # fallback/default role
    "*":           {"precision": 5, "max_jitter_m": 30.0},
}

def mask_with_profile(
    lat: float,
    lon: float,
    role: str,
    resource_id: str | None = None,
) -> tuple[float, float]:
    prof = PRECISION_LEVELS.get(role) or PRECISION_LEVELS["*"]
    return mask_coordinates(
        lat, lon, role,
        resource_id=resource_id,
        precision=prof["precision"],
        max_jitter_m=prof["max_jitter_m"],
    )

from __future__ import annotations
from typing import Any, Dict, Iterable, List, Mapping

def _get(o: Any, *names: str, default: Any = None):
    """Safe getattr/lookup across possible attr or dict keys."""
    for n in names:
        if o is None: 
            return default
        # attr
        if hasattr(o, n):
            val = getattr(o, n)
            if val is not None:
                return val
        # dict-like
        if isinstance(o, Mapping) and n in o and o[n] is not None:
            return o[n]
    return default

def model_to_geojson_collection(models: Iterable[Any]) -> Dict[str, Any]:
    """
    Convert iterable of KoleksiTumbuhan-like objects to a GeoJSON FeatureCollection.
    Expects lat/lon on either taman or asal fields; uses taman first, falls back to asal.
    """
    features: List[Dict[str, Any]] = []
    for m in models:
        # try taman coords first, then asal coords
        lat = _get(m, "latitude_taman", "latitude_asal", "latitude")
        lon = _get(m, "longitude_taman", "longitude_asal", "longitude")
        if lat is None or lon is None:
            # skip features without coordinates
            continue

        props = {
            "id": _get(m, "id"),
            "collectionNumber": _get(m, "nomor_koleksi"),
            "scientificName": _get(m, "nama_ilmiah"),
            "genus": _get(m, "genus"),
            "specificEpithet": _get(m, "spesies"),
            "vernacularName": _get(m, "nama_umum_nasional") or _get(m, "nama_lokal_daerah"),
            "gardenId": _get(m, "taman_kehati_id"),
            "zoneId": _get(m, "zona_id"),
            "elevation": _get(m, "ketinggian_taman", "ketinggian_asal"),
            "endemicStatus": _get(m, "status_endemik"),
        }

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            "properties": {k: v for k, v in props.items() if v is not None},
        })

    return {"type": "FeatureCollection", "features": features}

def create_dwc_export(models: Iterable[Any]) -> List[Dict[str, Any]]:
    """
    Produce a minimal Darwin Core export (DwC-A compatible tabular rows as list of dicts).
    Maps common fields if present; missing fields are left out.
    """
    rows: List[Dict[str, Any]] = []
    for m in models:
        row = {
            # Core identification
            "occurrenceID": _get(m, "id"),
            "scientificName": _get(m, "nama_ilmiah"),
            "genus": _get(m, "genus"),
            "specificEpithet": _get(m, "spesies"),
            "taxonAuthor": _get(m, "author"),

            # Vernacular / local names
            "vernacularName": _get(m, "nama_umum_nasional") or _get(m, "nama_lokal_daerah"),

            # Event
            "eventDate": _get(m, "tanggal_pengumpulan") or _get(m, "tanggal_penanaman"),
            "recordNumber": _get(m, "nomor_koleksi"),
            "recordedBy": _get(m, "created_by"),

            # Location (taman preferred, fallback asal)
            "decimalLatitude": _get(m, "latitude_taman", "latitude_asal"),
            "decimalLongitude": _get(m, "longitude_taman", "longitude_asal"),
            "verbatimElevation": _get(m, "ketinggian_taman", "ketinggian_asal"),
            "locality": _get(m, "asal_kampung"),
            "island": _get(m, "pulau"),
            "stateProvince": _get(m, "asal_provinsi_nama", "provinsi_nama"),
            "county": _get(m, "asal_kabupaten_nama", "kabupaten_nama"),
            "municipality": _get(m, "asal_kecamatan_nama", "kecamatan_nama"),
            "verbatimLocality": _get(m, "asal_desa_nama", "desa_nama"),

            # Project specifics
            "institutionCode": "TamanKehati",
            "collectionCode": _get(m, "taman_kehati_id"),
        }
        # drop Nones
        rows.append({k: v for k, v in row.items() if v is not None})
    return rows

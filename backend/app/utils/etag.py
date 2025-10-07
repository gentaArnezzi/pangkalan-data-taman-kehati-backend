"""
ETag utilities for HTTP caching and optimistic concurrency control
"""
import hashlib
from typing import Any, Union
from datetime import datetime


def generate_etag(resource: Any, include_timestamp: bool = True) -> str:
    """
    Generate an ETag for a resource based on its content and optionally timestamp
    """
    if hasattr(resource, 'updated_at') and include_timestamp:
        # For database models with updated_at field
        timestamp_str = str(resource.updated_at)
        resource_str = f"{str(resource)}{timestamp_str}"
    elif include_timestamp:
        # For other resources, use current time
        timestamp_str = datetime.utcnow().isoformat()
        resource_str = f"{str(resource)}{timestamp_str}"
    else:
        resource_str = str(resource)
    
    # Create a hash of the resource string
    etag_hash = hashlib.md5(resource_str.encode('utf-8')).hexdigest()
    return f'"{etag_hash}"'


def validate_if_match(request_etag: str, current_etag: str) -> bool:
    """
    Validate If-Match header against current ETag for optimistic concurrency
    """
    # Remove quotes from both etags if present
    if request_etag.startswith('"') and request_etag.endswith('"'):
        request_etag = request_etag[1:-1]
    if current_etag.startswith('"') and current_etag.endswith('"'):
        current_etag = current_etag[1:-1]
    
    return request_etag == current_etag or request_etag == "*"
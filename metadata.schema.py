#!/usr/bin/env python3
"""
PanQPlex Metadata Schemas
Defines metadata keys, roles, and their properties
"""

from typing import Dict, Any
from enum import Enum
from typing import List

# Configuration
AUTOPREFIX_METADATA_KEY_NAMES = False

# Role hierarchy with permission levels
ROLES = {
    "noone": {
        "level": float('inf'),
        "label": "No One",
        "description": "Locked, no editing allowed"
    },
    "god": {
        "level": 99,
        "label": "God",
        "description": "Full system access"
    },
    "system": {
        "level": 69,
        "label": "System",
        "description": "System administration access"
    },
    "sync": {
        "level": 42,
        "label": "Sync",
        "description": "Synchronization process access"
    },
    "user": {
        "level": 11,
        "label": "User",
        "description": "Regular user access"
    },
    "mouse": {
        "level": 2,
        "label": "Mouse",
        "description": "Minimal access level"
    }
}

# Intrinsic data - derived from video file itself, read-only
INTRINSIC_DATA = {
    "duration": {
        "label": "Duration",
        "key": "duration",
        "editable_by": "noone",
        "stub": "0.0"
    },
    "size": {
        "label": "File Size",
        "key": "size",
        "editable_by": "noone",
        "stub": "0"
    },
    "bit_rate": {
        "label": "Bit Rate",
        "key": "bit_rate",
        "editable_by": "noone",
        "stub": "0"
    },
    "format_name": {
        "label": "Format",
        "key": "format_name",
        "editable_by": "noone",
        "stub": "unknown"
    },
    "format_long_name": {
        "label": "Format Description",
        "key": "format_long_name",
        "editable_by": "noone",
        "stub": "unknown"
    },
    "width": {
        "label": "Width",
        "key": "width",
        "editable_by": "noone",
        "stub": "0"
    },
    "height": {
        "label": "Height",
        "key": "height",
        "editable_by": "noone",
        "stub": "0"
    },
    "codec_name": {
        "label": "Codec",
        "key": "codec_name",
        "editable_by": "noone",
        "stub": "unknown"
    },
    "codec_type": {
        "label": "Stream Type",
        "key": "codec_type",
        "editable_by": "noone",
        "stub": "unknown"
    },
    "filename": {
        "label": "Filename",
        "key": "filename",
        "editable_by": "noone",
        "stub": "unknown"
    },
    "filepath": {
        "label": "File Path",
        "key": "filepath",
        "editable_by": "noone",
        "stub": "unknown"
    }
}

# PQPCU - PanQPlex Core User metadata
PQPCU = {
    "title": {
        "label": "Title",
        "key": "title",
        "editable_by": "user",
        "stub": "Untitled"
    },
    "description": {
        "label": "Description",
        "key": "comment",
        "editable_by": "user",
        "stub": ""
    },
    "tags": {
        "label": "Tags",
        "key": "keywords",
        "editable_by": "user",
        "stub": ""
    },
    "category": {
        "label": "Category",
        "key": "genre",
        "editable_by": "user",
        "stub": ""
    },
    "artist": {
        "label": "Artist",
        "key": "artist",
        "editable_by": "user",
        "stub": ""
    },
    "album": {
        "label": "Album",
        "key": "album",
        "editable_by": "user",
        "stub": ""
    },
    "date": {
        "label": "Date",
        "key": "date",
        "editable_by": "user",
        "stub": ""
    },
    "copyright": {
        "label": "Copyright",
        "key": "copyright",
        "editable_by": "user",
        "stub": ""
    }
}

# PQPISA - PanQPlex Internal System Administration
PQPISA = {
    "upload_state": {
        "label": "Upload State",
        "key": "PQP:upload_state",
        "editable_by": "system",
        "stub": "queued"
    },
    "upload_progress": {
        "label": "Upload Progress",
        "key": "PQP:upload_progress",
        "editable_by": "system",
        "stub": "0"
    },
    "file_uuid": {
        "label": "File UUID",
        "key": "PQP:file_uuid",
        "editable_by": "system",
        "stub": "mock"
    },
    "last_sync": {
        "label": "Last Sync",
        "key": "PQP:last_sync",
        "editable_by": "system",
        "stub": "never"
    },
    "platform_id": {
        "label": "Platform ID",
        "key": "PQP:platform_id",
        "editable_by": "system",
        "stub": ""
    },
    "platform_url": {
        "label": "Platform URL",
        "key": "PQP:platform_url",
        "editable_by": "system",
        "stub": ""
    },
    "upload_user": {
        "label": "Upload User",
        "key": "PQP:upload_user",
        "editable_by": "user",
        "stub": "default"
    },
    "sync_hash": {
        "label": "Sync Hash",
        "key": "PQP:sync_hash",
        "editable_by": "system",
        "stub": ""
    },
    "retry_count": {
        "label": "Retry Count",
        "key": "PQP:retry_count",
        "editable_by": "system",
        "stub": "0"
    },
    "error_message": {
        "label": "Error Message",
        "key": "PQP:error_message",
        "editable_by": "system",
        "stub": ""
    }
}

def get_all_metadata_keys() -> Dict[str, Dict[str, Any]]:
    """Get all metadata keys combined"""
    return {**INTRINSIC_DATA, **PQPCU, **PQPISA}

def get_role_level(role: str) -> float:
    """Get role permission level"""
    return ROLES.get(role, {}).get("level", 0)

def can_edit_key(key: str, cardinal: str) -> bool:
    """Check if cardinal can edit key based on role hierarchy"""
    all_keys = get_all_metadata_keys()
    
    if key not in all_keys:
        return True  # Unknown keys are editable
    
    key_role = all_keys[key]["editable_by"]
    cardinal_level = get_role_level(cardinal)
    required_level = get_role_level(key_role)
    
    return cardinal_level >= required_level

def get_editable_keys(cardinal: str) -> Dict[str, Dict[str, Any]]:
    """Get keys editable by specific cardinal"""
    all_keys = get_all_metadata_keys()
    editable = {}
    
    for key, props in all_keys.items():
        if can_edit_key(key, cardinal):
            editable[key] = props
    
    return editable

def get_blacklisted_keys(cardinal: str) -> List[str]:
    """Get keys that are blacklisted for cardinal"""
    all_keys = get_all_metadata_keys()
    blacklisted = []
    
    for key, props in all_keys.items():
        if not can_edit_key(key, cardinal):
            blacklisted.append(key)
    
    return blacklisted

def normalize_key(key: str) -> str:
    """Normalize key to schema key"""
    # Remove PQP prefix for comparison
    if key.startswith("PQP:"):
        clean_key = key[4:]
    else:
        clean_key = key
    
    # Check if it matches any schema key
    all_keys = get_all_metadata_keys()
    for schema_key, props in all_keys.items():
        if (clean_key == schema_key or 
            key == props["key"] or 
            clean_key == props["key"]):
            return schema_key
    
    return key  # Return original if no match found

def is_intrinsic_key(key: str) -> bool:
    """Check if key is intrinsic data"""
    norm_key = normalize_key(key)
    return norm_key in INTRINSIC_DATA
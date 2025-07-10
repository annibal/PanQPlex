#!/usr/bin/env python3
"""
PanQPlex Format Helper
Handles all formatting operations for display
"""

import hashlib
from typing import Any

from status_enums import FileStatus, UploadState, get_status_display, get_upload_display

def format_duration(seconds: float) -> str:
    """Format duration as MM:SS or H:MM:SS"""
    if not seconds:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"

def format_file_size(bytes_size: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def format_progress(progress: Any) -> str:
    """Format upload progress with emoji"""
    try:
        prog = int(progress)
        if prog == 0:
            return "🔜   0%"
        elif prog == 100:
            return "✅ 100%"
        elif prog < 100:
            return f"📤 {prog:3d}%"
        else:
            return f"⚠️ {prog:3d}%"
    except (ValueError, TypeError):
        return "❓   ?%"

def format_file_status(status: FileStatus) -> str:
    """Format file status with emoji"""
    display = get_status_display(status)
    return f"{display['emoji']} {display['label']}"

def format_upload_state(state: UploadState, progress: int = 0) -> str:
    """Format upload state with progress"""
    display = get_upload_display(state, progress)
    return display["formatted"]

def format_upload_status(status: str) -> str:
    """Format upload status with emoji (legacy)"""
    # Convert string to enum for consistency
    try:
        if status in ['queued', 'queued_new']:
            return format_upload_state(UploadState.QUEUED)
        elif status == 'uploading':
            return format_upload_state(UploadState.UPLOADING)
        elif status in ['completed', 'finished']:
            return format_upload_state(UploadState.COMPLETED)
        elif status == 'error':
            return format_upload_state(UploadState.ERROR)
        elif status == 'paused':
            return format_upload_state(UploadState.PAUSED)
        elif status in ['changed', 'queued_edit']:
            return format_upload_state(UploadState.RETRY)
        else:
            return f"❓ {status}"
    except Exception:
        return f"❓ {status}"

def format_uuid(file_path: str) -> str:
    """Generate and format UUID hash for file"""
    hasher = hashlib.sha256()
    hasher.update(str(file_path).encode())
    return hasher.hexdigest()[:4].upper()

def format_time_ago(timestamp: str) -> str:
    """Format timestamp as time ago (placeholder)"""
    if not timestamp or timestamp == "never":
        return "never"
    return timestamp  # Simplified for now

def format_metadata_value(key: str, value: Any) -> str:
    """Format metadata value based on key type"""
    if value is None:
        return ""
    
    # Special formatting based on key
    formatters = {
        'duration': format_duration,
        'length': format_duration,
        'size': format_file_size,
        'upload_progress': format_progress,
        'upload_state': lambda x: format_upload_status(str(x)),
        'last_sync': format_time_ago,
        'file_uuid': format_uuid
    }
    
    formatter = formatters.get(key)
    if formatter:
        return formatter(value)
    
    return str(value)
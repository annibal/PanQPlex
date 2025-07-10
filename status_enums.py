#!/usr/bin/env python3
"""
PanQPlex Status Enums
Centralized status definitions for the entire project
"""

from enum import Enum
from typing import Dict, Any

class FileStatus(Enum):
    """File status enumeration matching list_of_all_statuses.py"""
    UNDEFINED = "undefined"
    ACKNOWLEDGED = "acknowledged" 
    PROVISIONED = "provisioned"
    QUEUED_NEW = "queued_new"
    UPLOADING = "uploading"
    FINISHED = "finished"
    QUEUED_EDIT = "queued_edit"
    HINDERED = "hindered"

class UploadState(Enum):
    """Upload states for tracking progress"""
    QUEUED = "queued"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    RETRY = "retry"
    PAUSED = "paused"

# Status display configuration
STATUS_DISPLAY = {
    FileStatus.UNDEFINED: {
        "emoji": "❓",
        "label": "Undefined",
        "description": "File not yet processed by PanQPlex"
    },
    FileStatus.ACKNOWLEDGED: {
        "emoji": "👀", 
        "label": "Acknowledged",
        "description": "File prepared by PanQPlex with default metadata"
    },
    FileStatus.PROVISIONED: {
        "emoji": "✍️",
        "label": "Provisioned", 
        "description": "Metadata edited but not ready for upload"
    },
    FileStatus.QUEUED_NEW: {
        "emoji": "⭐",
        "label": "Queued (New)",
        "description": "Ready for first upload"
    },
    FileStatus.UPLOADING: {
        "emoji": "📤",
        "label": "Uploading",
        "description": "Currently being uploaded or upload interrupted"
    },
    FileStatus.FINISHED: {
        "emoji": "🆗",
        "label": "Finished",
        "description": "Successfully uploaded and synchronized"
    },
    FileStatus.QUEUED_EDIT: {
        "emoji": "🔜",
        "label": "Queued (Edit)",
        "description": "Local changes need to be synced to remote"
    },
    FileStatus.HINDERED: {
        "emoji": "⚠️",
        "label": "Hindered",
        "description": "Error requiring human intervention"
    }
}

# Upload state display configuration
UPLOAD_DISPLAY = {
    UploadState.QUEUED: {
        "emoji": "🔜",
        "label": "Queued",
        "progress_format": "🔜   0%"
    },
    UploadState.UPLOADING: {
        "emoji": "📤", 
        "label": "Uploading",
        "progress_format": "📤 {progress:3d}%"
    },
    UploadState.PROCESSING: {
        "emoji": "⚙️",
        "label": "Processing", 
        "progress_format": "⚙️ PROC"
    },
    UploadState.COMPLETED: {
        "emoji": "✅",
        "label": "Completed",
        "progress_format": "✅ 100%"
    },
    UploadState.ERROR: {
        "emoji": "❌",
        "label": "Error",
        "progress_format": "❌ ERR"
    },
    UploadState.CANCELLED: {
        "emoji": "🚫",
        "label": "Cancelled", 
        "progress_format": "🚫 CANCEL"
    },
    UploadState.RETRY: {
        "emoji": "🔄",
        "label": "Retry",
        "progress_format": "🔄 RETRY"
    },
    UploadState.PAUSED: {
        "emoji": "⏸️",
        "label": "Paused",
        "progress_format": "⏸️ PAUSE"
    }
}

def get_status_display(status: FileStatus) -> Dict[str, str]:
    """Get display information for file status"""
    return STATUS_DISPLAY.get(status, {
        "emoji": "❓",
        "label": str(status.value).title(),
        "description": "Unknown status"
    })

def get_upload_display(state: UploadState, progress: int = 0) -> Dict[str, str]:
    """Get display information for upload state"""
    display = UPLOAD_DISPLAY.get(state, {
        "emoji": "❓",
        "label": str(state.value).title(),
        "progress_format": "❓ {progress:3d}%"
    })
    
    # Format progress if template contains placeholder
    if "{progress" in display["progress_format"]:
        display["formatted"] = display["progress_format"].format(progress=progress)
    else:
        display["formatted"] = display["progress_format"]
    
    return display

def format_status(status: FileStatus) -> str:
    """Format status for display"""
    display = get_status_display(status)
    return f"{display['emoji']} {display['label']}"

def format_upload_state(state: UploadState, progress: int = 0) -> str:
    """Format upload state with progress for display"""
    display = get_upload_display(state, progress)
    return display["formatted"]

def is_actionable_status(status: FileStatus) -> bool:
    """Check if status requires action during sync"""
    return status in [
        FileStatus.QUEUED_NEW,
        FileStatus.UPLOADING, 
        FileStatus.QUEUED_EDIT
    ]

def is_completed_status(status: FileStatus) -> bool:
    """Check if status represents completed state"""
    return status == FileStatus.FINISHED

def is_error_status(status: FileStatus) -> bool:
    """Check if status represents error state"""
    return status == FileStatus.HINDERED

def get_all_statuses() -> list[FileStatus]:
    """Get all available file statuses"""
    return list(FileStatus)

def get_all_upload_states() -> list[UploadState]:
    """Get all available upload states"""  
    return list(UploadState)

def status_from_string(status_str: str) -> FileStatus:
    """Convert string to FileStatus enum"""
    try:
        return FileStatus(status_str.lower())
    except ValueError:
        return FileStatus.UNDEFINED

def upload_state_from_string(state_str: str) -> UploadState:
    """Convert string to UploadState enum"""
    try:
        return UploadState(state_str.lower())
    except ValueError:
        return UploadState.QUEUED
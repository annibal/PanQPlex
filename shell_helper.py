#!/usr/bin/env python3
"""
PanQPlex Shell Helper
Handles file system operations and shell interactions
"""

import os
from pathlib import Path
from typing import List, Optional

def get_video_files_in_pwd() -> List[str]:
    """Get all video files in current working directory"""
    cwd = Path.cwd()
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v'}
    
    files = []
    for file_path in cwd.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            files.append(str(file_path))
    
    return sorted(files)

def file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return Path(file_path).exists()

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return Path(file_path).stat().st_size

def get_filename(file_path: str) -> str:
    """Get filename from path"""
    return Path(file_path).name

def ensure_directory_exists(dir_path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

def get_home_directory() -> str:
    """Get user home directory"""
    return str(Path.home())

def get_current_directory() -> str:
    """Get current working directory"""
    return str(Path.cwd())

def is_valid_media_file(file_path: str) -> bool:
    """Check if file is a valid media file"""
    if not file_exists(file_path):
        return False
    
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v'}
    return Path(file_path).suffix.lower() in video_extensions
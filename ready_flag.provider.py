#!/usr/bin/env python3
"""
PanQPlex Ready Flag Provider
Handles setting files as ready for upload
"""

from typing import List, Optional, Tuple
from pathlib import Path

from metadata.provider import MetadataProvider
from shell_helper import file_exists, is_valid_media_file

class ReadyFlagProvider:
    """Handles marking files as ready for upload"""
    
    def __init__(self):
        self.ready_flag_key = "ready_to_upload"
        self.cardinal = "user"
    
    def set_ready(self, file_path: str) -> bool:
        """Mark file as ready for upload"""
        if not self._validate_file(file_path):
            return False
        
        try:
            metadata_provider = MetadataProvider(file_path)
            return metadata_provider.set_metadata(self.ready_flag_key, "true", self.cardinal)
        except Exception:
            return False
    
    def unset_ready(self, file_path: str) -> bool:
        """Mark file as not ready for upload"""
        if not self._validate_file(file_path):
            return False
        
        try:
            metadata_provider = MetadataProvider(file_path)
            return metadata_provider.set_metadata(self.ready_flag_key, "false", self.cardinal)
        except Exception:
            return False
    
    def is_ready(self, file_path: str) -> bool:
        """Check if file is marked as ready for upload"""
        if not self._validate_file(file_path):
            return False
        
        try:
            metadata_provider = MetadataProvider(file_path)
            ready_value = metadata_provider.get_metadata(self.ready_flag_key)
            return ready_value and ready_value.lower() == "true"
        except Exception:
            return False
    
    def set_multiple_ready(self, file_paths: List[str]) -> List[Tuple[str, bool]]:
        """Mark multiple files as ready for upload"""
        results = []
        for file_path in file_paths:
            success = self.set_ready(file_path)
            results.append((file_path, success))
        return results
    
    def unset_multiple_ready(self, file_paths: List[str]) -> List[Tuple[str, bool]]:
        """Mark multiple files as not ready for upload"""
        results = []
        for file_path in file_paths:
            success = self.unset_ready(file_path)
            results.append((file_path, success))
        return results
    
    def get_ready_files(self, file_paths: List[str]) -> List[str]:
        """Get list of files marked as ready for upload"""
        ready_files = []
        for file_path in file_paths:
            if self.is_ready(file_path):
                ready_files.append(file_path)
        return ready_files
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file exists and is a valid media file"""
        return file_exists(file_path) and is_valid_media_file(file_path)

def set_file_ready(file_path: str) -> bool:
    """Convenience function to mark file as ready"""
    provider = ReadyFlagProvider()
    return provider.set_ready(file_path)

def unset_file_ready(file_path: str) -> bool:
    """Convenience function to mark file as not ready"""
    provider = ReadyFlagProvider()
    return provider.unset_ready(file_path)

def check_file_ready(file_path: str) -> bool:
    """Convenience function to check if file is ready"""
    provider = ReadyFlagProvider()
    return provider.is_ready(file_path)
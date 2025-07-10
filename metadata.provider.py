#!/usr/bin/env python3
"""
PanQPlex Metadata Provider
Handles metadata operations for individual files
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Import metadata schemas and status enums
from metadata.schemas import (
    INTRINSIC_DATA, PQPCU, PQPISA, AUTOPREFIX_METADATA_KEY_NAMES,
    get_all_metadata_keys, can_edit_key, 
    get_blacklisted_keys, normalize_key, is_intrinsic_key
)
from status_enums import FileStatus, UploadState

class MetadataOperation(Enum):
    DELETED = "D"
    ADDED = "A"
    CHANGED = "C"
    EQUAL = "E"

@dataclass
class MetadataDelta:
    key: str
    value: Any
    operation: MetadataOperation

class MetadataProvider:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # PanQPlex metadata prefix
        self.pqp_prefix = "PQP:"

    def _get_actual_key(self, key: str) -> str:
        """Get the actual key to use based on configuration"""
        if AUTOPREFIX_METADATA_KEY_NAMES and not key.startswith(self.pqp_prefix):
            return f"{self.pqp_prefix}{key}"
        return key

    def _run_ffprobe(self, show_format: bool = True, show_streams: bool = False) -> Dict[str, Any]:
        """Run ffprobe to get file metadata"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json'
        ]
        
        if show_format:
            cmd.append('-show_format')
        if show_streams:
            cmd.append('-show_streams')
            
        cmd.append(str(self.file_path))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFprobe failed: {e.stderr}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse FFprobe output: {e}")

    def _run_ffmpeg_metadata_update(self, metadata: Dict[str, Any]) -> bool:
        """Update file metadata using FFmpeg"""
        # Create temporary file
        temp_file = self.file_path.with_suffix('.tmp' + self.file_path.suffix)
        
        try:
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', str(self.file_path),
                '-c', 'copy',  # Copy streams without re-encoding
                '-map_metadata', '-1',  # Clear existing metadata
                '-y'  # Overwrite output
            ]
            
            # Add metadata parameters
            for key, value in metadata.items():
                if value is not None and value != "":
                    cmd.extend(['-metadata', f'{key}={value}'])
            
            cmd.append(str(temp_file))
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            # Replace original file with updated one
            temp_file.replace(self.file_path)
            return True
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _filter_editable_keys(self, metadata: Dict[str, Any], cardinal: str) -> Dict[str, Any]:
        """Filter metadata to only include keys editable by cardinal"""
        filtered = {}
        
        for key, value in metadata.items():
            norm_key = normalize_key(key)
            if can_edit_key(norm_key, cardinal):
                filtered[key] = value
        
        return filtered

    def get_all_metadata(self) -> Dict[str, Any]:
        """Get all metadata from file"""
        probe_data = self._run_ffprobe(show_format=True)
        
        if 'format' not in probe_data or 'tags' not in probe_data['format']:
            return {}
        
        return probe_data['format']['tags']

    def get_intrinsic_data(self) -> Dict[str, Any]:
        """Get intrinsic data derived from file"""
        probe_data = self._run_ffprobe(show_format=True, show_streams=True)
        
        intrinsic = {}
        
        if 'format' in probe_data:
            format_info = probe_data['format']
            intrinsic.update({
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', ''),
                'format_long_name': format_info.get('format_long_name', '')
            })
        
        if 'streams' in probe_data:
            # Get first video stream info
            for stream in probe_data['streams']:
                if stream.get('codec_type') == 'video':
                    intrinsic.update({
                        'width': stream.get('width', 0),
                        'height': stream.get('height', 0),
                        'codec_name': stream.get('codec_name', ''),
                        'codec_type': stream.get('codec_type', '')
                    })
                    break
        
        return intrinsic

    def get_file_status(self) -> FileStatus:
        """Get file upload status"""
        status_str = self.get_metadata("upload_state") or "undefined"
        return FileStatus(status_str.lower())

    def set_file_status(self, status: FileStatus, cardinal: str = "system") -> bool:
        """Set file upload status"""
        return self.set_metadata("upload_state", status.value, cardinal)

    def get_upload_state(self) -> UploadState:
        """Get upload state"""
        state_str = self.get_metadata("upload_state") or "queued"
        return UploadState(state_str.lower())

    def set_upload_state(self, state: UploadState, cardinal: str = "system") -> bool:
        """Set upload state"""
        return self.set_metadata("upload_state", state.value, cardinal)

    def get_metadata(self, key: str) -> Optional[Any]:
        """Get specific metadata value"""
        all_metadata = self.get_all_metadata()
        
        # Check direct key
        if key in all_metadata:
            return all_metadata[key]
        
        # If autoprefixing is enabled, also check PQP prefixed key
        if AUTOPREFIX_METADATA_KEY_NAMES:
            pqp_key = f"{self.pqp_prefix}{key}"
            if pqp_key in all_metadata:
                return all_metadata[pqp_key]
        
        return None

    def set_metadata(self, key: str, value: Any, cardinal: str = "user") -> bool:
        """Set specific metadata value"""
        # Check if key is editable by cardinal
        norm_key = normalize_key(key)
        if not can_edit_key(norm_key, cardinal):
            return False  # Silently ignore blacklisted keys
        
        current_metadata = self.get_all_metadata()
        
        # Determine the actual key to use
        actual_key = self._get_actual_key(key)
        
        # Update metadata
        current_metadata[actual_key] = str(value) if value is not None else ""
        
        return self._run_ffmpeg_metadata_update(current_metadata)

    def delete_metadata(self, key: str, cardinal: str = "user") -> bool:
        """Delete specific metadata key"""
        # Check if key is editable by cardinal
        norm_key = normalize_key(key)
        if not can_edit_key(norm_key, cardinal):
            return False  # Silently ignore blacklisted keys
        
        current_metadata = self.get_all_metadata()
        
        # Find and remove the key
        keys_to_remove = []
        
        # Check direct key
        if key in current_metadata:
            keys_to_remove.append(key)
        
        # If autoprefixing is enabled, also check PQP prefixed key
        if AUTOPREFIX_METADATA_KEY_NAMES:
            pqp_key = f"{self.pqp_prefix}{key}"
            if pqp_key in current_metadata:
                keys_to_remove.append(pqp_key)
        
        if not keys_to_remove:
            return False  # Key not found
        
        # Remove keys
        for key_to_remove in keys_to_remove:
            del current_metadata[key_to_remove]
        
        return self._run_ffmpeg_metadata_update(current_metadata)

    def compare_metadata(self, target_metadata: Dict[str, Any], cardinal: str = "user") -> List[MetadataDelta]:
        """Compare target metadata with file metadata and return delta"""
        # Filter target metadata to only include editable keys
        filtered_target = self._filter_editable_keys(target_metadata, cardinal)
        
        current_metadata = self.get_all_metadata()
        deltas = []
        
        # Normalize keys for comparison
        def normalize_key_local(key: str) -> str:
            if key.startswith(self.pqp_prefix):
                return key[len(self.pqp_prefix):]
            return key
        
        # Create normalized current metadata (only editable keys)
        normalized_current = {}
        for key, value in current_metadata.items():
            norm_key = normalize_key_local(key)
            if can_edit_key(norm_key, cardinal):
                normalized_current[norm_key] = value
        
        # Get all unique keys from filtered target
        all_keys = set(normalized_current.keys()) | set(filtered_target.keys())
        
        for key in all_keys:
            current_value = normalized_current.get(key)
            target_value = filtered_target.get(key)
            
            if current_value is None and target_value is not None:
                # Added
                deltas.append(MetadataDelta(key, target_value, MetadataOperation.ADDED))
            elif current_value is not None and target_value is None:
                # Deleted
                deltas.append(MetadataDelta(key, current_value, MetadataOperation.DELETED))
            elif current_value != target_value:
                # Changed
                deltas.append(MetadataDelta(key, target_value, MetadataOperation.CHANGED))
            else:
                # Equal
                deltas.append(MetadataDelta(key, current_value, MetadataOperation.EQUAL))
        
        return deltas

    def sync_metadata(self, target_metadata: Dict[str, Any], cardinal: str = "user") -> bool:
        """Sync file metadata to match target metadata"""
        # Filter target metadata to only include editable keys
        filtered_target = self._filter_editable_keys(target_metadata, cardinal)
        
        deltas = self.compare_metadata(filtered_target, cardinal)
        
        # Start with current metadata
        current_metadata = self.get_all_metadata()
        
        # Apply only editable changes
        for delta in deltas:
            if delta.operation == MetadataOperation.DELETED:
                # Remove the key
                keys_to_remove = []
                
                # Check direct key
                if delta.key in current_metadata:
                    keys_to_remove.append(delta.key)
                
                # Check PQP prefixed key
                pqp_key = f"{self.pqp_prefix}{delta.key}"
                if pqp_key in current_metadata:
                    keys_to_remove.append(pqp_key)
                
                for key_to_remove in keys_to_remove:
                    del current_metadata[key_to_remove]
            
            elif delta.operation in [MetadataOperation.ADDED, MetadataOperation.CHANGED]:
                # Add/update the key
                actual_key = self._get_actual_key(delta.key)
                current_metadata[actual_key] = str(delta.value) if delta.value is not None else ""
        
        return self._run_ffmpeg_metadata_update(current_metadata)

    def get_file_info(self) -> Dict[str, Any]:
        """Get basic file information"""
        probe_data = self._run_ffprobe(show_format=True, show_streams=True)
        
        info = {
            'filename': self.file_path.name,
            'filepath': str(self.file_path),
            'size': self.file_path.stat().st_size,
            'format': {},
            'streams': []
        }
        
        if 'format' in probe_data:
            format_info = probe_data['format']
            info['format'] = {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', ''),
                'format_long_name': format_info.get('format_long_name', '')
            }
        
        if 'streams' in probe_data:
            for stream in probe_data['streams']:
                stream_info = {
                    'index': stream.get('index', 0),
                    'codec_name': stream.get('codec_name', ''),
                    'codec_type': stream.get('codec_type', ''),
                    'width': stream.get('width'),
                    'height': stream.get('height'),
                    'duration': float(stream.get('duration', 0)) if stream.get('duration') else None
                }
                info['streams'].append(stream_info)
        
        return info

    def has_metadata(self, key: str) -> bool:
        """Check if metadata key exists"""
        return self.get_metadata(key) is not None

    def list_metadata_keys(self) -> List[str]:
        """List all metadata keys"""
        all_metadata = self.get_all_metadata()
        return list(all_metadata.keys())

    def get_pqp_metadata(self) -> Dict[str, Any]:
        """Get only PQP-prefixed metadata"""
        all_metadata = self.get_all_metadata()
        pqp_metadata = {}
        
        for key, value in all_metadata.items():
            if key.startswith(self.pqp_prefix):
                clean_key = key[len(self.pqp_prefix):]
                pqp_metadata[clean_key] = value
        
        return pqp_metadata

    def clear_all_metadata(self, cardinal: str = "user") -> bool:
        """Clear all editable metadata from file"""
        current_metadata = self.get_all_metadata()
        
        # Keep only non-editable keys
        filtered_metadata = {}
        for key, value in current_metadata.items():
            norm_key = normalize_key(key)
            if not can_edit_key(norm_key, cardinal):
                filtered_metadata[key] = value
        
        return self._run_ffmpeg_metadata_update(filtered_metadata)

    def backup_metadata(self) -> Dict[str, Any]:
        """Create a backup of current metadata"""
        return self.get_all_metadata().copy()

    def restore_metadata(self, backup: Dict[str, Any], cardinal: str = "user") -> bool:
        """Restore metadata from backup (only editable keys)"""
        filtered_backup = self._filter_editable_keys(backup, cardinal)
        return self.sync_metadata(filtered_backup, cardinal)

    def validate_file(self) -> bool:
        """Validate that file is a valid media file"""
        try:
            probe_data = self._run_ffprobe(show_format=True)
            return 'format' in probe_data
        except Exception:
            return False

    def get_duration_seconds(self) -> float:
        """Get file duration in seconds"""
        intrinsic = self.get_intrinsic_data()
        return intrinsic.get('duration', 0.0)

    def get_format_name(self) -> str:
        """Get file format name"""
        intrinsic = self.get_intrinsic_data()
        return intrinsic.get('format_name', '')

    def is_video_file(self) -> bool:
        """Check if file is a video file"""
        file_info = self.get_file_info()
        for stream in file_info['streams']:
            if stream['codec_type'] == 'video':
                return True
        return False

    def is_audio_file(self) -> bool:
        """Check if file is an audio file"""
        file_info = self.get_file_info()
        has_audio = any(stream['codec_type'] == 'audio' for stream in file_info['streams'])
        has_video = any(stream['codec_type'] == 'video' for stream in file_info['streams'])
        return has_audio and not has_video
#!/usr/bin/env python3
"""
PanQPlex Display Module
Handles formatted table output for terminal display
"""

from typing import List, Dict, Any, Optional

from metadata.provider import MetadataProvider
from metadata.schemas import get_all_metadata_keys
from config.provider import ConfigProvider
from shell_helper import get_video_files_in_pwd, get_file_size, get_filename
from format_helper import format_metadata_value, format_uuid
from status_enums import FileStatus, format_status, format_upload_state

def print_table_list(files: Optional[List[str]] = None, 
                    columns: Optional[List[str]] = None) -> None:
    """Print files in table format"""
    
    # Get file list
    if files is None:
        files = _get_all_files_in_pwd()
    
    # Get columns list
    if columns is None:
        columns = _get_columns_from_config()
    
    if not files:
        print("No files found")
        return
    
    if not columns:
        print("No columns specified")
        return
    
    # Collect metadata for all files
    table_data = []
    for file_path in files:
        try:
            row_data = _get_file_row_data(file_path, columns)
            table_data.append(row_data)
        except Exception:
            continue  # Skip files that can't be processed
    
    if not table_data:
        print("No valid files found")
        return
    
    # Calculate column widths
    col_widths = _calculate_column_widths(table_data, columns)
    
    # Print headers
    _print_headers(columns, col_widths)
    
    # Print rows
    for row_data in table_data:
        _print_row(row_data, columns, col_widths)

def print_full_list(files: Optional[List[str]] = None) -> None:
    """Print files in detailed format"""
    
    if files is None:
        files = _get_all_files_in_pwd()
    
    if not files:
        print("No files found")
        return
    
    for file_path in files:
        try:
            _print_file_details(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

def _print_file_details(file_path: str) -> None:
    """Print detailed information for a single file"""
    metadata_provider = MetadataProvider(file_path)
    
    filename = get_filename(file_path)
    file_uuid = format_uuid(file_path)
    
    # Get status and format it
    status = metadata_provider.get_file_status()
    status_display = format_status(status)
    
    # Get basic metadata
    title = metadata_provider.get_metadata("title") or "Untitled"
    description = metadata_provider.get_metadata("description") or "␀"
    tags = metadata_provider.get_metadata("tags") or "␀"
    
    duration = metadata_provider.get_duration_seconds()
    file_size = get_file_size(file_path)
    
    last_sync = metadata_provider.get_metadata("last_sync") or "never"
    
    print(f"\n▶ {filename}")
    print(f"  🆔 File ID: {file_uuid}     | Status: {status_display}")
    print(f"  🎞️ Length: {format_metadata_value('duration', duration)}     | ⚖️ Size: {format_metadata_value('size', file_size)}")
    print(f"  🗓️ Last Update: {format_metadata_value('last_sync', last_sync)}")
    print(f"  📜 Title: {title}")
    print(f"  📖 Desc: {description}")
    print(f"  🏷️ {tags}")

def _get_all_files_in_pwd() -> List[str]:
    """Get all video files in current directory"""
    return get_video_files_in_pwd()

def _get_columns_from_config() -> List[str]:
    """Get columns from config or use default"""
    try:
        config = ConfigProvider()
        columns = config.get_config_value('display.default_columns')
        if columns:
            return columns
    except Exception:
        pass
    
    # Default columns
    return ["file_uuid", "upload_state", "title", "filename", "duration", "size", "last_sync"]

def _get_file_row_data(file_path: str, columns: List[str]) -> Dict[str, str]:
    """Get metadata for a single file"""
    metadata_provider = MetadataProvider(file_path)
    row_data = {}
    
    for col in columns:
        if col == "file_uuid":
            value = format_uuid(file_path)
        elif col == "filename":
            value = get_filename(file_path)
        elif col == "duration" or col == "length":
            value = metadata_provider.get_duration_seconds()
        elif col == "size":
            value = get_file_size(file_path)
        elif col == "upload_state":
            status = metadata_provider.get_file_status()
            value = format_status(status)
        else:
            value = metadata_provider.get_metadata(col)
        
        row_data[col] = format_metadata_value(col, value)
    
    return row_data

def _calculate_column_widths(table_data: List[Dict[str, str]], 
                           columns: List[str]) -> Dict[str, int]:
    """Calculate maximum width for each column"""
    col_widths = {}
    
    # Get column labels from schema
    all_keys = get_all_metadata_keys()
    
    for col in columns:
        # Start with header width
        header = all_keys.get(col, {}).get('label', col.upper())
        max_width = len(header)
        
        # Check data width
        for row in table_data:
            value = row.get(col, "")
            max_width = max(max_width, len(str(value)))
        
        col_widths[col] = max_width
    
    return col_widths

def _print_headers(columns: List[str], col_widths: Dict[str, int]) -> None:
    """Print table headers"""
    all_keys = get_all_metadata_keys()
    headers = []
    
    for col in columns:
        label = all_keys.get(col, {}).get('label', col.upper())
        headers.append(label.ljust(col_widths[col]))
    
    print("| " + " | ".join(headers) + " |")

def _print_row(row_data: Dict[str, str], columns: List[str], 
              col_widths: Dict[str, int]) -> None:
    """Print table row"""
    values = []
    
    for col in columns:
        value = row_data.get(col, "")
        values.append(str(value).ljust(col_widths[col]))
    
    print("| " + " | ".join(values) + " |")
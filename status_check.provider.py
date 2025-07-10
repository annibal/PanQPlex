#!/usr/bin/env python3
"""
PanQPlex Status Check Provider
Compares local files with uploaded versions and updates metadata
"""

import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from shell_helper import get_video_files_in_pwd, file_exists
from metadata.provider import MetadataProvider
from metadata.schemas import get_all_metadata_keys
from youtube.provider import YouTubeProvider, YouTubeAccount
from config.provider import ConfigProvider
from format_helper import format_time_ago
from status_enums import FileStatus, UploadState

@dataclass
class FileStatusInfo:
    """Information about file sync status"""
    file_path: str
    local_status: FileStatus
    remote_status: Optional[str] = None
    video_id: Optional[str] = None
    platform_url: Optional[str] = None
    needs_upload: bool = False
    needs_update: bool = False
    error_message: Optional[str] = None
    last_sync: Optional[str] = None
    sync_hash: Optional[str] = None

class StatusCheckProvider:
    """Handles status checking and metadata synchronization"""
    
    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        self.config = config_provider or ConfigProvider()
        self.youtube_providers: Dict[str, YouTubeProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize YouTube providers for all accounts"""
        accounts = self.config.get_youtube_accounts()
        
        for account in accounts:
            if account.enabled:
                try:
                    # Convert config account to youtube provider account
                    yt_account = YouTubeAccount(
                        name=account.name,
                        client_id=account.client_id,
                        client_secret=account.client_secret,
                        channel_id=account.default_channel,
                        max_uploads_per_day=account.max_videos_per_day,
                        enabled=account.enabled
                    )
                    
                    credentials_path = self.config.get_logs_dir_path() / f'credentials_{account.name}.json'
                    provider = YouTubeProvider(yt_account, str(credentials_path))
                    
                    if provider.is_authenticated():
                        self.youtube_providers[account.name] = provider
                except Exception as e:
                    print(f"⚠️  Failed to initialize provider for {account.name}: {e}")

    def check_all_files(self, file_paths: Optional[List[str]] = None) -> List[FileStatusInfo]:
        """Check status of all files or specified files"""
        if file_paths is None:
            file_paths = get_video_files_in_pwd()
        
        results = []
        
        for file_path in file_paths:
            if file_exists(file_path):
                status_info = self._check_single_file(file_path)
                results.append(status_info)
        
        return results

    def _check_single_file(self, file_path: str) -> FileStatusInfo:
        """Check status of a single file"""
        try:
            metadata_provider = MetadataProvider(file_path)
            
            # Get current metadata
            file_uuid = metadata_provider.get_metadata("file_uuid")
            upload_state = metadata_provider.get_metadata("upload_state") or "undefined"
            video_id = metadata_provider.get_metadata("platform_id")
            platform_url = metadata_provider.get_metadata("platform_url")
            last_sync = metadata_provider.get_metadata("last_sync")
            sync_hash = metadata_provider.get_metadata("sync_hash")
            upload_user = metadata_provider.get_metadata("upload_user") or "default"
            
            # Initialize status info
            status_info = FileStatusInfo(
                file_path=file_path,
                local_status=FileStatus(upload_state),
                video_id=video_id,
                platform_url=platform_url,
                last_sync=last_sync,
                sync_hash=sync_hash
            )
            
            # Calculate current metadata hash
            current_hash = self._calculate_metadata_hash(metadata_provider)
            
            # Determine status based on current state
            if upload_state == "undefined":
                status_info = self._handle_undefined_file(status_info, metadata_provider)
            elif upload_state in ["acknowledged", "provisioned"]:
                status_info = self._handle_local_only_file(status_info, metadata_provider, current_hash)
            elif upload_state in ["queued_new", "uploading"]:
                status_info = self._handle_pending_upload(status_info, metadata_provider, upload_user)
            elif upload_state == "finished":
                status_info = self._handle_finished_file(status_info, metadata_provider, current_hash, upload_user)
            elif upload_state in ["queued_edit", "hindered"]:
                status_info = self._handle_problematic_file(status_info, metadata_provider, upload_user)
            
            # Update file metadata if needed
            self._update_file_metadata(metadata_provider, status_info)
            
            return status_info
            
        except Exception as e:
            return FileStatusInfo(
                file_path=file_path,
                local_status=FileStatus.HINDERED,
                error_message=f"Error checking file: {e}"
            )

    def _handle_undefined_file(self, status_info: FileStatusInfo, 
                              metadata_provider: MetadataProvider) -> FileStatusInfo:
        """Handle files that haven't been processed by PanQPlex yet"""
        # Initialize basic PQP metadata
        file_uuid = self._generate_file_uuid(status_info.file_path)
        
        # Set to acknowledged state
        status_info.local_status = FileStatus.ACKNOWLEDGED
        status_info.needs_upload = False
        
        return status_info

    def _handle_local_only_file(self, status_info: FileStatusInfo, 
                               metadata_provider: MetadataProvider,
                               current_hash: str) -> FileStatusInfo:
        """Handle files that exist only locally"""
        # Check if metadata is complete enough for upload
        title = metadata_provider.get_metadata("title")
        
        if title and title.strip():
            # File is ready for upload
            status_info.local_status = FileStatus.QUEUED_NEW
            status_info.needs_upload = True
        else:
            # Still needs metadata
            status_info.local_status = FileStatus.PROVISIONED
            status_info.needs_upload = False
        
        return status_info

    def _handle_pending_upload(self, status_info: FileStatusInfo,
                              metadata_provider: MetadataProvider,
                              upload_user: str) -> FileStatusInfo:
        """Handle files with pending uploads"""
        if upload_user in self.youtube_providers:
            provider = self.youtube_providers[upload_user]
            
            # Check if upload completed
            if status_info.video_id:
                video_info = provider.get_video_info(status_info.video_id)
                if video_info:
                    # Upload completed successfully
                    status_info.local_status = FileStatus.FINISHED
                    status_info.remote_status = video_info['status']['privacyStatus']
                    status_info.platform_url = f"https://www.youtube.com/watch?v={status_info.video_id}"
                    status_info.needs_upload = False
                else:
                    # Video not found, may have failed
                    status_info.local_status = FileStatus.HINDERED
                    status_info.error_message = "Uploaded video not found"
            else:
                # Still queued for upload
                status_info.needs_upload = True
        else:
            status_info.local_status = FileStatus.HINDERED
            status_info.error_message = f"Upload user '{upload_user}' not available"
        
        return status_info

    def _handle_finished_file(self, status_info: FileStatusInfo,
                             metadata_provider: MetadataProvider,
                             current_hash: str,
                             upload_user: str) -> FileStatusInfo:
        """Handle files that have been uploaded"""
        # Check if local metadata changed
        if current_hash != status_info.sync_hash:
            status_info.local_status = FileStatus.QUEUED_EDIT
            status_info.needs_update = True
        else:
            # Verify remote file still exists
            if upload_user in self.youtube_providers and status_info.video_id:
                provider = self.youtube_providers[upload_user]
                video_info = provider.get_video_info(status_info.video_id)
                
                if video_info:
                    status_info.remote_status = video_info['status']['privacyStatus']
                else:
                    status_info.local_status = FileStatus.HINDERED
                    status_info.error_message = "Remote video no longer exists"
        
        return status_info

    def _handle_problematic_file(self, status_info: FileStatusInfo,
                                metadata_provider: MetadataProvider,
                                upload_user: str) -> FileStatusInfo:
        """Handle files with errors or pending edits"""
        if status_info.local_status == FileStatus.QUEUED_EDIT:
            # Check if we can update the remote file
            if upload_user in self.youtube_providers and status_info.video_id:
                status_info.needs_update = True
            else:
                status_info.local_status = FileStatus.HINDERED
                status_info.error_message = "Cannot update remote video"
        
        return status_info

    def _calculate_metadata_hash(self, metadata_provider: MetadataProvider) -> str:
        """Calculate hash of user-editable metadata"""
        metadata = metadata_provider.get_all_metadata()
        
        # Get only user-editable metadata
        from metadata.schemas import can_edit_key
        user_metadata = {}
        
        for key, value in metadata.items():
            if can_edit_key(key, "user"):
                user_metadata[key] = value
        
        # Create hash
        metadata_str = str(sorted(user_metadata.items()))
        return hashlib.sha256(metadata_str.encode()).hexdigest()[:16]

    def _generate_file_uuid(self, file_path: str) -> str:
      """Generate UUID for file - uses format_uuid from format_helper"""
      from format_helper import format_uuid
      return format_uuid(file_path)

    def _update_file_metadata(self, metadata_provider: MetadataProvider, 
                             status_info: FileStatusInfo) -> None:
        """Update file metadata based on status check results"""
        current_time = str(int(time.time()))
        
        # Update file UUID if not set
        if not metadata_provider.get_metadata("file_uuid"):
            file_uuid = self._generate_file_uuid(status_info.file_path)
            metadata_provider.set_metadata("file_uuid", file_uuid, "system")
        
        # Update upload state
        metadata_provider.set_metadata("upload_state", status_info.local_status.value, "system")
        
        # Update platform information if available
        if status_info.video_id:
            metadata_provider.set_metadata("platform_id", status_info.video_id, "system")
        
        if status_info.platform_url:
            metadata_provider.set_metadata("platform_url", status_info.platform_url, "system")
        
        # Update sync hash for finished files
        if status_info.local_status == FileStatus.FINISHED:
            current_hash = self._calculate_metadata_hash(metadata_provider)
            metadata_provider.set_metadata("sync_hash", current_hash, "system")
        
        # Update last sync time
        metadata_provider.set_metadata("last_sync", current_time, "system")
        
        # Clear error message if status improved
        if status_info.local_status != FileStatus.HINDERED:
            metadata_provider.set_metadata("error_message", "", "system")
        elif status_info.error_message:
            metadata_provider.set_metadata("error_message", status_info.error_message, "system")

    def get_summary(self, status_results: List[FileStatusInfo]) -> Dict[str, int]:
        """Get summary statistics from status check results"""
        summary = {
            "total_files": len(status_results),
            "undefined": 0,
            "acknowledged": 0,
            "provisioned": 0,
            "queued_new": 0,
            "uploading": 0,
            "finished": 0,
            "queued_edit": 0,
            "hindered": 0,
            "needs_upload": 0,
            "needs_update": 0
        }
        
        for status_info in status_results:
            summary[status_info.local_status.value] += 1
            
            if status_info.needs_upload:
                summary["needs_upload"] += 1
            
            if status_info.needs_update:
                summary["needs_update"] += 1
        
        return summary

    def print_summary(self, status_results: List[FileStatusInfo]) -> None:
        """Print human-readable summary"""
        summary = self.get_summary(status_results)
        
        print(f"📊 Status Summary ({summary['total_files']} files)")
        print("─" * 40)
        
        if summary["undefined"] > 0:
            print(f"❓ Undefined:     {summary['undefined']}")
        if summary["acknowledged"] > 0:
            print(f"👀 Acknowledged:  {summary['acknowledged']}")
        if summary["provisioned"] > 0:
            print(f"✍️  Provisioned:   {summary['provisioned']}")
        if summary["queued_new"] > 0:
            print(f"⭐ Queued (new):  {summary['queued_new']}")
        if summary["uploading"] > 0:
            print(f"📤 Uploading:     {summary['uploading']}")
        if summary["finished"] > 0:
            print(f"🆗 Finished:      {summary['finished']}")
        if summary["queued_edit"] > 0:
            print(f"🔜 Queued (edit): {summary['queued_edit']}")
        if summary["hindered"] > 0:
            print(f"⚠️  Hindered:      {summary['hindered']}")
        
        print("─" * 40)
        print(f"🔄 Actions needed:")
        print(f"   • Upload: {summary['needs_upload']} files")
        print(f"   • Update: {summary['needs_update']} files")

    def close(self) -> None:
        """Clean up YouTube providers"""
        for provider in self.youtube_providers.values():
            provider.close()
        self.youtube_providers.clear()

def check_status(file_paths: Optional[List[str]] = None, 
                config_path: Optional[str] = None) -> List[FileStatusInfo]:
    """Convenience function to check file status"""
    config = ConfigProvider(config_path) if config_path else ConfigProvider()
    checker = StatusCheckProvider(config)
    
    try:
        return checker.check_all_files(file_paths)
    finally:
        checker.close()

def print_status_summary(file_paths: Optional[List[str]] = None,
                        config_path: Optional[str] = None) -> None:
    """Convenience function to print status summary"""
    results = check_status(file_paths, config_path)
    checker = StatusCheckProvider()
    checker.print_summary(results)
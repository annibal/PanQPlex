#!/usr/bin/env python3
"""
PanQPlex YouTube Provider
Complete YouTube API integration for video upload and management
"""

import json
import time
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from status_enums import UploadState

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload, MediaUploadProgress
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    raise ImportError("Google API client libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

class YouTubePrivacyStatus(Enum):
    """YouTube privacy statuses"""
    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"

class YouTubeCategory(Enum):
    """YouTube video categories"""
    FILM_ANIMATION = "1"
    AUTOS_VEHICLES = "2"
    MUSIC = "10"
    PETS_ANIMALS = "15"
    SPORTS = "17"
    TRAVEL_EVENTS = "19"
    GAMING = "20"
    PEOPLE_BLOGS = "22"
    COMEDY = "23"
    ENTERTAINMENT = "24"
    NEWS_POLITICS = "25"
    HOWTO_STYLE = "26"
    EDUCATION = "27"
    SCIENCE_TECHNOLOGY = "28"
    NONPROFITS_ACTIVISM = "29"

@dataclass
class YouTubeVideoMetadata:
    """YouTube video metadata structure"""
    title: str
    description: str = ""
    tags: List[str] = None
    category_id: str = "22"  # People & Blogs
    privacy_status: str = "private"
    made_for_kids: bool = False
    embeddable: bool = True
    license: str = "youtube"  # or "creativeCommon"
    public_stats_viewable: bool = True
    publish_at: Optional[str] = None
    default_language: str = "en"
    default_audio_language: str = "en"
    recording_date: Optional[str] = None
    location_description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class YouTubeUploadProgress:
    """Upload progress information"""
    bytes_uploaded: int = 0
    total_bytes: int = 0
    progress_percent: float = 0.0
    state: UploadState = UploadState.QUEUED
    video_id: Optional[str] = None
    upload_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    last_update: float = 0.0

@dataclass
class YouTubeAccount:
    """YouTube account configuration"""
    name: str
    client_id: str
    client_secret: str
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    token_expiry: Optional[float] = None
    channel_id: Optional[str] = None
    max_uploads_per_day: int = 6
    enabled: bool = True

@dataclass
class YouTubeQuota:
    """YouTube API quota tracking"""
    daily_limit: int = 10000
    used_today: int = 0
    last_reset: float = 0.0
    operations: Dict[str, int] = None

    def __post_init__(self):
        if self.operations is None:
            self.operations = {}

class YouTubeProvider:
    """Complete YouTube API provider for PanQPlex"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]
    
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    
    # Quota costs for different operations
    QUOTA_COSTS = {
        'video_insert': 1600,
        'video_update': 50,
        'video_list': 1,
        'channel_list': 1,
        'playlist_insert': 50,
        'playlist_items_insert': 50,
        'thumbnail_set': 50
    }
    
    # Chunk size for resumable uploads (8MB)
    UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024
    
    # Maximum file size (128GB)
    MAX_FILE_SIZE = 128 * 1024 * 1024 * 1024
    
    # Supported video formats
    SUPPORTED_FORMATS = {
        'mp4', 'mov', 'avi', 'wmv', 'flv', 'webm', 'mkv', '3gpp', 'mpg'
    }

    def __init__(self, account: YouTubeAccount, credentials_path: Optional[str] = None):
        """Initialize YouTube provider with account configuration"""
        self.account = account
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self.service = None
        self.credentials = None
        self.quota = YouTubeQuota()
        self.logger = self._setup_logger()
        
        # Upload tracking
        self.active_uploads: Dict[str, YouTubeUploadProgress] = {}
        
        # Initialize service
        self._initialize_service()

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for YouTube provider"""
        logger = logging.getLogger(f'youtube_provider_{self.account.name}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _initialize_service(self) -> None:
        """Initialize YouTube API service"""
        try:
            self.credentials = self._get_authenticated_credentials()
            if self.credentials:
                self.service = build(
                    self.API_SERVICE_NAME,
                    self.API_VERSION,
                    credentials=self.credentials
                )
                self.logger.info(f"YouTube service initialized for account: {self.account.name}")
            else:
                self.logger.error("Failed to get authenticated credentials")
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube service: {e}")
            raise

    def _get_authenticated_credentials(self) -> Optional[Credentials]:
        """Get authenticated Google credentials"""
        creds = None
        
        # Try to load existing credentials
        if self.credentials_path and self.credentials_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.credentials_path), self.SCOPES
                )
            except Exception as e:
                self.logger.warning(f"Failed to load credentials from file: {e}")
        
        # Try to use account stored tokens
        if not creds and self.account.refresh_token:
            try:
                creds = Credentials(
                    token=self.account.access_token,
                    refresh_token=self.account.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.account.client_id,
                    client_secret=self.account.client_secret,
                    scopes=self.SCOPES
                )
            except Exception as e:
                self.logger.warning(f"Failed to create credentials from account: {e}")
        
        # Refresh if credentials are expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
            except Exception as e:
                self.logger.error(f"Failed to refresh credentials: {e}")
                return None
        
        # If no valid credentials, start OAuth flow
        if not creds or not creds.valid:
            creds = self._perform_oauth_flow()
        
        return creds

    def _perform_oauth_flow(self) -> Optional[Credentials]:
        """Perform OAuth2 authentication flow"""
        try:
            # Create client configuration
            client_config = {
                "installed": {
                    "client_id": self.account.client_id,
                    "client_secret": self.account.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save credentials
            self._save_credentials(creds)
            
            self.logger.info("OAuth authentication completed successfully")
            return creds
            
        except Exception as e:
            self.logger.error(f"OAuth flow failed: {e}")
            return None

    def _save_credentials(self, creds: Credentials) -> None:
        """Save credentials to file and update account"""
        if self.credentials_path:
            try:
                with open(self.credentials_path, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                self.logger.warning(f"Failed to save credentials to file: {e}")
        
        # Update account with new tokens
        self.account.access_token = creds.token
        self.account.refresh_token = creds.refresh_token
        if creds.expiry:
            self.account.token_expiry = creds.expiry.timestamp()

    def _check_quota(self, operation: str) -> bool:
        """Check if operation is within quota limits"""
        cost = self.QUOTA_COSTS.get(operation, 1)
        
        # Reset daily quota if needed
        current_time = time.time()
        if current_time - self.quota.last_reset > 86400:  # 24 hours
            self.quota.used_today = 0
            self.quota.last_reset = current_time
        
        # Check if operation would exceed daily limit
        if self.quota.used_today + cost > self.quota.daily_limit:
            return False
        
        return True

    def _consume_quota(self, operation: str) -> None:
        """Consume quota for operation"""
        cost = self.QUOTA_COSTS.get(operation, 1)
        self.quota.used_today += cost
        self.quota.operations[operation] = self.quota.operations.get(operation, 0) + 1

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate file for YouTube upload"""
        path = Path(file_path)
        
        if not path.exists():
            return False, "File does not exist"
        
        if not path.is_file():
            return False, "Path is not a file"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check file extension
        extension = path.suffix.lower().lstrip('.')
        if extension not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {extension}"
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith('video/'):
            return False, f"Invalid MIME type: {mime_type}"
        
        return True, "Valid"

    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user's channel information"""
        if not self._check_quota('channel_list'):
            self.logger.error("Quota exceeded for channel_list operation")
            return None
        
        try:
            request = self.service.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            self._consume_quota('channel_list')
            
            if response.get('items'):
                channel = response['items'][0]
                self.account.channel_id = channel['id']
                return channel
            
            return None
            
        except HttpError as e:
            self.logger.error(f"Failed to get channel info: {e}")
            return None

    def upload_video(self, file_path: str, metadata: YouTubeVideoMetadata,
                    progress_callback: Optional[callable] = None) -> YouTubeUploadProgress:
        """Upload video to YouTube with resumable upload"""
        
        # Validate file
        is_valid, message = self.validate_file(file_path)
        if not is_valid:
            progress = YouTubeUploadProgress(
                state=UploadState.ERROR,
                error_message=message
            )
            return progress
        
        # Check quota
        if not self._check_quota('video_insert'):
            progress = YouTubeUploadProgress(
                state=UploadState.ERROR,
                error_message="Daily quota exceeded"
            )
            return progress
        
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size
        
        # Create upload progress tracker
        upload_id = self._generate_upload_id(file_path)
        progress = YouTubeUploadProgress(
            total_bytes=file_size,
            state=UploadState.UPLOADING,
            last_update=time.time()
        )
        self.active_uploads[upload_id] = progress
        
        try:
            # Prepare video resource
            video_body = self._prepare_video_body(metadata)
            
            # Create media upload object
            media_body = MediaFileUpload(
                file_path,
                chunksize=self.UPLOAD_CHUNK_SIZE,
                resumable=True,
                mimetype=mimetypes.guess_type(file_path)[0]
            )
            
            # Initialize upload request
            insert_request = self.service.videos().insert(
                part=','.join(video_body.keys()),
                body=video_body,
                media_body=media_body
            )
            
            # Perform resumable upload
            response = self._perform_resumable_upload(
                insert_request, progress, progress_callback
            )
            
            if response:
                progress.video_id = response['id']
                progress.upload_url = f"https://www.youtube.com/watch?v={response['id']}"
                progress.state = UploadState.COMPLETED
                progress.progress_percent = 100.0
                self._consume_quota('video_insert')
                self.logger.info(f"Video uploaded successfully: {response['id']}")
            else:
                progress.state = UploadState.ERROR
                progress.error_message = "Upload failed without error response"
            
        except HttpError as e:
            error_msg = f"HTTP error during upload: {e}"
            progress.state = UploadState.ERROR
            progress.error_message = error_msg
            self.logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during upload: {e}"
            progress.state = UploadState.ERROR
            progress.error_message = error_msg
            self.logger.error(error_msg)
        
        finally:
            progress.last_update = time.time()
        
        return progress

    def _generate_upload_id(self, file_path: str) -> str:
        """Generate unique upload ID"""
        hasher = hashlib.sha256()
        hasher.update(f"{file_path}{time.time()}{self.account.name}".encode())
        return hasher.hexdigest()[:16]

    def _prepare_video_body(self, metadata: YouTubeVideoMetadata) -> Dict[str, Any]:
        """Prepare video body for YouTube API"""
        body = {
            'snippet': {
                'title': metadata.title,
                'description': metadata.description,
                'tags': metadata.tags,
                'categoryId': metadata.category_id,
                'defaultLanguage': metadata.default_language,
                'defaultAudioLanguage': metadata.default_audio_language
            },
            'status': {
                'privacyStatus': metadata.privacy_status,
                'embeddable': metadata.embeddable,
                'license': metadata.license,
                'publicStatsViewable': metadata.public_stats_viewable,
                'madeForKids': metadata.made_for_kids
            }
        }
        
        # Add optional fields if provided
        if metadata.publish_at:
            body['status']['publishAt'] = metadata.publish_at
        
        if metadata.recording_date:
            body['recordingDetails'] = {
                'recordingDate': metadata.recording_date
            }
        
        if metadata.location_description:
            if 'recordingDetails' not in body:
                body['recordingDetails'] = {}
            body['recordingDetails']['locationDescription'] = metadata.location_description
        
        if metadata.latitude and metadata.longitude:
            if 'recordingDetails' not in body:
                body['recordingDetails'] = {}
            body['recordingDetails']['location'] = {
                'latitude': metadata.latitude,
                'longitude': metadata.longitude
            }
        
        return body

    def _perform_resumable_upload(self, insert_request, progress: YouTubeUploadProgress,
                                 progress_callback: Optional[callable] = None) -> Optional[Dict[str, Any]]:
        """Perform resumable upload with progress tracking"""
        response = None
        error = None
        retry_count = 0
        max_retries = 3
        
        while response is None and retry_count < max_retries:
            try:
                status, response = insert_request.next_chunk()
                
                if status:
                    progress.bytes_uploaded = status.resumable_progress
                    progress.progress_percent = (status.resumable_progress / progress.total_bytes) * 100
                    progress.last_update = time.time()
                    
                    if progress_callback:
                        progress_callback(progress)
                    
                    self.logger.debug(f"Upload progress: {progress.progress_percent:.1f}%")
                
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Retryable error
                    retry_count += 1
                    progress.retry_count = retry_count
                    wait_time = 2 ** retry_count
                    self.logger.warning(f"Retryable error occurred, waiting {wait_time}s before retry: {e}")
                    time.sleep(wait_time)
                else:
                    # Non-retryable error
                    error = e
                    break
            
            except Exception as e:
                error = e
                break
        
        if error:
            progress.error_message = str(error)
            self.logger.error(f"Upload failed: {error}")
            return None
        
        return response

    def update_video_metadata(self, video_id: str, metadata: YouTubeVideoMetadata) -> bool:
        """Update existing video metadata"""
        if not self._check_quota('video_update'):
            self.logger.error("Quota exceeded for video_update operation")
            return False
        
        try:
            video_body = self._prepare_video_body(metadata)
            video_body['id'] = video_id
            
            request = self.service.videos().update(
                part=','.join(video_body.keys()),
                body=video_body
            )
            
            response = request.execute()
            self._consume_quota('video_update')
            
            self.logger.info(f"Video metadata updated successfully: {video_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Failed to update video metadata: {e}")
            return False

    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video information by ID"""
        if not self._check_quota('video_list'):
            self.logger.error("Quota exceeded for video_list operation")
            return None
        
        try:
            request = self.service.videos().list(
                part="snippet,status,statistics,recordingDetails",
                id=video_id
            )
            
            response = request.execute()
            self._consume_quota('video_list')
            
            if response.get('items'):
                return response['items'][0]
            
            return None
            
        except HttpError as e:
            self.logger.error(f"Failed to get video info: {e}")
            return None

    def delete_video(self, video_id: str) -> bool:
        """Delete video from YouTube"""
        try:
            request = self.service.videos().delete(id=video_id)
            request.execute()
            
            self.logger.info(f"Video deleted successfully: {video_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Failed to delete video: {e}")
            return False

    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Set custom thumbnail for video"""
        if not self._check_quota('thumbnail_set'):
            self.logger.error("Quota exceeded for thumbnail_set operation")
            return False
        
        try:
            request = self.service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            )
            
            response = request.execute()
            self._consume_quota('thumbnail_set')
            
            self.logger.info(f"Thumbnail set successfully for video: {video_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Failed to set thumbnail: {e}")
            return False

    def get_upload_progress(self, upload_id: str) -> Optional[YouTubeUploadProgress]:
        """Get upload progress by upload ID"""
        return self.active_uploads.get(upload_id)

    def cancel_upload(self, upload_id: str) -> bool:
        """Cancel active upload"""
        if upload_id in self.active_uploads:
            progress = self.active_uploads[upload_id]
            progress.state = UploadState.CANCELLED
            progress.last_update = time.time()
            return True
        return False

    def get_quota_usage(self) -> YouTubeQuota:
        """Get current quota usage"""
        return self.quota

    def is_authenticated(self) -> bool:
        """Check if provider is properly authenticated"""
        return self.service is not None and self.credentials is not None and self.credentials.valid

    def test_connection(self) -> Tuple[bool, str]:
        """Test YouTube API connection"""
        try:
            if not self.is_authenticated():
                return False, "Not authenticated"
            
            channel_info = self.get_channel_info()
            if channel_info:
                return True, f"Connected to channel: {channel_info['snippet']['title']}"
            else:
                return False, "Failed to retrieve channel information"
                
        except Exception as e:
            return False, f"Connection test failed: {e}"

    def get_supported_formats(self) -> List[str]:
        """Get list of supported video formats"""
        return list(self.SUPPORTED_FORMATS)

    def get_max_file_size(self) -> int:
        """Get maximum supported file size"""
        return self.MAX_FILE_SIZE

    def close(self) -> None:
        """Clean up resources"""
        self.active_uploads.clear()
        self.service = None
        self.credentials = None
        self.logger.info("YouTube provider closed")
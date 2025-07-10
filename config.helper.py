#!/usr/bin/env python3
"""
PanQPlex Configuration Provider
Manages configuration files and settings
"""

import os
import toml
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class YouTubeAccount:
    name: str
    api_key: str
    client_id: str
    client_secret: str
    default_channel: str
    max_videos_per_day: int = 5
    enabled: bool = True

@dataclass
class UploadSettings:
    default_privacy: str = "private"
    default_category: str = "22"  # People & Blogs
    retry_attempts: int = 3
    retry_delay: int = 300
    chunk_size: int = 1048576

@dataclass
class MetadataMapping:
    title: str = "title"
    description: str = "comment"
    tags: str = "keywords"
    category: str = "genre"

@dataclass
class LoggingSettings:
    level: str = "INFO"
    max_file_size: str = "10MB"
    backup_count: int = 5

class ConfigProvider:
    def __init__(self, config_path: Optional[str] = None):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / '.pqpvsf'
        self.config_file = Path(config_path) if config_path else self.config_dir / 'config.toml'
        self.logs_dir = self.config_dir / 'logs'
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load configuration
        self._config_data = self._load_config()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.config_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        self.logs_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return toml.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {
            "youtube_accounts": [
                {
                    "name": "default_account",
                    "api_key": "YOUR_API_KEY_HERE",
                    "client_id": "YOUR_CLIENT_ID_HERE",
                    "client_secret": "YOUR_CLIENT_SECRET_HERE",
                    "default_channel": "YOUR_CHANNEL_ID_HERE",
                    "max_videos_per_day": 5,
                    "enabled": True
                }
            ],
            "upload_settings": {
                "default_privacy": "private",
                "default_category": "22",
                "retry_attempts": 3,
                "retry_delay": 300,
                "chunk_size": 1048576
            },
            "metadata_mapping": {
                "title": "title",
                "description": "comment",
                "tags": "keywords",
                "category": "genre"
            },
            "logging": {
                "level": "INFO",
                "max_file_size": "10MB",
                "backup_count": 5
            },
            "editor": {
                "command": ""  # Will use $EDITOR if empty
            }
        }
        
        self._save_config(default_config)
        return default_config

    def _save_config(self, config_data: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                toml.dump(config_data, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_youtube_accounts(self) -> List[YouTubeAccount]:
        """Get all YouTube accounts"""
        accounts_data = self._config_data.get('youtube_accounts', [])
        return [YouTubeAccount(**account) for account in accounts_data]

    def get_youtube_account(self, name: str) -> Optional[YouTubeAccount]:
        """Get specific YouTube account by name"""
        accounts = self.get_youtube_accounts()
        for account in accounts:
            if account.name == name:
                return account
        return None

    def get_youtube_account_by_api_key(self, api_key: str) -> Optional[YouTubeAccount]:
        """Get YouTube account by API key"""
        accounts = self.get_youtube_accounts()
        for account in accounts:
            if account.api_key == api_key:
                return account
        return None

    def add_youtube_account(self, account: YouTubeAccount):
        """Add new YouTube account"""
        accounts_data = self._config_data.get('youtube_accounts', [])
        accounts_data.append(asdict(account))
        self._config_data['youtube_accounts'] = accounts_data
        self._save_config(self._config_data)

    def update_youtube_account(self, name: str, account: YouTubeAccount):
        """Update existing YouTube account"""
        accounts_data = self._config_data.get('youtube_accounts', [])
        for i, acc in enumerate(accounts_data):
            if acc['name'] == name:
                accounts_data[i] = asdict(account)
                break
        self._config_data['youtube_accounts'] = accounts_data
        self._save_config(self._config_data)

    def remove_youtube_account(self, name: str):
        """Remove YouTube account"""
        accounts_data = self._config_data.get('youtube_accounts', [])
        accounts_data = [acc for acc in accounts_data if acc['name'] != name]
        self._config_data['youtube_accounts'] = accounts_data
        self._save_config(self._config_data)

    def get_upload_settings(self) -> UploadSettings:
        """Get upload settings"""
        settings_data = self._config_data.get('upload_settings', {})
        return UploadSettings(**settings_data)

    def update_upload_settings(self, settings: UploadSettings):
        """Update upload settings"""
        self._config_data['upload_settings'] = asdict(settings)
        self._save_config(self._config_data)

    def get_metadata_mapping(self) -> MetadataMapping:
        """Get metadata mapping"""
        mapping_data = self._config_data.get('metadata_mapping', {})
        return MetadataMapping(**mapping_data)

    def update_metadata_mapping(self, mapping: MetadataMapping):
        """Update metadata mapping"""
        self._config_data['metadata_mapping'] = asdict(mapping)
        self._save_config(self._config_data)

    def get_logging_settings(self) -> LoggingSettings:
        """Get logging settings"""
        logging_data = self._config_data.get('logging', {})
        return LoggingSettings(**logging_data)

    def update_logging_settings(self, settings: LoggingSettings):
        """Update logging settings"""
        self._config_data['logging'] = asdict(settings)
        self._save_config(self._config_data)

    def get_editor_command(self) -> str:
        """Get editor command"""
        editor_cmd = self._config_data.get('editor', {}).get('command', '')
        if not editor_cmd:
            # Use system default editor
            return os.environ.get('EDITOR', 'nano')
        return editor_cmd

    def set_editor_command(self, command: str):
        """Set editor command"""
        if 'editor' not in self._config_data:
            self._config_data['editor'] = {}
        self._config_data['editor']['command'] = command
        self._save_config(self._config_data)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (e.g., 'upload_settings.retry_attempts')"""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set_config_value(self, key: str, value: Any):
        """Set configuration value by key path"""
        keys = key.split('.')
        config_ref = self._config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        # Set the value
        config_ref[keys[-1]] = value
        self._save_config(self._config_data)

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data"""
        return self._config_data.copy()

    def open_editor(self):
        """Open configuration file in editor"""
        editor_cmd = self.get_editor_command()
        try:
            subprocess.run([editor_cmd, str(self.config_file)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error opening editor: {e}")
        except FileNotFoundError:
            print(f"Editor '{editor_cmd}' not found")

    def interactive_setup(self, platform: str = "youtube"):
        """Interactive setup for platform"""
        if platform.lower() == "youtube":
            self._interactive_youtube_setup()
        else:
            print(f"Platform '{platform}' not supported yet")

    def _interactive_youtube_setup(self):
        """Interactive YouTube setup"""
        print("\n🔧 YouTube Setup")
        print("=" * 50)
        
        account_name = input("Account name (default_account): ").strip() or "default_account"
        api_key = input("API Key: ").strip()
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        default_channel = input("Default Channel ID: ").strip()
        
        try:
            max_videos = int(input("Max videos per day (5): ").strip() or "5")
        except ValueError:
            max_videos = 5
        
        # Create account
        account = YouTubeAccount(
            name=account_name,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            default_channel=default_channel,
            max_videos_per_day=max_videos,
            enabled=True
        )
        
        # Check if account exists
        existing_account = self.get_youtube_account(account_name)
        if existing_account:
            self.update_youtube_account(account_name, account)
            print(f"✅ Updated account '{account_name}'")
        else:
            self.add_youtube_account(account)
            print(f"✅ Added account '{account_name}'")
        
        print("\n✅ YouTube setup completed!")

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check YouTube accounts
        accounts = self.get_youtube_accounts()
        if not accounts:
            issues.append("No YouTube accounts configured")
        
        for account in accounts:
            if not account.api_key or account.api_key == "YOUR_API_KEY_HERE":
                issues.append(f"Account '{account.name}' missing valid API key")
            if not account.client_id or account.client_id == "YOUR_CLIENT_ID_HERE":
                issues.append(f"Account '{account.name}' missing valid client ID")
            if not account.client_secret or account.client_secret == "YOUR_CLIENT_SECRET_HERE":
                issues.append(f"Account '{account.name}' missing valid client secret")
        
        # Check upload settings
        upload_settings = self.get_upload_settings()
        if upload_settings.retry_attempts < 1:
            issues.append("Retry attempts must be at least 1")
        if upload_settings.retry_delay < 0:
            issues.append("Retry delay cannot be negative")
        
        return issues

    def get_config_file_path(self) -> Path:
        """Get configuration file path"""
        return self.config_file

    def get_logs_dir_path(self) -> Path:
        """Get logs directory path"""
        return self.logs_dir

    def set_config_path(self, path: str):
        """Set custom configuration file path"""
        self.config_file = Path(path)
        self._config_data = self._load_config()
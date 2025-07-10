#!/usr/bin/env python3
"""
PanQPlex Video Sync & Upload Tool - Installer
Updated with YouTube Provider dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any

# ConfigProvider will be created after installation, not imported here

class PQPVSFInstaller:
    def __init__(self):
        self.home_dir = Path.home()
        self.install_dir = self.home_dir / '.pqpvsf'
        self.config_file = self.install_dir / 'config.toml'
        self.logs_dir = self.install_dir / 'logs'
        self.bin_dir = Path('/usr/local/bin')
        
        # Required system packages
        self.system_packages = [
            'ffmpeg',
            'python3-pip',
            'python3-venv',
            'python3-dev',  # For building some Python packages
            'build-essential',  # For compiling native extensions
            'curl',  # For downloading
            'ca-certificates'  # For SSL certificates
        ]
        
        # Required Python packages (updated with YouTube Provider dependencies)
        self.python_packages = [
            # Core YouTube API dependencies
            'google-api-python-client>=2.70.0',
            'google-auth-httplib2>=0.1.0',
            'google-auth-oauthlib>=0.8.0',
            'google-auth>=2.15.0',
            
            # Media processing
            'ffmpeg-python>=0.2.0',
            'pymediainfo>=6.0.0',
            
            # CLI and display
            'click>=8.1.0',
            'tabulate>=0.9.0',
            'colorama>=0.4.6',
            'tqdm>=4.64.0',
            
            # Configuration and data
            'toml>=0.10.2',
            
            # HTTP and networking
            'requests>=2.28.0',
            'urllib3>=1.26.0',
            
            # Additional utilities
            'python-dateutil>=2.8.0',
            'pytz>=2022.7'
        ]

    def check_system_requirements(self) -> bool:
        """Check if running on supported system"""
        if sys.platform != 'linux':
            print("❌ PQPVSf only supports Linux (Ubuntu/Debian)")
            return False
        
        if os.geteuid() != 0:
            print("❌ Please run installer with sudo")
            return False
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False
            
        return True

    def install_system_packages(self) -> bool:
        """Install required system packages"""
        print("📦 Installing system packages...")
        
        try:
            # Update package list
            print("   Updating package list...")
            subprocess.run(['apt', 'update'], check=True, capture_output=True)
            
            # Install packages
            for package in self.system_packages:
                print(f"   Installing {package}...")
                result = subprocess.run(
                    ['apt', 'install', '-y', package],
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            # Verify FFmpeg installation
            print("   Verifying FFmpeg installation...")
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ FFmpeg installation verification failed")
                return False
            else:
                print("   ✅ FFmpeg verified successfully")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system packages: {e}")
            if e.stderr:
                print(f"   Error details: {e.stderr}")
            return False
            
        return True

    def create_directories(self) -> bool:
        """Create necessary directories"""
        print("📁 Creating necessary directories...")
        
        try:
            self.install_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
            self.logs_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
            
            # Create additional directories for YouTube provider
            credentials_dir = self.install_dir / 'credentials'
            temp_dir = self.install_dir / 'temp'
            
            credentials_dir.mkdir(mode=0o700, parents=True, exist_ok=True)  # Secure permissions
            temp_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
            
            # Set ownership to the user who invoked sudo
            if 'SUDO_USER' in os.environ:
                sudo_user = os.environ['SUDO_USER']
                subprocess.run(['chown', '-R', f'{sudo_user}:{sudo_user}', str(self.install_dir)])
                
        except Exception as e:
            print(f"❌ Failed to create directories: {e}")
            return False
            
        return True

    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment"""
        print("🐍 Creating Python virtual environment...")
        
        venv_dir = self.install_dir / 'venv'
        
        try:
            # Create virtual environment
            subprocess.run([
                sys.executable, '-m', 'venv', str(venv_dir)
            ], check=True, capture_output=True)
            
            # Upgrade pip first
            pip_path = venv_dir / 'bin' / 'pip'
            print("   Upgrading pip...")
            subprocess.run([
                str(pip_path), 'install', '--upgrade', 'pip'
            ], check=True, capture_output=True)
            
            # Install wheel for better package building
            print("   Installing wheel...")
            subprocess.run([
                str(pip_path), 'install', 'wheel'
            ], check=True, capture_output=True)
            
            # Install packages with progress indication
            for package in self.python_packages:
                print(f"   Installing {package}...")
                result = subprocess.run([
                    str(pip_path), 'install', package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ Failed to install {package}")
                    print(f"   Error: {result.stderr}")
                    return False
            
            # Verify Google API client installation
            print("   Verifying Google API client...")
            python_path = venv_dir / 'bin' / 'python'
            result = subprocess.run([
                str(python_path), '-c', 
                'import googleapiclient.discovery; print("Google API client OK")'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ Google API client verification failed")
                return False
            else:
                print("   ✅ Google API client verified")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            if e.stderr:
                print(f"   Error details: {e.stderr}")
            return False
            
        return True

    def create_config_file(self) -> bool:
        """Create initial configuration file using ConfigProvider"""
        print("⚙️  Creating configuration file...")
        
        try:
            # Create default TOML configuration manually
            default_config = self._create_default_toml_config()
            
            # Add YouTube-specific configuration template
                def _create_default_toml_config(self) -> str:
        """Create default TOML configuration as string"""
        return '''[youtube_accounts]
# Add your YouTube accounts here
[[youtube_accounts]]
name = "default_account"
api_key = "YOUR_API_KEY_HERE"
client_id = "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET_HERE"
default_channel = "YOUR_CHANNEL_ID_HERE"
max_videos_per_day = 5
enabled = true

[upload_settings]
default_privacy = "private"
default_category = "22"
retry_attempts = 3
retry_delay = 300
chunk_size = 1048576

[metadata_mapping]
title = "title"
description = "comment"
tags = "keywords"
category = "genre"

[logging]
level = "INFO"
max_file_size = "10MB"
backup_count = 5

[editor]
command = ""

# YouTube API Configuration
[youtube_api]
# Get these from Google Cloud Console (https://console.cloud.google.com/)
# 1. Create a new project or select existing one
# 2. Enable YouTube Data API v3
# 3. Create credentials (OAuth 2.0 client ID for desktop application)
# 4. Download the client configuration and copy values below

client_id = "YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET_HERE"

# Daily upload limits (YouTube allows 6 uploads per day by default)
max_uploads_per_day = 6

# Default upload settings
default_privacy = "private"  # private, public, unlisted
default_category = "22"      # 22 = People & Blogs
made_for_kids = false
embeddable = true
public_stats_viewable = true

[quota_tracking]
# YouTube API quota management
daily_limit = 10000
reset_time = "00:00"  # UTC time when quota resets

[upload_settings]
# Upload behavior configuration
chunk_size_mb = 8          # Upload chunk size in megabytes
max_retries = 3            # Maximum retry attempts for failed uploads
retry_delay_seconds = 30   # Delay between retries
resume_incomplete = true   # Resume incomplete uploads on restart
'''
            
            # Write complete config to file
            with open(self.config_file, 'w') as f:
                f.write(default_config)
            
            print(f"   Configuration file created at: {self.config_file}")
            print("\n   █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█")
            print("   █  ⚠️  CRITICAL: YouTube API Setup Required!    █")
            print("   █                                               █")
            print("   █  1. Go to: https://console.cloud.google.com/ █")
            print("   █  2. Create project & enable YouTube API v3   █")
            print("   █  3. Create OAuth 2.0 credentials             █")
            print("   █  4. Edit config file with your credentials   █")
            print("   █                                               █")
            print("   █  PanQPlex WILL NOT WORK without these!       █")
            print("   █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█\n")
            
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return False
            
        return True

    def create_executable_script(self) -> bool:
        """Create the main executable script"""
        print("📜 Creating executable script...")
        
        script_content = f"""#!/bin/bash
# PanQPlex (pqpvsf) launcher script

INSTALL_DIR="{self.install_dir}"
VENV_DIR="$INSTALL_DIR/venv"
PYTHON="$VENV_DIR/bin/python"
MAIN_SCRIPT="$INSTALL_DIR/main.py"

# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ PanQPlex installation not found at $INSTALL_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python virtual environment not found"
    echo "   Please reinstall PanQPlex"
    exit 1
fi

# Check if main script exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Main script not found at $MAIN_SCRIPT"
    echo "   Please reinstall PanQPlex"
    exit 1
fi

# Activate virtual environment and run
cd "$INSTALL_DIR"
source "$VENV_DIR/bin/activate"
exec "$PYTHON" "$MAIN_SCRIPT" "$@"
"""
        
        script_path = self.bin_dir / 'pqpvsf'
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)

            print("   pqpvsf added to BIN, setting permissions...")
            script_path.chmod(0o755)
            
            # Verify script is accessible
            result = subprocess.run(['which', 'pqpvsf'], capture_output=True)
            if result.returncode == 0:
                print("   ✅ pqpvsf command available globally")
            else:
                print("   ⚠️  pqpvsf might not be in PATH")
            
        except Exception as e:
            print(f"❌ Failed to create executable script: {e}")
            return False
            
        return True

    def copy_source_files(self) -> bool:
        """Copy source files to install directory"""
        print("📋 Copying source files...")
        
        # Current directory where installer is running from
        source_dir = Path(__file__).parent
        
        # Core source files needed for PanQPlex (all in root directory)
        source_files = [
            'config.provider.py',
            'metadata.provider.py',
            'metadata.schema.py',
            'youtube.provider.py',
            'format_helper.py',
            'shell_helper.py',
            'display_helper.py'
        ]
        
        try:
            # Copy each source file from current directory to install directory
            for file in source_files:
                source_path = source_dir / file
                target_path = self.install_dir / file
                
                if source_path.exists():
                    print(f"   Copying {file}...")
                    with open(source_path, 'r') as src, open(target_path, 'w') as dst:
                        dst.write(src.read())
                else:
                    print(f"   ⚠️  Source file not found: {file}")
            
            # Create main.py in install directory
            main_py_path = self.install_dir / 'main.py'
            main_py_path.write_text(self._get_main_py_template())
            print("   Created main.py")
                        
        except Exception as e:
            print(f"❌ Failed to copy source files: {e}")
            return False
            
        return True

    def _get_main_py_template(self) -> str:
        """Get main.py template with basic CLI structure"""
        return """#!/usr/bin/env python3
\"\"\"
PanQPlex Main Entry Point
\"\"\"

import sys
import click
from pathlib import Path

@click.command()
@click.option('--setup', help='Setup platform (youtube)')
@click.option('--list', is_flag=True, help='List files')
@click.option('--sync', is_flag=True, help='Sync files')
@click.option('--check', is_flag=True, help='Check sync status')
@click.version_option(version='1.0.0', prog_name='PanQPlex')
def main(**kwargs):
    \"\"\"PanQPlex - Automated video sync and upload tool\"\"\"
    
    if kwargs.get('setup'):
        print(f"Setting up {kwargs['setup']}...")
        print("⚠️  Implementation in progress")
        
    elif kwargs.get('list'):
        print("Listing files...")
        print("⚠️  Implementation in progress")
        
    elif kwargs.get('sync'):
        print("Starting sync...")
        print("⚠️  Implementation in progress")
        
    elif kwargs.get('check'):
        print("Checking sync status...")
        print("⚠️  Implementation in progress")
        
    else:
        print("PanQPlex v1.0.0 - Video Sync & Upload Tool")
        print("Use --help for available commands")

if __name__ == '__main__':
    main()
"""

    def verify_installation(self) -> bool:
        """Verify installation is working"""
        print("🔍 Verifying installation...")
        
        try:
            # Test Python environment
            venv_python = self.install_dir / 'venv' / 'bin' / 'python'
            result = subprocess.run([
                str(venv_python), '-c', 
                'import sys; print(f"Python {sys.version}")'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ Python environment test failed")
                return False
            
            # Test Google API import
            result = subprocess.run([
                str(venv_python), '-c',
                'import googleapiclient.discovery; print("Google API: OK")'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ Google API import test failed")
                return False
            
            # Test FFmpeg
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            if result.returncode != 0:
                print("❌ FFmpeg test failed")
                return False
            
            print("   ✅ All components verified successfully")
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def install(self) -> bool:
        """Main installation process"""
        print("🚀 Installing PanQPlex with YouTube Provider...")
        print("═" * 60)
        
        steps = [
            ("Checking system requirements", self.check_system_requirements),
            ("Installing system packages", self.install_system_packages),
            ("Creating directories", self.create_directories),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Creating configuration file", self.create_config_file),
            ("Copying source files", self.copy_source_files),
            ("Creating executable script", self.create_executable_script),
            ("Verifying installation", self.verify_installation),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📌 {step_name}...")
            if not step_func():
                print(f"\n❌ Installation failed at: {step_name}")
                return False
                
        return True

    def post_install_info(self):
        """Display post-installation information"""
        print("\n" + "═" * 60)
        print("✅ PanQPlex with YouTube Provider installed successfully!")
        print("\n📋 Next steps:")
        print("1. 🔧 Configure YouTube API:")
        print("   • Go to: https://console.cloud.google.com/")
        print("   • Create project & enable YouTube Data API v3")
        print("   • Create OAuth 2.0 credentials")
        print(f"   • Edit: {self.config_file}")
        print("\n2. 🧪 Test installation:")
        print("   pqpvsf --help")
        print("   pqpvsf --setup youtube")
        print("\n3. 📁 Usage:")
        print("   cd /path/to/your/videos")
        print("   pqpvsf --list")
        print("   pqpvsf --sync")
        print("\n📂 Important locations:")
        print(f"   Config: {self.config_file}")
        print(f"   Logs: {self.logs_dir}")
        print(f"   Credentials: {self.install_dir}/credentials/")
        print("\n⚠️  Remember:")
        print("   • YouTube allows 6 uploads per day by default")
        print("   • Configure your Google API quota limits")
        print("   • Keep your credentials secure")

def main():
    installer = PQPVSFInstaller()
    
    print("PanQPlex Installer - YouTube Provider Edition")
    print("=" * 50)
    
    if installer.install():
        installer.post_install_info()
        sys.exit(0)
    else:
        print("\n❌ Installation failed!")
        print("Check the error messages above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
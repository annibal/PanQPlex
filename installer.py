#!/usr/bin/env python3
"""
PanQPlex Video Sync & Upload Tool - Installer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any

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
            'python3-venv'
        ]
        
        # Required Python packages
        self.python_packages = [
            'google-api-python-client',
            'google-auth-httplib2',
            'google-auth-oauthlib',
            'ffmpeg-python',
            'pymediainfo',
            'click',
            'tabulate',
            'colorama',
            'tqdm',
            'toml'
        ]

    def check_system_requirements(self) -> bool:
        """Check if running on supported system"""
        if sys.platform != 'linux':
            print("❌ PQPVSf only supports Linux (Ubuntu/Debian)")
            return False
        
        if os.geteuid() != 0:
            print("❌ Please run installer with sudo")
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
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system packages: {e}")
            return False
            
        return True

    def create_directories(self) -> bool:
        """Create necessary directories"""
        print("📁 Creating necessary directories...")
        
        try:
            self.install_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
            self.logs_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
            
            # Create package directories
            (self.install_dir / 'config').mkdir(exist_ok=True)
            (self.install_dir / 'metadata').mkdir(exist_ok=True)
            (self.install_dir / 'youtube').mkdir(exist_ok=True)
            (self.install_dir / 'status_check').mkdir(exist_ok=True)
            
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
            subprocess.run([
                sys.executable, '-m', 'venv', str(venv_dir)
            ], check=True, capture_output=True)
            
            # Install pip packages in venv
            pip_path = venv_dir / 'bin' / 'pip'
            
            for package in self.python_packages:
                print(f"   Installing {package}...")
                subprocess.run([
                    str(pip_path), 'install', package
                ], check=True, capture_output=True)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
            
        return True

    def create_init_files(self) -> bool:
        """Create __init__.py files for packages"""
        print("📄 Creating package __init__ files...")
        
        init_files = {
            '__init__.py': '''#!/usr/bin/env python3
"""
PanQPlex - Pankeimena QueuePlex Volitional Synchronization Framework
"""
__version__ = "1.0.0"
''',
            'config/__init__.py': '''"""PanQPlex Configuration Package"""
from .provider import ConfigProvider

__all__ = ["ConfigProvider"]
''',
            'metadata/__init__.py': '''"""PanQPlex Metadata Package"""
from .provider import MetadataProvider
from . import schemas

__all__ = ["MetadataProvider", "schemas"]
''',
            'youtube/__init__.py': '''"""PanQPlex YouTube Package"""
from .provider import YouTubeProvider

__all__ = ["YouTubeProvider"]
''',
            'status_check/__init__.py': '''"""PanQPlex Status Check Package"""
from .provider import StatusCheckProvider

__all__ = ["StatusCheckProvider"]
'''
        }
        
        try:
            for file_path, content in init_files.items():
                target_path = self.install_dir / file_path
                target_path.write_text(content)
                
        except Exception as e:
            print(f"❌ Failed to create __init__ files: {e}")
            return False
            
        return True

    def create_config_file(self) -> bool:
        """Create initial configuration file"""
        print("⚙️  Creating configuration file...")
        
        default_config = '''# PanQPlex Configuration File

[[youtube_accounts]]
name = "default_account"
api_key = "OAUTH2_TOKEN"
client_id = "YOUR_CLIENT_ID_HERE"
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
command = ""  # Will use $EDITOR if empty

[display]
default_columns = ["file_uuid", "upload_state", "title", "filename", "duration", "size", "last_sync"]
'''
        
        try:
            self.config_file.write_text(default_config)
            
            print(f"   Configuration file created at: {self.config_file}")
            print("\n   ╔═══════════════════════════════════════╗")
            print("   ║  ⚠️  Important!                       ║")
            print("   ║  Remember to edit the config file     ║")
            print("   ║  Add your YouTube OAuth2 credentials  ║")
            print("   ║  before using PanQPlex!               ║")
            print("   ╚═══════════════════════════════════════╝\n")
            
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return False
            
        return True

    def create_executable_script(self) -> bool:
        """Create the main executable script"""
        print("📜 Creating executable script...")
        
        script_content = f'''#!/bin/bash
# PanQPlex launcher script
cd {self.install_dir}
source venv/bin/activate
export PYTHONPATH="{self.install_dir}:$PYTHONPATH"
python3 pqpvsf.py "$@"
'''
        
        script_path = self.bin_dir / 'pqpvsf'
        
        try:
            script_path.write_text(script_content)
            script_path.chmod(0o755)
            print("   Executable 'pqpvsf' added to PATH")
            
        except Exception as e:
            print(f"❌ Failed to create executable script: {e}")
            return False
            
        return True

    def copy_source_files(self) -> bool:
        """Copy source files to install directory"""
        print("📋 Creating placeholder files...")
        
        # Create main entry point placeholder
        main_content = '''#!/usr/bin/env python3
"""
PanQPlex Main Entry Point
This file will be created after installation
"""

import click

@click.group()
def cli():
    """PanQPlex - Video Synchronization Tool"""
    pass

if __name__ == "__main__":
    cli()
'''
        
        try:
            (self.install_dir / 'pqpvsf.py').write_text(main_content)
            print("   Created main entry point placeholder")
            
        except Exception as e:
            print(f"❌ Failed to create placeholder files: {e}")
            return False
            
        return True

    def install(self) -> bool:
        """Main installation process"""
        print("\n🚀 Installing PanQPlex...")
        print("═" * 50)
        
        steps = [
            ("Checking system requirements", self.check_system_requirements),
            ("Installing system packages", self.install_system_packages),
            ("Creating directories", self.create_directories),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Creating __init__ files", self.create_init_files),
            ("Creating configuration file", self.create_config_file),
            ("Creating placeholder files", self.copy_source_files),
            ("Creating executable script", self.create_executable_script),
        ]
        
        for step_name, step_func in steps:
            print(f"\n▶ {step_name}...")
            if not step_func():
                return False
                
        return True

    def post_install_info(self):
        """Display post-installation information"""
        print("\n" + "═" * 50)
        print("✅ PanQPlex installed successfully!")
        print("═" * 50)
        print("\n📋 Next steps:")
        print("1. Configure YouTube OAuth2:")
        print(f"   sudo nano {self.config_file}")
        print("\n2. Copy your PanQPlex source files to:")
        print(f"   {self.install_dir}/")
        print("\n3. Test installation:")
        print("   pqpvsf --version")
        print("\n📚 Important paths:")
        print(f"   Config: {self.config_file}")
        print(f"   Logs:   {self.logs_dir}")
        print(f"   Install: {self.install_dir}")
        print("\n⚠️  Remember:")
        print("   - Add your YouTube OAuth2 credentials")
        print("   - You'll be prompted to authenticate on first use")
        print("   - Check ffmpeg is working: ffmpeg -version")

def main():
    installer = PQPVSFInstaller()
    
    if installer.install():
        installer.post_install_info()
        sys.exit(0)
    else:
        print("\n❌ Installation failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
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

# Import config provider to use its default config generation
sys.path.insert(0, str(Path(__file__).parent))
from config.provider import ConfigProvider

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
            print("   updating package list...")
            subprocess.run(['apt', 'update'], check=True, capture_output=True)
            
            # Install packages
            for package in self.system_packages:
                print(f"  Installing {package}...")
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
                print(f"  Installing {package} in the Venv...")
                subprocess.run([
                    str(pip_path), 'install', package
                ], check=True, capture_output=True)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
            
        return True

    def create_config_file(self) -> bool:
        """Create initial configuration file using ConfigProvider"""
        print("⚙️  Creating configuration file...")
        
        try:
            # Use ConfigProvider to create default configuration
            config_provider = ConfigProvider(str(self.config_file))
            
            print(f"   Configuration file created at: {self.config_file}.\n")
            print( "   █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█")
            print( "   █  ⚠️  Important!                     █")
            print( "   █  Remember to edit this file ASAP.   █")
            print( "   █  Add your YouTube API credentials   █")
            print( "   █  and configure your preferences.    █")
            print( "   █                                     █")
            print( "   █  PanQPlex won't work without them!  █")
            print( "   █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█\n\n")
            
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return False
            
        return True

    def create_executable_script(self) -> bool:
        """Create the main executable script"""
        print("📜 Creating executable script...")
        
        script_content = f"""#!/bin/bash
cd {self.install_dir}
source venv/bin/activate
python3 main.py "$@"
"""
        
        script_path = self.bin_dir / 'pqpvsf'
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)

            print("   pqpvsf added to BIN. setting permissions now...\n")
            script_path.chmod(0o755)
            
        except Exception as e:
            print(f"❌ Failed to create executable script: {e}")
            return False
            
        return True

    def copy_source_files(self) -> bool:
        """Copy source files to install directory"""
        print("📋 Copying source files...")
        
        # This would copy the actual source files
        # For now, we'll create placeholder files
        source_files = [
            'main.py',
            'config.py',
            'metadata.py',
            'youtube_api.py',
            'queue.py',
            'sync.py',
            'utils.py'
        ]
        
        try:
            for file in source_files:
                target_path = self.install_dir / file
                if not target_path.exists():
                    target_path.write_text(f'# {file} - To be implemented\n')
                    
        except Exception as e:
            print(f"❌ Failed to copy source files: {e}")
            return False
            
        return True

    def install(self) -> bool:
        """Main installation process"""
        print("🚀 Installing PanQPlex...")
        print("𑍟 " * 50)
        
        steps = [
            ("Checking system requirements", self.check_system_requirements),
            ("Installing system packages", self.install_system_packages),
            ("Creating directories", self.create_directories),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Creating configuration file", self.create_config_file),
            ("Copying source files", self.copy_source_files),
            ("Creating executable script", self.create_executable_script),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                return False
                
        return True

    def post_install_info(self):
        """Display post-installation information"""
        print("\n" + "𑍟 " * 50)
        print("✅ PQPVSf installed successfully!")
        print("\n📋 Next steps:")
        print(f"1. Edit configuration: pqpvsf --config --set")
        print(f"2. Add YouTube API credentials to: {self.config_file}")
        print("3. Test installation: pqpvsf --list")
        print("\n📚 Configuration file location:")
        print(f"   {self.config_file}")
        print("\n📝 Logs directory:")
        print(f"   {self.logs_dir}")
        print("\n⚠️  Important:")
        print("   - Configure YouTube API credentials before first use")
        print("   - Ensure ffmpeg is working: ffmpeg -version")
        print("   - Run 'pqpvsf --check' to verify setup")

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
#!/usr/bin/env python3
"""
Floorplan Genie - Production Server Launcher
Professional CAD Analysis & Îlot Placement Engine
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask', 'ezdxf', 'pdfplumber', 'shapely', 
        'matplotlib', 'cv2', 'numpy', 
        'PIL', 'scipy', 'networkx', 'skimage'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_directories():
    """Create necessary directories"""
    directories = ['uploads', 'static', 'output_files']
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Directory ready: {directory}/")

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                     FLOORPLAN GENIE                         ║
║              Professional CAD Analysis Engine               ║
║                                                              ║
║  🏗️  Advanced CAD Processing    🧠 AI-Powered Placement     ║
║  📐 Corridor Network Generation  🎨 Professional Rendering  ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    """Main application launcher"""
    print_banner()
    
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("✓ All dependencies installed")
    
    # Setup directories
    setup_directories()
    
    # Import and run Flask app
    try:
        from app import app
        
        print("\n🚀 Starting Floorplan Genie server...")
        print("📍 Access the application at: http://localhost:5000")
        print("🔗 API endpoint: http://localhost:5000/api/process")
        print("📚 Documentation: http://localhost:5000/about")
        print("\n⚡ Server starting...\n")
        
        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Floorplan Genie server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
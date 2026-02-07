"""
Download required static assets for offline use in air-gapped environment.

This script downloads:
1. Bulma CSS Framework
2. Animate.css
3. Alpine.js
4. Chart.js
5. Font Awesome

Run this script on a machine with internet access, then copy the entire project
to the air-gapped Windows machine.
"""

import os
import urllib.request
import sys

# Asset URLs
ASSETS = {
    'bulma.css': {
        'url': 'https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css',
        'path': 'static/css/bulma.min.css',
        'description': 'Bulma CSS v0.9.4'
    },
    'animate.css': {
        'url': 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css',
        'path': 'static/css/animate.min.css',
        'description': 'Animate.css v4.1.1'
    },
    'fontawesome.css': {
        'url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
        'path': 'static/css/fontawesome.min.css',
        'description': 'Font Awesome v6.5.1'
    },
    'alpine.min.js': {
        'url': 'https://cdn.jsdelivr.net/npm/alpinejs@3.13.5/dist/cdn.min.js',
        'path': 'static/js/alpine.min.js',
        'description': 'Alpine.js v3.13.5'
    },
    'chart.min.js': {
        'url': 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
        'path': 'static/js/chart.min.js',
        'description': 'Chart.js v4.4.1'
    }
}


def download_file(url, destination):
    """Download a file from URL to destination."""
    try:
        print(f"  Downloading from {url}...")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download the file
        urllib.request.urlretrieve(url, destination)
        
        # Get file size
        file_size = os.path.getsize(destination)
        file_size_kb = file_size / 1024
        
        print(f"  ✓ Downloaded successfully ({file_size_kb:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Error downloading: {e}")
        return False


def main():
    """Main function to download all assets."""
    print("=" * 60)
    print("TLC Nexus - Static Assets Downloader")
    print("=" * 60)
    print()
    
    success_count = 0
    total_count = len(ASSETS)
    
    for name, asset in ASSETS.items():
        print(f"Downloading {asset['description']}...")
        
        if download_file(asset['url'], asset['path']):
            success_count += 1
        
        print()
    
    print("=" * 60)
    print(f"Download complete: {success_count}/{total_count} assets downloaded")
    print("=" * 60)
    print()
    
    if success_count == total_count:
        print("✓ All assets downloaded successfully!")
        print()
        print("Next steps:")
        print("1. Copy the entire project folder to the air-gapped machine")
        print("2. Run 'run_nexus.bat' to start the application")
        print()
        return 0
    else:
        print("⚠ Some assets failed to download.")
        print("Please check your internet connection and try again.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

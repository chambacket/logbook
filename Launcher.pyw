import subprocess
import os
import time
import webbrowser
import socket
import sys
from pathlib import Path

# Simple launcher - no heavy dependencies
class SimpleLauncher:
    def __init__(self):
        # IMPORTANT: Update this path to match your actual project location
        # Example: r"C:\Users\YourName\Documents\faculty-borrowing-system"
        self.PROJECT_PATH = r"C:\Users\ASPIRE\OneDrive\Desktop\2s-3\Integration\logbook"  # CHANGE THIS!
        
        self.port = 5000
        self.process = None
        
    def check_project_path(self):
        """Check if project path is configured and valid."""
        if "YourName" in self.PROJECT_PATH:
            print("\n" + "="*60)
            print("ERROR: Project path not configured!")
            print("="*60)
            print("\nPlease edit this script and update PROJECT_PATH to your actual project location.")
            print("Example: r\"C:\\Users\\John\\Documents\\my-project\"")
            print("\nCurrent path:", self.PROJECT_PATH)
            input("\nPress Enter to exit...")
            return False
            
        app_path = os.path.join(self.PROJECT_PATH, 'app.py')
        if not os.path.exists(app_path):
            print("\n" + "="*60)
            print("ERROR: app.py not found!")
            print("="*60)
            print(f"\nLooking for: {app_path}")
            print("Please check that the PROJECT_PATH is correct.")
            input("\nPress Enter to exit...")
            return False
            
        return True
    
    def kill_port(self):
        """Kill any process using our port."""
        if os.name == 'nt':  # Windows
            # Kill any process using port 5000
            os.system(f'netstat -ano | findstr :{self.port} > temp.txt 2>nul')
            try:
                with open('temp.txt', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'LISTENING' in line:
                            parts = line.strip().split()
                            pid = parts[-1]
                            os.system(f'taskkill /F /PID {pid} >nul 2>&1')
                os.remove('temp.txt')
            except:
                pass
    
    def get_local_ip(self):
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def wait_for_server(self, timeout=30):
        """Wait for Flask server to start."""
        print("\nStarting Flask server", end='')
        for i in range(timeout):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', self.port))
                sock.close()
                if result == 0:
                    print(" ✓")
                    return True
            except:
                pass
            print(".", end='', flush=True)
            time.sleep(1)
        print(" ✗")
        return False
    
    def run(self):
        """Main execution."""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("="*60)
        print("Faculty Borrowing Logbook System - Launcher")
        print("="*60)
        
        # Check configuration
        if not self.check_project_path():
            return
        
        # Change to project directory
        os.chdir(self.PROJECT_PATH)
        print(f"\nProject directory: {self.PROJECT_PATH}")
        
        # Kill any existing processes on our port
        print("\nChecking for existing processes...")
        self.kill_port()
        time.sleep(2)
        
        # Start Flask in a new window
        print("\nStarting Flask application...")
        if os.name == 'nt':  # Windows
            # Start in a new minimized console window
            self.process = subprocess.Popen(
                f'start "Flask Server" /MIN python app.py',
                shell=True
            )
        else:  # Linux/Mac
            self.process = subprocess.Popen(
                ['python3', 'app.py'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Wait for server to start
        if not self.wait_for_server():
            print("\n❌ Failed to start Flask server!")
            print("Please check if all dependencies are installed.")
            input("\nPress Enter to exit...")
            return
        
        # Get local IP
        local_ip = self.get_local_ip()
        
        print("\n✅ Server is running!")
        print(f"\n📡 Access URLs:")
        print(f"   • Local:     http://localhost:{self.port}")
        print(f"   • Network:   http://{local_ip}:{self.port}")
        
        # Open browser
        print("\nOpening browser...")
        webbrowser.open(f'http://localhost:{self.port}')
        
        print("\n" + "="*60)
        print("Server is running in the background.")
        print("\nTo stop the server:")
        print("  1. Close this window, OR")
        print("  2. Press Ctrl+C")
        print("="*60)
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            # Cleanup
            if os.name == 'nt':
                os.system(f'taskkill /F /FI "WINDOWTITLE eq Flask Server*" >nul 2>&1')
                self.kill_port()
            else:
                if self.process:
                    self.process.terminate()
            print("Server stopped.")

# Create a batch file creator
def create_batch_file():
    """Create a simple batch file for even easier launching."""
    batch_content = '''@echo off
title Faculty Borrowing System
cd /d "{project_path}"
echo Starting Faculty Borrowing System...
echo.
python app.py
pause
'''
    
    print("\n" + "="*40)
    print("Batch File Creator")
    print("="*40)
    print("\nThis will create a simple .bat file to run your Flask app.")
    project_path = input("\nEnter your project path: ").strip()
    
    if not os.path.exists(os.path.join(project_path, 'app.py')):
        print("Error: app.py not found in that directory!")
        return
    
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    bat_file = os.path.join(desktop, 'Start_FBLS.bat')
    
    with open(bat_file, 'w') as f:
        f.write(batch_content.format(project_path=project_path))
    
    print(f"\n✅ Created: {bat_file}")
    print("You can now double-click 'Start_FBLS.bat' on your desktop!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--create-batch':
        create_batch_file()
    else:
        launcher = SimpleLauncher()
        launcher.run()
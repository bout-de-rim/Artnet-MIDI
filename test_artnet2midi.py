import subprocess
import time
import os
import signal

def test_startup():
    try:
        # Start the application
        process = subprocess.Popen(['./dist/artnet2midi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Application started successfully")
        
        # Wait for a few seconds to ensure it's running
        time.sleep(10)
        
        # Check if the process is still running
        if process.poll() is None:
            print("Application is running")
        else:
            raise Exception("Application terminated unexpectedly")
        
        # Terminate the application
        process.terminate()
        process.wait()
        print("Application terminated successfully")
    
    except Exception as e:
        print(f"Startup test failed: {e}")
        if process.poll() is None:
            process.terminate()
            process.wait()
        exit(1)

if __name__ == "__main__":
    test_startup()

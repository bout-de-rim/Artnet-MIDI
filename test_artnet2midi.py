import subprocess
import time
import os
import signal

def test_startup():
    try:
        # Open log files
        stdout_log = open("stdout.log", "w")
        stderr_log = open("stderr.log", "w")
        
        # Start the application
        process = subprocess.Popen(['./dist/artnet2midi.app'], stdout=stdout_log, stderr=stderr_log)
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
        exit(0)
    finally:
        # Close log files
        stdout_log.close()
        stderr_log.close()

if __name__ == "__main__":
    test_startup()

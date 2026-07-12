import uvicorn
import subprocess
import threading
import time
import re
import sys
import api

def start_pinggy_tunnel():
    print("Starting Pinggy tunnel (No account required)...")
    
    # Start SSH tunnel to pinggy.io
    # -p 443 connects to port 443
    # -R0:localhost:8000 forwards a random remote port to local 8000
    # -o StrictHostKeyChecking=no prevents the prompt
    # -o ServerAliveInterval=30 keeps the connection alive
    cmd = ["ssh", "-p", "443", "-R0:localhost:8000", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "a.pinggy.io"]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        # Parse the output to find the URL
        url_found = False
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            # Pinggy prints the URL like: http://rnzha-2401-4900-1c5c-7d94-a131-a08f-bfd6-84d4.a.free.pinggy.link
            if "http://" in line and "pinggy" in line:
                # Extract URL using regex
                match = re.search(r'(http://[^\s]+)', line)
                if match:
                    url = match.group(1)
                    print(f"\n=======================================================")
                    print(f"TUNNEL CREATED SUCCESSFULLY!")
                    print(f"Public URL: {url}")
                    print(f"Enter this URL in the app's 'API SERVER URL' field.")
                    print(f"=======================================================\n")
                    url_found = True
                    break
                    
        if not url_found:
            print("Failed to parse tunnel URL from SSH output.")
            
    except Exception as e:
        print(f"Failed to start SSH tunnel: {e}")
        print("Please ensure you have SSH installed (built into Windows 10/11).")

if __name__ == "__main__":
    # Start the tunnel in a background thread
    tunnel_thread = threading.Thread(target=start_pinggy_tunnel, daemon=True)
    tunnel_thread.start()
    
    # Give it a second to connect before starting the API
    time.sleep(2)
    
    # Start the FastAPI server on the main thread
    print("Starting API Server...")
    uvicorn.run(api.app, host="0.0.0.0", port=8000)

import uvicorn
from pyngrok import ngrok
import sys
import api

def start_tunnel():
    print("Starting ngrok tunnel...")
    # Open a ngrok tunnel to the dev server
    try:
        public_url = ngrok.connect(8000).public_url
        print(f"\n=======================================================")
        print(f"NGROK TUNNEL CREATED SUCCESSFULLY!")
        print(f"Public URL: {public_url}")
        print(f"Enter this URL in the app's 'API SERVER URL' field.")
        print(f"=======================================================\n")
    except Exception as e:
        print(f"Failed to start ngrok: {e}")
        print("You might need to add an auth token. You can sign up at https://ngrok.com/ and then run: pyngrok config add-authtoken <token>")
        sys.exit(1)

    # Start the FastAPI server
    uvicorn.run(api.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_tunnel()

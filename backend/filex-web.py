"""
FileX Web Server Entrypoint

Run this script to start the FileX web server. The server loads embedding models
once at startup and keeps them in memory for fast API responses.

Usage:
    python filex-web.py [--host HOST] [--port PORT]

To stop the server, press Ctrl+C or send a shutdown signal.
"""
import argparse
import signal
import sys
import os
import uvicorn
from pathlib import Path


def signal_handler(sig, frame):
    """
    Handle shutdown signals gracefully.
    
    :param sig: Signal number
    :param frame: Current stack frame
    """
    print("\n\nShutting down FileX web server...")
    print("Cleaning up resources...")
    # Flush stdout to ensure message is printed
    sys.stdout.flush()
    # Exit immediately without waiting
    os._exit(0)


def main():
    """
    Main entry point for FileX web server.
    """
    parser = argparse.ArgumentParser(
        description="FileX Web Server - Semantic file indexing and search API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1, localhost only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (not recommended for production)",
    )
    
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("FileX Web Server")
    print("=" * 60)
    print(f"Starting server on http://{args.host}:{args.port}")
    print(f"API documentation: http://{args.host}:{args.port}/docs")
    print(f"Alternative docs: http://{args.host}:{args.port}/redoc")
    print()
    print("Note: Models will be loaded on first request or at startup.")
    print("This may take 5-10 seconds on first run.")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        uvicorn.run(
            "src.web_app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
            access_log=False,  # Disable access logs to reduce output
        )
    except KeyboardInterrupt:
        print("\n\nShutting down FileX web server...")
        print("Cleaning up resources...")
        sys.stdout.flush()
        os._exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🎧 Starting Product Service Consumer...")
    
    # Wait for services to be ready
    print("⏳ Waiting 10 seconds for services to initialize...")
    time.sleep(10)
    
    try:
        from src.app.messaging import start_consumer
        start_consumer()
    except Exception as e:
        print(f"❌ Failed to start consumer: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
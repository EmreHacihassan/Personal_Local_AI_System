#!/usr/bin/env python3
"""Comprehensive endpoint testing script - OUTPUT TO FILE."""

import requests
import json
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8001"
OUTPUT_FILE = "TEST_RESULTS.txt"

def write_result(message):
    """Write result to file."""
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

def test_health():
    write_result("\n1. Health Check:")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=30)
        data = r.json()
        write_result(f"   ✅ Status: {data.get('status')}")
        write_result(f"   ✅ Checks: {len(data.get('checks', {}))}")
        return True
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_voice_status():
    write_result("\n2. Voice Status:")
    try:
        r = requests.get(f"{BASE_URL}/api/voice/status", timeout=30)
        data = r.json()
        write_result(f"   TTS: {data.get('tts_available')}")
        write_result(f"   STT: {data.get('stt_available')}")
        write_result(f"   Vision: {data.get('vision_available')}")
        return True
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_screen_status():
    write_result("\n3. Screen Capture Status:")
    try:
        r = requests.get(f"{BASE_URL}/api/screen/status", timeout=30)
        data = r.json()
        write_result(f"   Available: {data.get('available')}")
        write_result(f"   Vision: {data.get('vision_available')}")
        write_result(f"   Backend: {data.get('capture_backend')}")
        return True
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_documents():
    write_result("\n4. Documents:")
    try:
        r = requests.get(f"{BASE_URL}/api/documents", timeout=30)
        write_result(f"   ✅ Status: {r.status_code}")
        return True
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_screen_capture():
    write_result("\n5. Screen Capture Test:")
    try:
        r = requests.post(f"{BASE_URL}/api/screen/capture", json={"mode": "primary"}, timeout=30)
        data = r.json()
        if data.get("success"):
            write_result(f"   ✅ Width: {data.get('width')}")
            write_result(f"   ✅ Height: {data.get('height')}")
            write_result(f"   ✅ Screenshot ID: {data.get('screenshot_id')}")
        else:
            write_result(f"   ⚠️ Error: {data.get('error')}")
        return data.get("success", False)
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_monitors():
    write_result("\n6. Monitors List:")
    try:
        r = requests.get(f"{BASE_URL}/api/screen/monitors", timeout=30)
        data = r.json()
        if data.get("success"):
            write_result(f"   ✅ Total monitors: {data.get('count')}")
            for i, mon in enumerate(data.get('monitors', [])):
                write_result(f"      Monitor {i}: {mon.get('width')}x{mon.get('height')}")
        return data.get("success", False)
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_tts():
    write_result("\n7. TTS Test:")
    try:
        r = requests.post(f"{BASE_URL}/api/voice/tts", json={"text": "Test mesajı"}, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if data.get("audio"):
                write_result(f"   ✅ Audio generated (length: {len(data.get('audio', ''))})")
            elif data.get("success"):
                write_result(f"   ✅ TTS successful")
            else:
                write_result(f"   ⚠️ Response keys: {list(data.keys())}")
        else:
            write_result(f"   ⚠️ Status: {r.status_code}")
        return True
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def test_rag_sync():
    write_result("\n8. RAG Sync Status:")
    try:
        r = requests.get(f"{BASE_URL}/api/rag/sync-status", timeout=30)
        data = r.json()
        write_result(f"   ✅ Status retrieved")
        return True
    except Exception as e:
        write_result(f"   ❌ Error: {e}")
        return False

def main():
    # Clear old results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("   KAPSAMLI ENDPOINT TESTLERİ\n")
        f.write("=" * 60 + "\n")
    
    results = {
        "Health": test_health(),
        "Voice Status": test_voice_status(),
        "Screen Status": test_screen_status(),
        "Documents": test_documents(),
        "Screen Capture": test_screen_capture(),
        "Monitors": test_monitors(),
        "TTS": test_tts(),
        "RAG Sync": test_rag_sync(),
    }
    
    write_result("\n" + "=" * 60)
    write_result("   SONUÇLAR")
    write_result("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        write_result(f"   {status} {name}")
    
    write_result(f"\n   Toplam: {passed}/{total} test başarılı")
    write_result("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"\nFATAL ERROR: {e}\n")
        print(f"FATAL: {e}")

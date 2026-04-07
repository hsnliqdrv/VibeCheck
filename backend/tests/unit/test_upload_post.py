"""
Test script for post image upload to DigitalOcean Spaces

Usage:
    python tests/unit/test_upload_post.py

Run from backend directory for predictable relative paths.

This script:
1. Authenticates with the API
2. Gets a presigned URL for post image upload
3. Uploads example.png to the presigned URL
"""

import requests
import sys
import os
from pathlib import Path

BASE_URL = "http://localhost:3000/api/v1"

# Test credentials
TEST_EMAIL = "testpostupload@example.com"
TEST_PASSWORD = "TestPassword123"


def log(message: str, status: str = "INFO"):
    """Simple logging function"""
    print(f"[{status}] {message}")


def register_or_login():
    """Register or login to get JWT token"""
    log("Step 1: Attempting to register/login user...", "INFO")
    
    # Try to register first
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": "testpostupload"
        }
    )
    
    if register_response.status_code == 201:
        log(f"User registered successfully", "SUCCESS")
    elif register_response.status_code == 409:
        log(f"User already exists, logging in instead", "INFO")
    else:
        log(f"Registration failed: {register_response.text}", "ERROR")
        return None
    
    # Login to get token
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if login_response.status_code != 200:
        log(f"Login failed: {login_response.text}", "ERROR")
        return None
    
    token = login_response.json().get("token")
    if not token:
        log(f"No token in response: {login_response.json()}", "ERROR")
        return None
    log(f"Login successful, token: {token[:20]}...", "SUCCESS")
    return token


def get_presigned_url(token: str, file_extension: str = "png"):
    """Get presigned URL for post image upload"""
    log(f"Step 2: Getting presigned URL for {file_extension} file...", "INFO")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/upload/post?file_extension={file_extension}",
        headers=headers
    )
    
    if response.status_code != 200:
        log(f"Failed to get presigned URL: {response.text}", "ERROR")
        return None
    
    data = response.json()
    log(f"Presigned URL obtained successfully", "SUCCESS")
    print(f"  - File Key: {data.get('file_key')}")
    print(f"  - Post ID: {data.get('post_id')}")
    print(f"  - Max Size: {data.get('max_size_bytes')} bytes")
    print(f"  - Allowed Types: {data.get('allowed_types')}")
    print(f"  - Expires In: {data.get('expires_in_seconds')} seconds")
    print(f"  - Presigned URL: {data.get('presigned_url')}")
    print(f"  - CDN URL: {data.get('cdn_url')}")
    
    return data


def upload_file(presigned_url: str, file_path: str):
    """Upload file to presigned URL using PUT"""
    log(f"Step 3: Uploading {file_path}...", "INFO")
    
    # Check if file exists
    if not os.path.exists(file_path):
        log(f"File not found: {file_path}", "ERROR")
        return False
    
    # Get file size
    file_size = os.path.getsize(file_path)
    log(f"File size: {file_size} bytes", "INFO")
    
    # Read and upload file
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    log(f"Uploading to presigned URL...", "INFO")
    print(f"  - URL: {presigned_url[:100]}...")
    
    # Try with Content-Type header
    response = requests.put(
        presigned_url,
        data=file_data,
        headers={
            "Content-Type": "image/png",
            "x-amz-acl": "public-read"
        }
    )
    
    if response.status_code in [200, 201]:
        log(f"File uploaded successfully!", "SUCCESS")
        return True
    else:
        log(f"Upload failed (Status {response.status_code})", "ERROR")
        print(f"Response: {response.text[:500]}")
        
        # Try without Content-Type header as fallback
        log(f"Retrying without Content-Type header...", "INFO")
        response2 = requests.put(
            presigned_url,
            data=file_data
        )
        
        if response2.status_code in [200, 201]:
            log(f"File uploaded successfully (without Content-Type)!", "SUCCESS")
            return True
        else:
            log(f"Upload still failed (Status {response2.status_code})", "ERROR")
            print(f"Response: {response2.text[:500]}")
            return False


def main():
    """Main test execution"""
    log("Starting post image upload test...", "INFO")
    print()
    
    # Step 1: Get token
    token = register_or_login()
    if not token:
        log("Authentication failed, exiting", "ERROR")
        sys.exit(1)
    print()
    
    # Step 2: Get presigned URL
    presigned_data = get_presigned_url(token, "png")
    if not presigned_data:
        log("Failed to get presigned URL, exiting", "ERROR")
        sys.exit(1)
    print()
    
    # Step 3: Upload file
    # Look for example.png in the tests directory
    test_dir = Path(__file__).parent
    example_file = test_dir / "example.png"
    
    if not example_file.exists():
        log(f"example.png not found in {test_dir}", "WARNING")
        log("Creating a minimal test PNG file...", "INFO")
        # Create a minimal 1x1 PNG programmatically
        try:
            import struct
            import zlib
            
            # Minimal PNG: 1x1 pixel, red
            width, height = 1, 1
            
            # PNG header
            png_header = b'\x89PNG\r\n\x1a\n'
            
            # IHDR chunk (image header)
            ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
            ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            
            # IDAT chunk (image data) - red pixel
            raw_data = b'\x00\xff\x00\x00'  # filter byte + RGB red
            compressed_data = zlib.compress(raw_data)
            idat_crc = zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff
            idat_chunk = struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data + struct.pack('>I', idat_crc)
            
            # IEND chunk (image end)
            iend_crc = zlib.crc32(b'IEND') & 0xffffffff
            iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
            
            # Write PNG file
            with open(example_file, 'wb') as f:
                f.write(png_header + ihdr_chunk + idat_chunk + iend_chunk)
            
            log(f"Created minimal test PNG at {example_file}", "SUCCESS")
        except Exception as e:
            log(f"Failed to create test PNG: {e}", "ERROR")
            sys.exit(1)
    
    success = upload_file(presigned_data['presigned_url'], str(example_file))
    print()
    
    if success:
        log("Post image upload test completed successfully!", "SUCCESS")
        file_key = presigned_data.get('file_key', 'unknown')
        post_id = presigned_data.get('post_id', 'unknown')
        cdn_url = presigned_data.get('cdn_url', 'unknown')
        log(f"Post image accessible at: {cdn_url}", "INFO")
        log(f"Post ID: {post_id}", "INFO")
    else:
        log("Post image upload test failed", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()

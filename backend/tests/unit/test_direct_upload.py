"""
Direct upload test - tests presigned URL directly without the test framework

Usage (from backend directory):
    python tests/unit/test_direct_upload.py

Optional path overrides (otherwise current directory is used):
    DOTENV_PATH=/absolute/path/to/.env python tests/unit/test_direct_upload.py
    TEST_FILE_PATH=/absolute/path/to/example.png python tests/unit/test_direct_upload.py
"""
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from explicit path when provided, otherwise current directory.
dotenv_path = Path(os.getenv("DOTENV_PATH", Path.cwd() / ".env"))
load_dotenv(dotenv_path)

BASE_URL = "http://localhost:3000/api/v1"
TEST_EMAIL = "directupload@example.com"
TEST_PASSWORD = "TestPassword123"

# Test file path can be specified; defaults to current directory.
test_file = Path(os.getenv("TEST_FILE_PATH", Path.cwd() / "example.png"))

if not test_file.exists():
    print(f"ERROR: {test_file} not found")
    exit(1)

print("[1] Getting JWT token...")
# Register/login
reg_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "username": "directupload"}
)

login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
)

if login_response.status_code != 200:
    print(f"ERROR: Login failed - {login_response.text}")
    exit(1)

token = login_response.json().get("token")
print(f"✓ Token obtained\n")

print("[2] Getting presigned URL...")
headers = {"Authorization": f"Bearer {token}"}
url_response = requests.post(
    f"{BASE_URL}/upload/avatar?file_extension=png",
    headers=headers
)

if url_response.status_code != 200:
    print(f"ERROR: Failed to get presigned URL - {url_response.text}")
    exit(1)

data = url_response.json()
presigned_url = data['presigned_url']
print(f"✓ Presigned URL obtained")
print(f"  File key: {data['file_key']}")
print(f"  URL: {presigned_url[:100]}...\n")

# Read file
with open(test_file, 'rb') as f:
    file_data = f.read()

print(f"[3] Testing upload (file size: {len(file_data)} bytes)...\n")

# Try 1: With Content-Type header
print("[Attempt 1] Upload WITH Content-Type: image/png header...")
response1 = requests.put(
    presigned_url,
    data=file_data,
    headers={"Content-Type": "image/png"}
)
print(f"  Status: {response1.status_code}")
if response1.status_code in [200, 201]:
    print("  ✓ SUCCESS!\n")
    exit(0)
else:
    print(f"  Error: {response1.text[:200]}\n")

# Try 2: Without headers
print("[Attempt 2] Upload WITHOUT custom headers...")
response2 = requests.put(
    presigned_url,
    data=file_data
)
print(f"  Status: {response2.status_code}")
if response2.status_code in [200, 201]:
    print("  ✓ SUCCESS!\n")
    exit(0)
else:
    print(f"  Error: {response2.text[:200]}\n")

# Try 3: With empty Content-Type
print("[Attempt 3] Upload with empty Content-Type...")
response3 = requests.put(
    presigned_url,
    data=file_data,
    headers={"Content-Type": ""}
)
print(f"  Status: {response3.status_code}")
if response3.status_code in [200, 201]:
    print("  ✓ SUCCESS!\n")
    exit(0)
else:
    print(f"  Error: {response3.text[:200]}\n")

print("All upload attempts failed. Check your presigned URL and DigitalOcean Spaces configuration.")


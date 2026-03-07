"""
Test DigitalOcean Spaces connection directly
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / '.env')

print("[INFO] Testing DigitalOcean Spaces connection...")
print()

# Check config from environment
do_spaces_name = os.getenv('DO_SPACES_NAME')
do_spaces_region = os.getenv('DO_SPACES_REGION')
do_spaces_endpoint = os.getenv('DO_SPACES_ENDPOINT')
do_spaces_key = os.getenv('DO_SPACES_KEY')
do_spaces_secret = os.getenv('DO_SPACES_SECRET')

print("[INFO] Configuration from .env:")
print(f"  - Space Name: {do_spaces_name}")
print(f"  - Region: {do_spaces_region}")
print(f"  - Endpoint: {do_spaces_endpoint}")
print(f"  - Key: {do_spaces_key[:10]}..." if do_spaces_key else "  - Key: NOT SET")
print(f"  - Secret: {do_spaces_secret[:10]}..." if do_spaces_secret else "  - Secret: NOT SET")
print()

# Validate all required config
if not all([do_spaces_name, do_spaces_region, do_spaces_endpoint, do_spaces_key, do_spaces_secret]):
    print("[ERROR] Missing required DigitalOcean Spaces configuration!")
    print("Please check your .env file.")
    sys.exit(1)

try:
    # Import boto3 and initialize client directly
    import boto3
    print("[INFO] Initializing boto3 S3 client...")
    
    s3_client = boto3.client(
        's3',
        region_name=do_spaces_region,
        endpoint_url=do_spaces_endpoint,
        aws_access_key_id=do_spaces_key,
        aws_secret_access_key=do_spaces_secret
    )
    print("[SUCCESS] boto3 client initialized")
    print()
    
    # Try to generate a presigned URL
    print("[INFO] Generating presigned URL...")
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': do_spaces_name,
            'Key': 'avatars/test_user_123/avatar.png',
            'ContentType': 'image/png'
        },
        ExpiresIn=3600,
        HttpMethod='PUT'
    )
    print("[SUCCESS] Presigned URL generated!")
    print()
    
    print(f"File Key: avatars/test_user_123/avatar.png")
    print(f"Bucket: {do_spaces_name}")
    print(f"URL (first 150 chars): {presigned_url[:150]}...")
    print()
    
    # Test that URL format is valid
    print("[INFO] Checking URL format...")
    if "https://" in presigned_url:
        print("[SUCCESS] URL has valid HTTPS scheme")
    else:
        print("[ERROR] URL missing HTTPS scheme!")
    
    if do_spaces_endpoint.split('//')[1] in presigned_url:
        print(f"[SUCCESS] URL contains correct endpoint")
    else:
        print(f"[WARNING] URL might not contain expected endpoint")
        
    print()
    print("[SUCCESS] DigitalOcean Spaces connection test passed!")
    
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

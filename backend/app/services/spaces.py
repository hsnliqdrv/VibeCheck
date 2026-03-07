"""
DigitalOcean Spaces service for handling uploads
"""
import boto3
from botocore.exceptions import ClientError
from flask import current_app
import uuid
import logging

logger = logging.getLogger(__name__)


class SpacesService:
    """Service for interacting with DigitalOcean Spaces"""
    
    def __init__(self):
        """Initialize the Spaces service with boto3 client"""
        try:
            # Normalize endpoint to regional S3 API endpoint and use virtual-hosted style.
            # This avoids storing keys with an unintended bucket-name prefix.
            region = current_app.config['DO_SPACES_REGION']
            configured_endpoint = current_app.config['DO_SPACES_ENDPOINT']
            endpoint_url = self._normalize_spaces_endpoint(configured_endpoint, region)
            s3_config = boto3.session.Config(s3={'addressing_style': 'virtual'})
            
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                endpoint_url=endpoint_url,
                aws_access_key_id=current_app.config['DO_SPACES_KEY'],
                aws_secret_access_key=current_app.config['DO_SPACES_SECRET'],
                config=s3_config
            )
            self.bucket_name = current_app.config['DO_SPACES_NAME']
            logger.info(
                f"SpacesService initialized with bucket: {self.bucket_name}, "
                f"region: {region}, endpoint: {endpoint_url}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize SpacesService: {str(e)}")
            raise

    def _normalize_spaces_endpoint(self, endpoint: str, region: str) -> str:
        """Return a regional Spaces API endpoint usable for S3 operations."""
        if not endpoint:
            return f"https://{region}.digitaloceanspaces.com"

        lowered = endpoint.lower()
        # If user passed CDN endpoint or bucket endpoint, force regional API endpoint.
        if ".cdn.digitaloceanspaces.com" in lowered or lowered.startswith("https://"):
            if f"https://{region}.digitaloceanspaces.com" == endpoint:
                return endpoint

        if lowered.endswith(f".{region}.digitaloceanspaces.com") and lowered.count(".") >= 3:
            return f"https://{region}.digitaloceanspaces.com"

        return endpoint
    
    def generate_avatar_presigned_url(self, user_id: str, file_extension: str) -> dict:
        """
        Generate a presigned URL for avatar upload
        
        Args:
            user_id: The user ID
            file_extension: File extension (jpg, png, webp)
        
        Returns:
            Dictionary with presigned URL and file key
        
        Note: Each user can only have one avatar. New uploads overwrite the previous one.
        """
        # Validate file extension
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
        if file_extension.lower() not in allowed_extensions:
            raise ValueError(f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
        
        # Use consistent key per user (overwrites previous avatar)
        file_key = f"avatars/{user_id}/avatar.{file_extension.lower()}"
        
        try:
            # Generate presigned PUT URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': self._get_content_type(file_extension),
                    'ACL': 'public-read'
                },
                ExpiresIn=current_app.config['PRESIGNED_URL_EXPIRY'],
                HttpMethod='PUT'
            )
            
            logger.info(f"Generated presigned URL for avatar: {file_key}")
            return {
                'presigned_url': presigned_url,
                'file_key': file_key,
                'bucket': self.bucket_name
            }
        except ClientError as e:
            error_msg = f"Failed to generate presigned URL: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def generate_post_image_presigned_url(self, user_id: str, file_extension: str) -> dict:
        """
        Generate a presigned URL for post image upload
        
        Args:
            user_id: The user ID
            file_extension: File extension (jpg, png, webp, gif)
        
        Returns:
            Dictionary with presigned URL and file key
        """
        # Validate file extension
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp', 'gif']
        if file_extension.lower() not in allowed_extensions:
            raise ValueError(f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
        
        # Generate unique key
        post_id = str(uuid.uuid4())
        file_key = f"posts/{user_id}/{post_id}/image.{file_extension.lower()}"
        
        try:
            # Generate presigned PUT URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': self._get_content_type(file_extension),
                    'ACL': 'public-read'
                },
                ExpiresIn=current_app.config['PRESIGNED_URL_EXPIRY'],
                HttpMethod='PUT'
            )
            
            return {
                'presigned_url': presigned_url,
                'file_key': file_key,
                'bucket': self.bucket_name,
                'post_id': post_id
            }
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    def _get_content_type(self, file_extension: str) -> str:
        """Map file extension to MIME type"""
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif'
        }
        return mime_types.get(file_extension.lower(), 'application/octet-stream')
    
    def get_cdn_url(self, file_key: str) -> str:
        """Get CDN URL for an uploaded file.

        Uses custom CDN domain: cdn.vibeaura.app
        """
        return f"https://cdn.vibeaura.app/{file_key}"

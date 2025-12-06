"""
Google Cloud Storage Document Upload Utility

Handles secure document upload and storage for brand analysis.
Provides URL-based access to stored documents for processing.
"""

import os
import logging
import tempfile
import uuid
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Google Cloud Storage imports
try:
    from google.cloud import storage
    from google.cloud.storage import Blob
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class DocumentStorage:
    """
    Manages document storage in Google Cloud Storage for brand analysis.
    
    Handles:
    - Secure document upload with auto-generated names
    - Temporary signed URL generation for processing
    - Document metadata tracking
    - Automatic cleanup of expired documents
    """
    
    def __init__(self):
        """Initialize DocumentStorage with GCS client."""
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage required for document storage")
        
        self.logger = logging.getLogger(__name__)
        
        # GCS configuration
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "sylvan-replica-478802-p4")
        self.bucket_name = os.getenv("GCS_DOCUMENTS_BUCKET", "capacityreset-documents")
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        
        # Document settings
        self.max_file_size = int(os.getenv("MAX_DOCUMENT_SIZE", "10485760"))  # 10MB default
        self.allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        self.document_ttl_hours = int(os.getenv("DOCUMENT_TTL_HOURS", "168"))  # 1 week default
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: str,
        content_type: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Upload document to GCS and return access details.
        
        Args:
            file_content: Binary content of the document
            filename: Original filename
            user_id: ID of user uploading document
            content_type: MIME type of the document
            
        Returns:
            Tuple of (gcs_url, signed_url, metadata)
        """
        self.logger.info(f"Uploading document for user {user_id}: {filename}")
        
        try:
            # Validate file
            self._validate_document(file_content, filename)
            
            # Generate secure filename
            file_extension = Path(filename).suffix.lower()
            secure_filename = self._generate_secure_filename(user_id, file_extension)
            
            # Create blob path
            blob_path = f"brand-documents/{user_id}/{secure_filename}"
            blob = self.bucket.blob(blob_path)
            
            # Set metadata
            metadata = {
                'user_id': user_id,
                'original_filename': filename,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'expiry_timestamp': (datetime.utcnow() + timedelta(hours=self.document_ttl_hours)).isoformat(),
                'content_type': content_type or self._detect_content_type(filename)
            }
            
            blob.metadata = metadata
            
            # Upload document
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_string(file_content)
            
            # Generate signed URL for access
            signed_url = blob.generate_signed_url(
                expiration=timedelta(hours=self.document_ttl_hours),
                method='GET'
            )
            
            gcs_url = f"gs://{self.bucket_name}/{blob_path}"
            
            self.logger.info(f"Document uploaded successfully: {gcs_url}")
            
            return gcs_url, signed_url, metadata
            
        except Exception as e:
            self.logger.error(f"Document upload failed: {str(e)}")
            raise ValueError(f"Document upload failed: {str(e)}")
    
    async def upload_document_from_file(
        self, 
        file_path: str, 
        user_id: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Upload document from local file path.
        
        Args:
            file_path: Local path to document file
            user_id: ID of user uploading document
            
        Returns:
            Tuple of (gcs_url, signed_url, metadata)
        """
        self.logger.info(f"Uploading file {file_path} for user {user_id}")
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Detect content type
            content_type = self._detect_content_type(file_path_obj.name)
            
            return await self.upload_document(
                file_content, 
                file_path_obj.name, 
                user_id, 
                content_type
            )
            
        except Exception as e:
            self.logger.error(f"File upload failed: {str(e)}")
            raise
    
    async def get_document_url(self, gcs_path: str) -> str:
        """
        Generate new signed URL for existing document.
        
        Args:
            gcs_path: GCS path (gs://bucket/path/file.ext)
            
        Returns:
            Signed URL for document access
        """
        try:
            # Parse GCS path
            if not gcs_path.startswith('gs://'):
                raise ValueError("Invalid GCS path format")
            
            path_parts = gcs_path[5:].split('/', 1)  # Remove gs:// prefix
            bucket_name = path_parts[0]
            blob_path = path_parts[1]
            
            # Get blob
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            if not blob.exists():
                raise FileNotFoundError(f"Document not found: {gcs_path}")
            
            # Generate signed URL
            signed_url = blob.generate_signed_url(
                expiration=timedelta(hours=24),  # 24 hour access for processing
                method='GET'
            )
            
            return signed_url
            
        except Exception as e:
            self.logger.error(f"Error generating document URL: {str(e)}")
            raise
    
    async def get_document_metadata(self, gcs_path: str) -> Dict[str, Any]:
        """
        Retrieve metadata for stored document.
        
        Args:
            gcs_path: GCS path to document
            
        Returns:
            Document metadata dictionary
        """
        try:
            # Parse GCS path
            if not gcs_path.startswith('gs://'):
                raise ValueError("Invalid GCS path format")
            
            path_parts = gcs_path[5:].split('/', 1)
            bucket_name = path_parts[0]
            blob_path = path_parts[1]
            
            # Get blob
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            if not blob.exists():
                raise FileNotFoundError(f"Document not found: {gcs_path}")
            
            # Refresh blob to get latest metadata
            blob.reload()
            
            return {
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'metadata': blob.metadata or {},
                'gcs_path': gcs_path
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving document metadata: {str(e)}")
            raise
    
    async def delete_document(self, gcs_path: str) -> bool:
        """
        Delete document from storage.
        
        Args:
            gcs_path: GCS path to document
            
        Returns:
            True if deleted successfully
        """
        try:
            # Parse GCS path
            if not gcs_path.startswith('gs://'):
                raise ValueError("Invalid GCS path format")
            
            path_parts = gcs_path[5:].split('/', 1)
            bucket_name = path_parts[0]
            blob_path = path_parts[1]
            
            # Delete blob
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                blob.delete()
                self.logger.info(f"Document deleted: {gcs_path}")
                return True
            else:
                self.logger.warning(f"Document not found for deletion: {gcs_path}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error deleting document: {str(e)}")
            raise
    
    async def cleanup_expired_documents(self, user_id: Optional[str] = None) -> int:
        """
        Clean up expired documents to free storage space.
        
        Args:
            user_id: Optional user ID to limit cleanup scope
            
        Returns:
            Number of documents deleted
        """
        self.logger.info(f"Starting document cleanup{' for user ' + user_id if user_id else ''}")
        
        try:
            deleted_count = 0
            current_time = datetime.utcnow()
            
            # List documents to check for expiry
            prefix = f"brand-documents/{user_id}/" if user_id else "brand-documents/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                # Check expiry from metadata
                if blob.metadata and 'expiry_timestamp' in blob.metadata:
                    expiry_time = datetime.fromisoformat(blob.metadata['expiry_timestamp'])
                    
                    if current_time > expiry_time:
                        blob.delete()
                        deleted_count += 1
                        self.logger.debug(f"Deleted expired document: {blob.name}")
            
            self.logger.info(f"Cleanup complete. Deleted {deleted_count} expired documents")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error during document cleanup: {str(e)}")
            raise
    
    def _validate_document(self, file_content: bytes, filename: str) -> None:
        """Validate document before upload."""
        
        # Check file size
        if len(file_content) > self.max_file_size:
            raise ValueError(f"File too large: {len(file_content)} bytes (max: {self.max_file_size})")
        
        if len(file_content) == 0:
            raise ValueError("Empty file not allowed")
        
        # Check file extension
        file_extension = Path(filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _generate_secure_filename(self, user_id: str, file_extension: str) -> str:
        """Generate secure, unique filename for storage."""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{timestamp}_{unique_id}_{user_id[:8]}{file_extension}"
    
    def _detect_content_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        
        extension = Path(filename).suffix.lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.htm': 'text/html'
        }
        
        return content_type_map.get(extension, 'application/octet-stream')
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage configuration and status information."""
        
        return {
            'bucket_name': self.bucket_name,
            'project_id': self.project_id,
            'max_file_size_mb': self.max_file_size / 1024 / 1024,
            'allowed_extensions': list(self.allowed_extensions),
            'document_ttl_hours': self.document_ttl_hours,
            'gcs_available': GCS_AVAILABLE
        }
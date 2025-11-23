"""
Embeddings Generator Module

Generates vector embeddings for job descriptions using Vertex AI
with intelligent chunking strategies.
"""

import uuid
import json
from typing import List, Dict, Any
from datetime import datetime
from google.cloud import bigquery
from vertexai.language_models import TextEmbeddingModel
import vertexai

# Initialize Vertex AI
vertexai.init(project="sylvan-replica-478802-p4", location="us-central1")


class EmbeddingsGenerator:
    """Generate vector embeddings for semantic search."""
    
    def __init__(self):
        self.model_name = "text-embedding-004"
        self.version = f"v1.0-{self.model_name}"
        self.embedding_dimension = 768
        self.max_tokens_per_chunk = 2000  # Conservative limit
        self.model = TextEmbeddingModel.from_pretrained(self.model_name)
        self.bigquery_client = bigquery.Client()
        self.project_id = "sylvan-replica-478802-p4"
        self.dataset_id = f"{self.project_id}.brightdata_jobs"
    
    def get_version(self) -> str:
        """Return generator version identifier."""
        return self.version
    
    def get_model_name(self) -> str:
        """Return embedding model name."""
        return self.model_name
    
    def generate_embeddings(
        self,
        job_posting_id: str,
        job_description: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for job description with intelligent chunking.
        
        Args:
            job_posting_id: Job reference
            job_description: Full job description text
            metadata: Job context (title, company, location)
            
        Returns:
            List of embedding dictionaries with chunk info and vectors
        """
        if not job_description:
            return []
        
        # Chunk the description intelligently
        chunks = self._chunk_description(job_description)
        
        embeddings = []
        for idx, chunk in enumerate(chunks):
            try:
                # Generate embedding via Vertex AI
                embedding_response = self.model.get_embeddings([chunk['content']])
                embedding_vector = embedding_response[0].values
                
                embeddings.append({
                    'chunk_id': idx,
                    'chunk_type': chunk['type'],
                    'content': chunk['content'],
                    'content_tokens': self._estimate_tokens(chunk['content']),
                    'embedding': embedding_vector,
                    'metadata': metadata
                })
            except Exception as e:
                # Log but continue with other chunks
                print(f"Failed to generate embedding for chunk {idx}: {str(e)}")
                continue
        
        return embeddings
    
    def _chunk_description(self, description: str) -> List[Dict[str, str]]:
        """
        Chunk description intelligently by sections.
        
        Strategies:
        1. Try to detect sections (Responsibilities, Requirements, etc.)
        2. Fall back to fixed-size chunks with overlap if no sections found
        
        Args:
            description: Full job description
            
        Returns:
            List of chunks with type and content
        """
        chunks = []
        
        # Common section headers
        section_keywords = [
            'responsibilities', 'requirements', 'qualifications', 'benefits',
            'about us', 'about the role', 'what you\'ll do', 'what we\'re looking for',
            'nice to have', 'preferred qualifications', 'compensation', 'perks'
        ]
        
        # Try to find sections
        description_lower = description.lower()
        sections = []
        
        for keyword in section_keywords:
            if keyword in description_lower:
                start_pos = description_lower.find(keyword)
                sections.append((start_pos, keyword))
        
        # Sort by position
        sections.sort()
        
        if sections:
            # Extract content by sections
            for i, (start_pos, keyword) in enumerate(sections):
                # Find end position (next section or end of description)
                if i + 1 < len(sections):
                    end_pos = sections[i + 1][0]
                else:
                    end_pos = len(description)
                
                # Extract section content
                section_content = description[start_pos:end_pos].strip()
                
                # Skip if too small
                if len(section_content) < 50:
                    continue
                
                # Split if too large
                if self._estimate_tokens(section_content) > self.max_tokens_per_chunk:
                    # Split into multiple chunks
                    sub_chunks = self._split_large_section(section_content)
                    for sub_idx, sub_content in enumerate(sub_chunks):
                        chunks.append({
                            'type': f'{keyword.replace(" ", "_")}_part_{sub_idx + 1}',
                            'content': sub_content
                        })
                else:
                    chunks.append({
                        'type': keyword.replace(' ', '_'),
                        'content': section_content
                    })
        else:
            # No sections found, use fixed-size chunking with overlap
            chunk_size = 1500  # Conservative token estimate
            overlap = 200
            
            words = description.split()
            current_chunk = []
            
            for word in words:
                current_chunk.append(word)
                
                # Estimate tokens (rough: 1 token ~= 0.75 words)
                estimated_tokens = len(current_chunk) * 0.75
                
                if estimated_tokens >= chunk_size:
                    chunk_content = ' '.join(current_chunk)
                    chunks.append({
                        'type': f'chunk_{len(chunks) + 1}',
                        'content': chunk_content
                    })
                    
                    # Keep overlap for next chunk
                    overlap_words = int(overlap / 0.75)
                    current_chunk = current_chunk[-overlap_words:]
            
            # Add remaining content
            if current_chunk:
                chunk_content = ' '.join(current_chunk)
                if len(chunk_content) > 50:  # Skip tiny chunks
                    chunks.append({
                        'type': f'chunk_{len(chunks) + 1}',
                        'content': chunk_content
                    })
        
        # Always include full description as one chunk if small enough
        if self._estimate_tokens(description) <= self.max_tokens_per_chunk:
            chunks.insert(0, {
                'type': 'full_description',
                'content': description
            })
        
        return chunks
    
    def _split_large_section(self, content: str, max_tokens: int = 2000) -> List[str]:
        """Split a large section into smaller chunks."""
        chunks = []
        sentences = content.split('. ')
        current_chunk = []
        
        for sentence in sentences:
            current_chunk.append(sentence)
            
            # Estimate tokens
            chunk_text = '. '.join(current_chunk)
            if self._estimate_tokens(chunk_text) >= max_tokens:
                chunks.append(chunk_text)
                current_chunk = []
        
        # Add remaining
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ~= 4 characters)."""
        return len(text) // 4
    
    def store_embeddings(
        self,
        job_posting_id: str,
        enrichment_id: str,
        embeddings: List[Dict[str, Any]]
    ):
        """
        Store embeddings in BigQuery.
        
        Args:
            job_posting_id: Job reference
            enrichment_id: Enrichment tracking reference
            embeddings: List of embedding records
        """
        if not embeddings:
            return
        
        rows = []
        for embedding in embeddings:
            rows.append({
                'embedding_id': str(uuid.uuid4()),
                'job_posting_id': job_posting_id,
                'enrichment_id': enrichment_id,
                'chunk_id': embedding['chunk_id'],
                'chunk_type': embedding['chunk_type'],
                'content': embedding['content'],
                'content_tokens': embedding['content_tokens'],
                'embedding': embedding['embedding'],
                'model_version': self.model_name,
                'metadata': json.dumps(embedding['metadata']),
                'created_at': datetime.utcnow().isoformat()
            })
        
        table_id = f"{self.dataset_id}.job_embeddings"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store embeddings: {errors}")

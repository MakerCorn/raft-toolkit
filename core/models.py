"""
Data models and types for the RAFT application.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from datetime import datetime
import uuid

# Enum types
class DocType(Enum):
    PDF = "pdf"
    TXT = "txt"
    JSON = "json"
    API = "api"
    PPTX = "pptx"

class OutputFormat(Enum):
    HF = "hf"
    COMPLETION = "completion"
    CHAT = "chat"
    EVAL = "eval"

class OutputType(Enum):
    JSONL = "jsonl"
    PARQUET = "parquet"

class ChunkingStrategy(Enum):
    SEMANTIC = "semantic"
    FIXED = "fixed"
    SENTENCE = "sentence"

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    id: str
    content: str
    source: str
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, content: str, source: str, metadata: Optional[Dict[str, Any]] = None, 
              chunk_id: Optional[str] = None) -> 'DocumentChunk':
        """Create a new document chunk with generated ID."""
        return cls(
            id=chunk_id or str(uuid.uuid4()),
            content=content,
            source=source,
            metadata=metadata or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunk':
        """Create from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            metadata=data["metadata"],
            created_at=created_at
        )

@dataclass
class Question:
    """Represents a generated question."""
    id: str
    text: str
    chunk_id: str
    
    @classmethod
    def create(cls, text: str, chunk_id: str) -> 'Question':
        """Create a new question with generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            text=text,
            chunk_id=chunk_id
        )

@dataclass
class QADataPoint:
    """Represents a question-answer data point with context."""
    id: str
    type: str
    question: str
    context: str  # Changed from Dict to str for simplicity
    oracle_context: str
    cot_answer: str
    instruction: str
    
    @classmethod
    def create(cls, question: str, oracle_context: str, distractor_contexts: List[str], 
               cot_answer: str, doctype: str) -> 'QADataPoint':
        """Create a new QA data point."""
        # Combine oracle and distractor contexts into single string
        context = oracle_context
        if distractor_contexts:
            context += "\n\n" + "\n\n".join(distractor_contexts)
        
        # Build instruction format
        instruction = ""
        docs = [oracle_context] + distractor_contexts
        for doc in docs:
            instruction += f"<DOCUMENT>{doc}</DOCUMENT>\n"
        instruction += question
        
        return cls(
            id=str(uuid.uuid4()),
            type="api call" if doctype == "api" else "cot",
            question=question,
            context=context,
            oracle_context=oracle_context,
            cot_answer=cot_answer,
            instruction=instruction
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "question": self.question,
            "context": self.context,
            "oracle_context": self.oracle_context,
            "cot_answer": self.cot_answer,
            "instruction": self.instruction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QADataPoint':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            question=data["question"],
            context=data["context"],
            oracle_context=data["oracle_context"],
            cot_answer=data["cot_answer"],
            instruction=data["instruction"]
        )

@dataclass
class ProcessingJob:
    """Represents a processing job for document chunks."""
    id: str
    chunk: DocumentChunk
    num_questions: int
    num_distractors: int
    include_oracle_probability: float
    status: str = "pending"  # pending, processing, completed, failed
    
    @classmethod
    def create(cls, chunk: DocumentChunk, num_questions: int, 
               num_distractors: int, include_oracle_probability: float) -> 'ProcessingJob':
        """Create a new processing job."""
        return cls(
            id=str(uuid.uuid4()),
            chunk=chunk,
            num_questions=num_questions,
            num_distractors=num_distractors,
            include_oracle_probability=include_oracle_probability
        )

@dataclass
class ProcessingResult:
    """Results from processing a job."""
    job_id: str
    success: bool
    qa_data_points: List[QADataPoint] = field(default_factory=list)
    processing_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "success": self.success,
            "qa_data_points": [qa.to_dict() for qa in self.qa_data_points],
            "processing_time": self.processing_time,
            "token_usage": self.token_usage,
            "error": self.error
        }
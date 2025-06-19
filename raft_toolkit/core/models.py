"""
Data models and types for the RAFT application.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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
    embedding: Optional[List[float]] = None

    @classmethod
    def create(
        cls,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> "DocumentChunk":
        """Create a new document chunk with generated ID."""
        return cls(
            id=chunk_id or str(uuid.uuid4()),
            content=content,
            source=source,
            metadata=metadata or {},
            embedding=embedding,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            metadata=data["metadata"],
            created_at=created_at,
            embedding=data.get("embedding"),
        )


@dataclass
class Question:
    """Represents a generated question."""

    id: str
    text: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, text: str, chunk_id: str, metadata: Optional[Dict[str, Any]] = None) -> "Question":
        """Create a new question with generated ID."""
        return cls(id=str(uuid.uuid4()), text=text, chunk_id=chunk_id, metadata=metadata or {})


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
    doctype: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        question: str,
        oracle_context: str,
        distractor_contexts: List[str],
        cot_answer: str,
        doctype: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "QADataPoint":
        """Create a new QA data point."""
        # Combine oracle and distractor contexts into single string
        context_parts = [oracle_context]
        if distractor_contexts:
            context_parts.extend(distractor_contexts)
        context = "\n\n".join(context_parts)

        # Build instruction format with documents
        instruction_parts = []
        docs = [oracle_context] + distractor_contexts
        for doc in docs:
            instruction_parts.append(f"<DOCUMENT>{doc}</DOCUMENT>")
        instruction_parts.append(question)
        instruction = "\n".join(instruction_parts)

        return cls(
            id=str(uuid.uuid4()),
            type="api call" if doctype == "api" else "cot",
            question=question,
            context=context,
            oracle_context=oracle_context,
            cot_answer=cot_answer,
            instruction=instruction,
            doctype=doctype,
            metadata=metadata or {},
        )

    def get_all_contexts(self) -> List[str]:
        """Get all contexts (oracle + distractors) as a list."""
        return self.context.split("\n\n")

    @property
    def distractor_contexts(self) -> List[str]:
        """Get distractor contexts (all except oracle)."""
        all_contexts = self.get_all_contexts()
        return [ctx for ctx in all_contexts if ctx != self.oracle_context]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "question": self.question,
            "context": self.context,
            "oracle_context": self.oracle_context,
            "cot_answer": self.cot_answer,
            "instruction": self.instruction,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QADataPoint":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            question=data["question"],
            context=data["context"],
            oracle_context=data["oracle_context"],
            cot_answer=data["cot_answer"],
            instruction=data["instruction"],
            doctype=data.get("doctype", "unknown"),
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
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        chunk: DocumentChunk,
        num_questions: int,
        num_distractors: int,
        include_oracle_probability: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ProcessingJob":
        """Create a new processing job."""
        return cls(
            id=str(uuid.uuid4()),
            chunk=chunk,
            num_questions=num_questions,
            num_distractors=num_distractors,
            include_oracle_probability=include_oracle_probability,
            metadata=metadata or {},
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
            "error": self.error,
        }


@dataclass
class ProcessingStatistics:
    """Statistics from processing operations."""

    total_chunks: int = 0
    total_qa_pairs: int = 0
    processing_time: float = 0.0
    total_tokens: int = 0
    successful_chunks: int = 0
    failed_chunks: int = 0

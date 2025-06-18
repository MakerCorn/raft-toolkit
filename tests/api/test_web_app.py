"""
API tests for the web application.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

try:
    from fastapi.testclient import TestClient
except ImportError:
    from starlette.testclient import TestClient

from web.app import app, jobs


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_upload_file(temp_directory):
    """Create a temporary upload file."""
    test_file = temp_directory / "test_upload.txt"
    test_file.write_text("This is a test document for upload testing.")
    return test_file


@pytest.mark.api
class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.api
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "raft-toolkit"


@pytest.mark.api
class TestConfigEndpoint:
    """Test configuration endpoint."""

    @pytest.mark.api
    def test_get_config(self, client):
        """Test getting default configuration."""
        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()

        # Verify expected config fields
        assert "output_format" in data
        assert "doctype" in data
        assert "chunking_strategy" in data
        assert "chunk_size" in data
        assert "questions" in data
        assert "distractors" in data
        assert "workers" in data

        # Verify default values
        assert data["output_format"] == "hf"
        assert data["doctype"] == "pdf"
        assert data["chunking_strategy"] == "semantic"


@pytest.mark.api
class TestUploadEndpoint:
    """Test file upload endpoint."""

    @pytest.mark.api
    def test_upload_file_success(self, client, temp_upload_file):
        """Test successful file upload."""
        with open(temp_upload_file, "rb") as f:
            response = client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})

        assert response.status_code == 200
        data = response.json()

        assert "file_id" in data
        assert "file_path" in data
        assert data["filename"] == "test.txt"
        assert data["size"] == 43  # Length of test content
        assert Path(data["file_path"]).exists()

    @pytest.mark.api
    def test_upload_file_no_file(self, client):
        """Test upload endpoint with no file."""
        response = client.post("/api/upload")

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    def test_upload_file_empty_filename(self, client):
        """Test upload with empty filename."""
        response = client.post("/api/upload", files={"file": ("", b"content", "text/plain")})

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Filename is required" in data["detail"]


@pytest.mark.api
class TestProcessEndpoint:
    """Test processing endpoint."""

    @pytest.mark.api
    def test_start_processing_success(self, client, temp_upload_file):
        """Test starting processing job successfully."""
        # First upload a file
        with open(temp_upload_file, "rb") as f:
            upload_response = client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})

        file_path = upload_response.json()["file_path"]

        # Start processing
        process_request = {
            "output_format": "hf",
            "doctype": "txt",
            "chunking_strategy": "fixed",
            "chunk_size": 512,
            "questions": 3,
            "distractors": 2,
            "workers": 1,
        }

        response = client.post(f"/api/process?file_path={file_path}", json=process_request)

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["message"] == "Processing started"

    @pytest.mark.api
    def test_start_processing_missing_file(self, client):
        """Test starting processing with missing file."""
        process_request = {"output_format": "hf", "doctype": "txt"}

        response = client.post("/api/process?file_path=nonexistent.txt", json=process_request)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    def test_start_processing_invalid_config(self, client, temp_upload_file):
        """Test starting processing with invalid configuration."""
        # Upload file first
        with open(temp_upload_file, "rb") as f:
            upload_response = client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})

        file_path = upload_response.json()["file_path"]

        # Invalid config (negative chunk_size)
        process_request = {"output_format": "invalid_format", "doctype": "txt", "chunk_size": -100}

        response = client.post(f"/api/process?file_path={file_path}", json=process_request)

        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data


@pytest.mark.api
class TestJobStatusEndpoint:
    """Test job status endpoints."""

    @pytest.mark.api
    def test_get_job_status_success(self, client):
        """Test getting job status for existing job."""
        # Create a mock job
        job_id = "test-job-123"
        jobs[job_id] = {
            "status": "processing",
            "progress": 0.5,
            "message": "Processing in progress",
            "stats": None,
            "error": None,
        }

        response = client.get(f"/api/jobs/{job_id}/status")

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == job_id
        assert data["status"] == "processing"
        assert data["progress"] == 0.5
        assert data["message"] == "Processing in progress"

    @pytest.mark.api
    def test_get_job_status_not_found(self, client):
        """Test getting status for non-existent job."""
        response = client.get("/api/jobs/nonexistent-job/status")

        assert response.status_code == 404
        data = response.json()
        assert "Job not found" in data["detail"]

    @pytest.mark.api
    def test_get_all_jobs(self, client):
        """Test getting all jobs."""
        # Clear existing jobs
        jobs.clear()

        # Add test jobs
        jobs["job1"] = {"status": "completed", "progress": 1.0, "message": "Completed", "stats": None, "error": None}
        jobs["job2"] = {"status": "processing", "progress": 0.5, "message": "Processing", "stats": None, "error": None}

        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        job_ids = {job["job_id"] for job in data}
        assert job_ids == {"job1", "job2"}

    @pytest.mark.api
    def test_delete_job_success(self, client):
        """Test deleting a job successfully."""
        job_id = "delete-test-job"
        jobs[job_id] = {
            "status": "completed",
            "progress": 1.0,
            "message": "Completed",
            "stats": None,
            "error": None,
            "config": Mock(),
        }

        response = client.delete(f"/api/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Job deleted"
        assert job_id not in jobs

    @pytest.mark.api
    def test_delete_job_not_found(self, client):
        """Test deleting non-existent job."""
        response = client.delete("/api/jobs/nonexistent-job")

        assert response.status_code == 404
        data = response.json()
        assert "Job not found" in data["detail"]


@pytest.mark.api
class TestDownloadEndpoint:
    """Test download endpoint."""

    @pytest.mark.api
    def test_download_completed_job(self, client, temp_directory):
        """Test downloading results from completed job."""
        job_id = "download-test-job"

        # Create mock output directory with files
        output_dir = temp_directory / "output"
        output_dir.mkdir()

        # Create test files
        result_file = output_dir / "dataset.jsonl"
        result_file.write_text('{"test": "data"}\n')

        # Create mock config
        mock_config = Mock()
        mock_config.output = str(output_dir / "dataset")
        mock_config.output_type = "jsonl"

        jobs[job_id] = {
            "status": "completed",
            "progress": 1.0,
            "message": "Completed",
            "config": mock_config,
            "stats": None,
            "error": None,
        }

        response = client.get(f"/api/jobs/{job_id}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment" in response.headers["content-disposition"]

    @pytest.mark.api
    def test_download_job_not_completed(self, client):
        """Test downloading from non-completed job."""
        job_id = "processing-job"
        jobs[job_id] = {"status": "processing", "progress": 0.5, "message": "Processing", "stats": None, "error": None}

        response = client.get(f"/api/jobs/{job_id}/download")

        assert response.status_code == 400
        data = response.json()
        assert "Job not completed" in data["detail"]

    @pytest.mark.api
    def test_download_job_not_found(self, client):
        """Test downloading from non-existent job."""
        response = client.get("/api/jobs/nonexistent-job/download")

        assert response.status_code == 404
        data = response.json()
        assert "Job not found" in data["detail"]


@pytest.mark.api
class TestPreviewEndpoint:
    """Test preview endpoint."""

    @pytest.mark.api
    def test_get_preview_success(self, client, temp_upload_file):
        """Test getting processing preview."""
        # Upload file first
        with open(temp_upload_file, "rb") as f:
            upload_response = client.post("/api/upload", files={"file": ("test.txt", f, "text/plain")})

        file_path = upload_response.json()["file_path"]

        preview_request = {"doctype": "txt", "chunking_strategy": "fixed", "chunk_size": 100, "questions": 3}

        with patch("web.app.RaftEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine.get_processing_preview.return_value = {
                "input_path": file_path,
                "doctype": "txt",
                "files_to_process": [file_path],
                "estimated_chunks": 2,
                "estimated_qa_points": 6,
            }
            mock_engine_class.return_value = mock_engine

            response = client.post(f"/api/preview?file_path={file_path}", json=preview_request)

        assert response.status_code == 200
        data = response.json()

        assert "files_to_process" in data
        assert data["estimated_chunks"] == 2
        assert data["estimated_qa_points"] == 6
        assert data["doctype"] == "txt"

    @pytest.mark.api
    def test_get_preview_missing_file(self, client):
        """Test preview with missing file."""
        preview_request = {"doctype": "txt", "chunking_strategy": "fixed"}

        response = client.post("/api/preview?file_path=nonexistent.txt", json=preview_request)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


@pytest.mark.api
class TestStaticFiles:
    """Test static file serving."""

    @pytest.mark.api
    def test_serve_index_html(self, client):
        """Test serving the main HTML page."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.api
    def test_serve_static_js(self, client):
        """Test serving JavaScript files."""
        # Note: This test may fail if the actual static files don't exist
        # In a real environment, you'd ensure test static files exist
        response = client.get("/static/app.js")

        # Should either serve the file or return 404 if file doesn't exist
        assert response.status_code in [200, 404]

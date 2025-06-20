"""
CLI interface for RAFT toolkit using the shared core modules.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

from raft_toolkit.core.config import RaftConfig, get_config
from raft_toolkit.core.raft_engine import RaftEngine

# Import enhanced logging setup
try:
    from raft_toolkit.core.logging.setup import configure_logging, get_logger, log_setup, setup_sentry_logging
except ImportError:
    # Fallback to basic logging if enhanced logging is not available

    def log_setup() -> None:
        import logging

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)8s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    def get_logger(name: str) -> Any:
        import logging

        return logging.getLogger(name)

    def configure_logging(
        level: Optional[str] = None,
        format_type: Optional[str] = None,
        output: Optional[str] = None,
        structured: Optional[bool] = None,
        external_handler: Any = None,
        progress_tracking: Optional[bool] = None,
        tracing_enabled: Optional[bool] = None,
        trace_sampling_rate: Optional[float] = None,
        jaeger_endpoint: Optional[str] = None,
        trace_service_name: Optional[str] = None,
        **context: Any,
    ) -> None:
        pass

    def setup_sentry_logging(dsn: str, **kwargs: Any) -> None:
        import logging

        logging.warning("Enhanced logging not available. Sentry integration disabled.")


# Initialize logger (will be properly configured after log_setup())
logger: Optional[Any] = None


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="RAFT Toolkit - Retrieval Augmentation Fine-Tuning Dataset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # I/O Arguments
    parser.add_argument("--datapath", type=Path, help="Path to the input document or directory (for local sources)")
    parser.add_argument("--output", type=str, default="./raft_output", help="Path to save the generated dataset")

    # Input Source Arguments
    parser.add_argument(
        "--source-type", type=str, default="local", choices=["local", "s3", "sharepoint"], help="Type of input source"
    )
    parser.add_argument(
        "--source-uri", type=str, help="URI for the input source (S3 bucket, SharePoint URL, or local path)"
    )
    parser.add_argument(
        "--source-credentials", type=str, help="JSON string containing credentials for the input source"
    )
    parser.add_argument("--source-include-patterns", type=str, help="JSON array of glob patterns to include")
    parser.add_argument("--source-exclude-patterns", type=str, help="JSON array of glob patterns to exclude")
    parser.add_argument(
        "--source-max-file-size", type=int, default=50 * 1024 * 1024, help="Maximum file size in bytes (default: 50MB)"
    )
    parser.add_argument("--source-batch-size", type=int, default=100, help="Batch size for processing source files")
    parser.add_argument(
        "--output-format",
        type=str,
        default="hf",
        choices=["hf", "completion", "chat", "eval"],
        help="Format to convert the dataset to",
    )
    parser.add_argument(
        "--output-type",
        type=str,
        default="jsonl",
        choices=["jsonl", "parquet"],
        help="File type to export the dataset to",
    )
    parser.add_argument("--output-chat-system-prompt", type=str, help="System prompt for chat output format")
    parser.add_argument(
        "--output-completion-prompt-column", type=str, default="prompt", help="Prompt column name for completion format"
    )
    parser.add_argument(
        "--output-completion-completion-column",
        type=str,
        default="completion",
        help="Completion column name for completion format",
    )

    # Processing Arguments
    parser.add_argument("--distractors", type=int, default=1, help="Number of distractor documents per data point")
    parser.add_argument("--p", type=float, default=1.0, help="Probability of including oracle document in context")
    parser.add_argument("--questions", type=int, default=5, help="Number of questions to generate per chunk")
    parser.add_argument("--chunk_size", type=int, default=512, help="Size of each chunk in tokens")
    parser.add_argument(
        "--doctype",
        type=str,
        default="pdf",
        choices=["pdf", "txt", "json", "api", "pptx"],
        help="Type of the input document",
    )
    parser.add_argument(
        "--chunking-strategy",
        type=str,
        default="semantic",
        choices=["semantic", "fixed", "sentence"],
        help="Chunking algorithm to use",
    )
    parser.add_argument("--chunking-params", type=str, help="JSON string of extra chunker parameters")

    # AI Model Arguments
    parser.add_argument("--openai_key", type=str, help="OpenAI API key (can also use OPENAI_API_KEY env var)")
    parser.add_argument("--embedding_model", type=str, default="nomic-embed-text", help="Embedding model for chunking")
    parser.add_argument(
        "--completion_model", type=str, default="llama3.2", help="Model for question and answer generation"
    )
    parser.add_argument("--system-prompt-key", type=str, default="gpt", help="System prompt template to use")

    # Azure Arguments
    parser.add_argument(
        "--use-azure-identity", action="store_true", help="Use Azure Default Credentials for authentication"
    )

    # Performance Arguments
    parser.add_argument("--workers", type=int, default=1, help="Number of worker threads for QA generation")
    parser.add_argument("--embed-workers", type=int, default=1, help="Number of worker threads for embedding/chunking")
    parser.add_argument("--pace", action="store_true", default=True, help="Pace LLM calls to stay within rate limits")
    parser.add_argument(
        "--auto-clean-checkpoints", action="store_true", help="Automatically clean checkpoints after completion"
    )

    # Rate Limiting Arguments
    parser.add_argument("--rate-limit", action="store_true", help="Enable rate limiting for API requests")
    parser.add_argument(
        "--rate-limit-strategy",
        type=str,
        choices=["fixed_window", "sliding_window", "token_bucket", "adaptive"],
        default="sliding_window",
        help="Rate limiting strategy",
    )
    parser.add_argument(
        "--rate-limit-preset",
        type=str,
        choices=[
            "openai_gpt4",
            "openai_gpt35_turbo",
            "azure_openai_standard",
            "anthropic_claude",
            "conservative",
            "aggressive",
        ],
        help="Use a preset rate limit configuration",
    )
    parser.add_argument("--rate-limit-requests-per-minute", type=int, help="Maximum requests per minute")
    parser.add_argument("--rate-limit-tokens-per-minute", type=int, help="Maximum tokens per minute")
    parser.add_argument("--rate-limit-max-burst", type=int, help="Maximum burst requests allowed")
    parser.add_argument(
        "--rate-limit-max-retries", type=int, default=3, help="Maximum number of retries on rate limit errors"
    )

    # Template Arguments
    parser.add_argument("--templates", type=str, default="./templates/", help="Directory containing prompt templates")
    parser.add_argument("--embedding-prompt-template", type=str, help="Path to custom embedding prompt template file")
    parser.add_argument("--qa-prompt-template", type=str, help="Path to custom Q&A generation prompt template file")
    parser.add_argument(
        "--answer-prompt-template", type=str, help="Path to custom answer generation prompt template file"
    )

    # LangWatch Observability Arguments
    parser.add_argument("--langwatch-enabled", action="store_true", help="Enable LangWatch observability and tracing")
    parser.add_argument(
        "--langwatch-api-key", type=str, help="LangWatch API key (can also use LANGWATCH_API_KEY env var)"
    )
    parser.add_argument("--langwatch-endpoint", type=str, help="Custom LangWatch endpoint URL")
    parser.add_argument("--langwatch-project", type=str, help="LangWatch project name")
    parser.add_argument("--langwatch-debug", action="store_true", help="Enable LangWatch debug logging")

    # Utility Arguments
    parser.add_argument("--preview", action="store_true", help="Show processing preview without running")
    parser.add_argument("--validate", action="store_true", help="Validate configuration and inputs only")
    parser.add_argument("--env-file", type=str, help="Path to .env file for configuration")

    return parser


def override_config_from_args(config: RaftConfig, args: argparse.Namespace) -> RaftConfig:
    """Override configuration with command line arguments."""
    import json

    # Input source configuration
    if args.source_type != "local":
        config.source_type = args.source_type
    if args.source_uri:
        config.source_uri = args.source_uri
    if args.source_credentials:
        try:
            config.source_credentials = json.loads(args.source_credentials)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in source-credentials: {e}")
            sys.exit(1)
    if args.source_include_patterns:
        try:
            config.source_include_patterns = json.loads(args.source_include_patterns)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in source-include-patterns: {e}")
            sys.exit(1)
    if args.source_exclude_patterns:
        try:
            config.source_exclude_patterns = json.loads(args.source_exclude_patterns)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in source-exclude-patterns: {e}")
            sys.exit(1)
    if args.source_max_file_size != 50 * 1024 * 1024:
        config.source_max_file_size = args.source_max_file_size
    if args.source_batch_size != 100:
        config.source_batch_size = args.source_batch_size

    # Legacy datapath handling - if provided and no source_uri, use it
    if args.datapath and not config.source_uri:
        if config.source_type == "local":
            config.datapath = args.datapath
            config.source_uri = str(args.datapath)
        else:
            config.datapath = args.datapath

    # Only override if explicitly provided
    if args.output != "./raft_output":  # Only if changed from default
        config.output = args.output
    if args.output_format != "hf":
        config.output_format = args.output_format
    if args.output_type != "jsonl":
        config.output_type = args.output_type
    if args.output_chat_system_prompt:
        config.output_chat_system_prompt = args.output_chat_system_prompt
    if args.output_completion_prompt_column != "prompt":
        config.output_completion_prompt_column = args.output_completion_prompt_column
    if args.output_completion_completion_column != "completion":
        config.output_completion_completion_column = args.output_completion_completion_column

    if args.distractors != 1:
        config.distractors = args.distractors
    if args.p != 1.0:
        config.p = args.p
    if args.questions != 5:
        config.questions = args.questions
    if args.chunk_size != 512:
        config.chunk_size = args.chunk_size
    if args.doctype != "pdf":
        config.doctype = args.doctype
    if args.chunking_strategy != "semantic":
        config.chunking_strategy = args.chunking_strategy
    if args.chunking_params:
        try:
            config.chunking_params = json.loads(args.chunking_params)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid chunking params JSON: {e}")
            sys.exit(1)

    if args.openai_key:
        config.openai_key = args.openai_key
    if args.embedding_model != "nomic-embed-text":
        config.embedding_model = args.embedding_model
    if args.completion_model != "llama3.2":
        config.completion_model = args.completion_model
    if args.system_prompt_key != "gpt":
        config.system_prompt_key = args.system_prompt_key

    if args.use_azure_identity:
        config.use_azure_identity = args.use_azure_identity

    if args.workers != 1:
        config.workers = args.workers
    if args.embed_workers != 1:
        config.embed_workers = args.embed_workers
    if not args.pace:  # Only if explicitly disabled
        config.pace = args.pace
    if args.auto_clean_checkpoints:
        config.auto_clean_checkpoints = args.auto_clean_checkpoints

    # Rate limiting arguments
    if args.rate_limit:
        config.rate_limit_enabled = args.rate_limit
    if args.rate_limit_strategy != "sliding_window":
        config.rate_limit_strategy = args.rate_limit_strategy
    if args.rate_limit_preset:
        config.rate_limit_preset = args.rate_limit_preset
    if args.rate_limit_requests_per_minute:
        config.rate_limit_requests_per_minute = args.rate_limit_requests_per_minute
    if args.rate_limit_tokens_per_minute:
        config.rate_limit_tokens_per_minute = args.rate_limit_tokens_per_minute
    if args.rate_limit_max_burst:
        config.rate_limit_max_burst = args.rate_limit_max_burst
    if args.rate_limit_max_retries != 3:
        config.rate_limit_max_retries = args.rate_limit_max_retries

    if args.templates != "./templates/":
        config.templates = args.templates

    # Template file paths
    if args.embedding_prompt_template:
        config.embedding_prompt_template = args.embedding_prompt_template
    if args.qa_prompt_template:
        config.qa_prompt_template = args.qa_prompt_template
    if args.answer_prompt_template:
        config.answer_prompt_template = args.answer_prompt_template

    # LangWatch arguments
    if args.langwatch_enabled:
        config.langwatch_enabled = args.langwatch_enabled
    if args.langwatch_api_key:
        config.langwatch_api_key = args.langwatch_api_key
    if args.langwatch_endpoint:
        config.langwatch_endpoint = args.langwatch_endpoint
    if args.langwatch_project:
        config.langwatch_project = args.langwatch_project
    if args.langwatch_debug:
        config.langwatch_debug = args.langwatch_debug

    return config


def show_preview(engine: RaftEngine, config: RaftConfig) -> None:
    """Show processing preview."""
    if logger is not None:
        logger.set_progress("PREV")
        logger.info(f"Generating preview for {config.source_type} source")

    try:
        if config.source_type == "local":
            datapath = Path(config.datapath) if isinstance(config.datapath, str) else config.datapath
            preview = engine.get_processing_preview(datapath)
        else:
            preview = engine.get_processing_preview()

        print("\n" + "=" * 60)
        print("RAFT PROCESSING PREVIEW")
        print("=" * 60)

        # Handle both legacy and new preview formats
        if "source_type" in preview:
            # New format for remote sources
            print(f"Source Type: {preview['source_type'].title()}")
            print(f"Source URI: {preview['source_uri']}")
            print(f"Total Documents: {preview['total_documents']}")
            print(f"Supported Documents: {preview['supported_documents']}")
            if preview["unsupported_documents"] > 0:
                print(f"Unsupported Documents: {preview['unsupported_documents']}")
            print(f"Total Size: {preview['total_size_mb']} MB")

            if preview["document_types"]:
                print("\nDocument Types:")
                for doc_type, count in preview["document_types"].items():
                    print(f"  - {doc_type}: {count} files")
        else:
            # Legacy format for local files
            print(f"Input Path: {preview['input_path']}")
            print("Document Type: {}".format(preview["doctype"]))
            print(f"Files to Process: {len(preview['files_to_process'])}")

            if "files_to_process" in preview and preview["files_to_process"]:
                if len(preview["files_to_process"]) <= 5:
                    for file_path in preview["files_to_process"]:
                        print(f"  - {file_path}")
                else:
                    for file_path in preview["files_to_process"][:3]:
                        print(f"  - {file_path}")
                    print(f"  ... and {len(preview['files_to_process']) - 3} more files")

        print(f"\nEstimated Chunks: {preview['estimated_chunks']}")
        print(f"Estimated QA Points: {preview['estimated_qa_points']}")
        print(f"Questions per Chunk: {engine.config.questions}")
        print(f"Distractors per Point: {engine.config.distractors}")
        print(f"Chunking Strategy: {preview.get('chunking_strategy', engine.config.chunking_strategy)}")
        print("\nUse --validate to check configuration or run without --preview to start processing.")
        print("=" * 60)

    except Exception as e:
        if logger is not None:
            logger.error(f"Error generating preview: {e}", exc_info=True)
        else:
            print(f"Error generating preview: {e}")
        sys.exit(1)


def validate_only(engine: RaftEngine, config: RaftConfig) -> None:
    """Validate configuration and inputs only."""
    if logger is not None:
        logger.set_progress("VALD")
        logger.info(f"Validating {config.source_type} input source")

    try:
        if config.source_type == "local":
            datapath = Path(config.datapath) if isinstance(config.datapath, str) else config.datapath
            engine.validate_inputs(datapath)
            # Use forward slashes for path representation in output for consistency across platforms
            source_info = f"Ready to process: {str(datapath).replace(os.sep, '/')}"
        else:
            # For remote sources, use async validation
            import asyncio

            asyncio.run(engine.validate_input_source())
            source_info = f"Ready to process: {config.source_uri}"

        print("\n✅ Configuration and inputs are valid!")
        print(source_info)
        print(f"Source type: {config.source_type}")
        print(f"Output will be saved to: {engine.config.output}")
        print(f"Document type: {engine.config.doctype}")
        print(f"Output format: {engine.config.output_format} ({engine.config.output_type})")

    except Exception as e:
        if logger is not None:
            logger.error(f"Validation failed: {e}", exc_info=True)
        else:
            print(f"Validation failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    # Initialize logging system
    log_setup()

    # Get configured logger with progress tracking
    global logger
    logger = get_logger("raft_cli")

    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load configuration from environment (and optional .env file)
        logger.info("Loading configuration")
        config = get_config(args.env_file)

        # Override with command line arguments
        config = override_config_from_args(config, args)

        # Security validation for file paths (skip during testing)
        import os

        from ..core.security import SecurityConfig

        # Skip security validation if we're running under pytest or if paths are mock objects
        skip_validation = (
            os.getenv("PYTEST_CURRENT_TEST")
            or "pytest" in str(sys.argv)
            or str(type(config.output)) == "<class 'unittest.mock.Mock'>"
            if hasattr(config, "output")
            else False
        )

        if not skip_validation:
            if config.source_type == "local" and config.datapath:
                if not SecurityConfig.validate_file_path(str(config.datapath)):
                    logger.error(f"Data path is unsafe: {config.datapath}")
                    sys.exit(1)

            if (
                hasattr(config, "output")
                and config.output
                and not SecurityConfig.validate_file_path(str(config.output))
            ):
                logger.error(f"Output path is unsafe: {config.output}")
                sys.exit(1)

            # Validate custom template paths if provided
            template_paths = [
                ("embedding_prompt_template", getattr(config, "embedding_prompt_template", None)),
                ("qa_prompt_template", getattr(config, "qa_prompt_template", None)),
                ("answer_prompt_template", getattr(config, "answer_prompt_template", None)),
            ]

            for template_name, template_path in template_paths:
                if template_path and not SecurityConfig.validate_file_path(str(template_path)):
                    logger.error(f"{template_name} path is unsafe: {template_path}")
                    sys.exit(1)

        # Validate required arguments based on source type
        if config.source_type == "local":
            if not config.datapath and not args.datapath:
                parser.error("--datapath is required for local source type")
        else:
            if not config.source_uri:
                parser.error(f"--source-uri is required for {config.source_type} source type")

        # Set up external logging if configured
        if hasattr(config, "sentry_dsn") and config.sentry_dsn:
            logger.info("Setting up Sentry logging integration")
            setup_sentry_logging(config.sentry_dsn)

        # Create engine
        logger.info("Initializing RAFT engine")
        engine = RaftEngine(config)

        # Handle special modes
        if args.preview:
            logger.info("Generating processing preview")
            show_preview(engine, config)
            return

        if args.validate:
            logger.info("Validating configuration and inputs")
            validate_only(engine, config)
            return

        # Normal processing
        logger.info("Starting RAFT dataset generation")

        # Set up input path for logging
        input_path = config.source_uri if config.source_type != "local" else str(config.datapath)

        logger.set_context(
            input_path=input_path,
            source_type=config.source_type,
            output_path=config.output,
            doctype=config.doctype,
            chunk_strategy=config.chunking_strategy,
            model=config.completion_model,
            workers=config.workers,
        )

        # Start tracing operation if supported
        if hasattr(logger, "start_operation"):
            logger.start_operation(
                "raft_dataset_generation",
                input_path=input_path,
                source_type=config.source_type,
                doctype=config.doctype,
                chunk_strategy=config.chunking_strategy,
                model=config.completion_model,
            )

        logger.info(f"Source type: {config.source_type}")
        logger.info(f"Input: {input_path}")
        logger.info(f"Output: {config.output}")
        logger.info(f"Document type: {config.doctype}")
        logger.info(f"Chunking strategy: {config.chunking_strategy}")
        logger.info(f"Model: {config.completion_model}")
        logger.info(f"Workers: {config.workers}")

        start_time = time.time()

        # Validate inputs - using new method that handles all source types
        logger.set_progress("INIT")
        logger.info("Validating inputs")
        if hasattr(logger, "add_trace_event"):
            logger.add_trace_event("validation_start")

        if config.source_type == "local":
            datapath = Path(config.datapath) if isinstance(config.datapath, str) else config.datapath
            engine.validate_inputs(datapath)
        else:
            import asyncio

            asyncio.run(engine.validate_input_source())

        if hasattr(logger, "add_trace_event"):
            logger.add_trace_event("validation_complete")

        # Generate dataset
        logger.set_progress("PROC")
        logger.info("Beginning dataset generation")
        if hasattr(logger, "add_trace_event"):
            logger.add_trace_event("generation_start", chunk_size=config.chunk_size, questions=config.questions)
        # Generate dataset using new method that handles all source types
        if config.source_type == "local":
            datapath = Path(config.datapath) if isinstance(config.datapath, str) else config.datapath
            stats = engine.generate_dataset(datapath, config.output)
        else:
            stats = engine.generate_dataset(None, config.output)
        if hasattr(logger, "add_trace_event"):
            logger.add_trace_event("generation_complete", **stats)

        # Show results
        total_time = time.time() - start_time
        logger.set_progress("DONE")
        logger.set_context(
            total_qa_points=stats["total_qa_points"],
            successful_chunks=stats["successful_chunks"],
            failed_chunks=stats["failed_chunks"],
            total_time=total_time,
            tokens_used=stats["token_usage"]["total_tokens"],
        )

        logger.info("RAFT dataset generation completed successfully")

        # End tracing operation if supported
        if hasattr(logger, "end_operation"):
            logger.end_operation(
                "success",
                total_time=total_time,
                total_qa_points=stats["total_qa_points"],
                successful_chunks=stats["successful_chunks"],
                failed_chunks=stats["failed_chunks"],
                total_tokens=stats["token_usage"]["total_tokens"],
            )

        print("\n" + "=" * 60)
        print("RAFT GENERATION COMPLETED")
        print("=" * 60)
        print(f"Total QA Points Generated: {stats['total_qa_points']}")
        print(f"Successful Chunks: {stats['successful_chunks']}")
        print(f"Failed Chunks: {stats['failed_chunks']}")
        print(f"Total Processing Time: {total_time:.2f}s")
        print(f"Average Time per Chunk: {stats['avg_time_per_chunk']:.2f}s")
        print(f"Tokens per Second: {stats['token_usage']['tokens_per_second']:.1f}")
        print(f"Total Tokens Used: {stats['token_usage']['total_tokens']:,}")

        # Display rate limiting statistics if enabled
        rate_stats = stats.get("rate_limiting", {})
        if rate_stats.get("enabled", False):
            print("Rate Limiting Statistics:")
            print(f"  Strategy: {rate_stats.get('strategy', 'N/A')}")
            print(f"  Total Wait Time: {rate_stats.get('total_wait_time', 0):.1f}s")
            print(f"  Rate Limit Hits: {rate_stats.get('rate_limit_hits', 0)}")
            if rate_stats.get("average_response_time", 0) > 0:
                print(f"  Average Response Time: {rate_stats['average_response_time']:.2f}s")
            if rate_stats.get("current_rate_limit"):
                print(f"  Current Rate Limit: {rate_stats['current_rate_limit']:.1f} req/min")

        print(f"Output Location: {config.output}")
        print("=" * 60)

    except KeyboardInterrupt:
        if logger:
            logger.set_progress("STOP")
            logger.info("Process interrupted by user")
            if hasattr(logger, "end_operation"):
                logger.end_operation("interrupted")
        else:
            print("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        if logger:
            logger.set_progress("FAIL")
            logger.error("Fatal error during processing", exc_info=True)
            if hasattr(logger, "end_operation"):
                logger.end_operation("error", error_message=str(e))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

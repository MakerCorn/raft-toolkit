"""
Template loading utilities for prompts used in embeddings and Q&A generation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..config import RaftConfig

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Utility class for loading and managing prompt templates."""

    DEFAULT_TEMPLATES = {
        "embedding": """
Default embedding prompt for document processing.

Instructions for the embedding model:
Generate a high-quality vector embedding for the following document content.
The embedding should capture the semantic meaning, key concepts, and contextual information
to enable effective similarity search and retrieval in a RAG (Retrieval-Augmented Generation) system.

Document Type: {document_type}
Content: {content}

Focus on understanding the main themes, technical concepts, factual information,
and relationships described in the content to create meaningful embeddings.
""".strip(),
        "gpt_qa": """You are a synthetic question-answer pair generator. Given a chunk of context about """
        """some topic(s), generate %s example questions a user could ask that:
- Comply with OpenAI's content filtering policies (no unsafe, offensive, or inappropriate content).
- Can be answered using only the information present in the provided context.
- Are clear, specific, and relevant to the context.
- Vary in complexity (include both simple factual and more analytical questions when possible).

For example, if the context is a Wikipedia paragraph about the United States, an example question could be:
- "How many states are in the United States?"
- "What is the capital of the United States?"
- "How has the number of states in the United States changed over time?"

Return only the list of questions, one per line, with no additional commentary or explanation.""",
        "gpt": """
    Question: {question}
    Context: {context}
    
    Please answer the question using only the information provided in the context above. Follow these instructions:
    - Begin with a clear, step-by-step reasoning process. Explain how you arrive at the answer, referencing relevant context. Use your own words for reasoning, but if you quote directly from the context, enclose those sentences in ##begin_quote## and ##end_quote##. Everything outside of these tags should be your own synthesis.
    - Format your answer as shown below, using Markdown. For every fact or statement, include a citation in the format [CIT:source_id:CIT], where source_id is from the sources list.
    - After the answer, provide 2-3 thoughtful follow-up questions a user might ask next, based on your answer.
    - Do not include information that is not present in the context.

    Example:
    <ANSWER>
    **Reasoning:**
    1. The context states ##begin_quote##"The mitochondria is the powerhouse of the cell."##end_quote##, which describes the main function of mitochondria.
    2. The question asks about the role of mitochondria, so I will summarize this information and cite the source.
    
    **Answer:**
    The mitochondria is responsible for producing energy in the cell by converting nutrients into ATP, the cell's main energy currency. [CIT:1234abcd:CIT]
    </ANSWER>
    <FOLLOW_UP_QUESTIONS>
    - How does the mitochondria convert nutrients into ATP?
    - What happens if mitochondria do not function properly?
    - Are there differences in mitochondria between cell types?
    </FOLLOW_UP_QUESTIONS>
""".strip(),
        "llama_qa": """You are a synthetic question generator.

Instructions:
- Given a chunk of context about some topic(s), generate %s example questions a user could ask.
- Each question must be answerable using only information from the provided context.
- Generate one question per line, and output only the questions (no explanations or commentary).
- Ensure all questions are clear, specific, and relevant to the context.
- Vary the complexity: include both simple factual and more analytical questions when possible.
- All questions must comply with OpenAI's content filtering policies (no unsafe, offensive, or inappropriate content).
- Questions should be succinct and natural.

Here are some samples:
Context: A Wikipedia paragraph about the United States,
Questions:
How many states are in the United States?
What is the capital of the United States?
How has the number of states in the United States changed over time?

Context: A Wikipedia paragraph about vampire bats,
Questions:
What are the different species of vampire bats?
How do vampire bats obtain their food?
What adaptations help vampire bats survive in their environment?""",
        "llama": """
    Question: {question}
    Context: {context}

    Please answer the question using only the information provided in the context above.
    
    Instructions:
    - Begin with a clear, step-by-step reasoning process, explaining how you arrive at the answer. Reference relevant parts of the context.
    - When quoting directly from the context, enclose those sentences in ##begin_quote## and ##end_quote##. Everything outside of these tags should be your own synthesis.
    - Explain which parts of the context are meaningful and why.
    - Summarize how you reached your answer.
    - End your response with the final answer in the form <ANSWER>: $answer. The answer should be succinct and must begin with the tag "<ANSWER>:".
    - Do not use information that is not present in the context.

    Here are some improved samples:

    Example question: What movement did the arrest of Jack Weinberg in Sproul Plaza give rise to?
    Example answer: To answer the question, I first look for references to Jack Weinberg's arrest in the context. I find the sentence: ##begin_quote##The arrest in Sproul Plaza of Jack Weinberg, a recent Berkeley alumnus and chair of Campus CORE, prompted a series of student-led acts of formal remonstrance and civil disobedience that ultimately gave rise to the Free Speech Movement##end_quote##. This sentence directly connects the arrest to the emergence of the Free Speech Movement. Therefore, based on the context provided, the arrest of Jack Weinberg in Sproul Plaza gave rise to the Free Speech Movement.
    <ANSWER>: Free Speech Movement

    Example question: What is the main function of mitochondria?
    Example answer: I search the context for information about mitochondria. The context states: ##begin_quote##"The mitochondria is the powerhouse of the cell."##end_quote##. This means mitochondria produce energy for the cell. Therefore, the main function of mitochondria is to generate energy for cellular processes.
    <ANSWER>: Producing energy for the cell
""".strip(),
        # Additional simple templates for fallback
        "simple_qa": """Generate %d questions based on the following context that can be answered from the text.

Instructions:
- Each question should be answerable using only the provided context
- Questions should be clear and specific
- Return only the questions, one per line

Context: {context}""",
        "simple": """Question: {question}
Context: {context}

Please answer the question using only the information provided in the context above.

Answer:""",
        "default": """Question: {question}
Context: {context}

Please provide a clear answer based on the context above. If the context doesn't contain enough information to answer the question, say so.

Answer:""",
    }

    def __init__(self, config: RaftConfig):
        """Initialize template loader with configuration."""
        self.config = config
        self.templates_dir = Path(config.templates)
        self._cache: Dict[str, str] = {}

    def load_template(self, template_name: str, template_type: str = "prompt") -> Optional[str]:
        """
        Load a template from file.

        Args:
            template_name: Name of the template file or key
            template_type: Type of template ("prompt", "qa", "embedding")

        Returns:
            Template content as string, or None if not found
        """
        cache_key = f"{template_name}_{template_type}"

        # Return cached template if available
        if cache_key in self._cache:
            return self._cache[cache_key]

        # If template_name ends with .txt, treat it as a direct file path
        if template_name.endswith(".txt"):
            file_path = self.templates_dir / template_name
            try:
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        logger.debug(f"Loaded template from {file_path}")
                        self._cache[cache_key] = content
                        return content
            except Exception as e:
                logger.warning(f"Failed to load template from {file_path}: {e}")
            return None

        # Try to load from file
        template_content = self._load_from_file(template_name, template_type)

        # Fall back to default if file not found
        if template_content is None:
            template_content = self._get_default_template(template_name, template_type)

        # Cache and return
        self._cache[cache_key] = template_content
        return template_content

    def _load_from_file(self, template_name: str, template_type: str = "prompt") -> Optional[str]:
        """Load template from file with comprehensive fallback strategy."""
        # Try multiple possible file names in order of preference
        possible_filenames = []

        if template_type == "embedding":
            possible_filenames = [
                "embedding_prompt_template.txt",
                "default_embedding_template.txt",
                "embedding_template.txt",
            ]
        elif template_type == "qa":
            possible_filenames = [
                f"{template_name}_qa_template.txt",
                "default_qa_template.txt",
                "simple_qa_template.txt",
                "qa_template.txt",
            ]
        else:  # prompt/answer
            possible_filenames = [
                f"{template_name}_template.txt",
                "default_answer_template.txt",
                "simple_answer_template.txt",
                "answer_template.txt",
            ]

        for filename in possible_filenames:
            file_path = self.templates_dir / filename
            try:
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        logger.debug(f"Loaded template from {file_path}")
                        return content
            except Exception as e:
                logger.warning(f"Failed to load template from {file_path}: {e}")
                continue

        logger.debug(f"No template files found for {template_name}_{template_type}")
        return None

    def _get_default_template(self, template_name: str, template_type: str = "prompt") -> str:
        """Get default template content with smart fallbacks."""
        if template_type == "embedding":
            return self.DEFAULT_TEMPLATES["embedding"]
        elif template_type == "qa":
            # Try to find the best matching QA template
            if f"{template_name}_qa" in self.DEFAULT_TEMPLATES:
                return self.DEFAULT_TEMPLATES[f"{template_name}_qa"]
            # Fall back to a reasonable default based on template name
            elif template_name.lower().startswith("llama"):
                return self.DEFAULT_TEMPLATES["llama_qa"]
            elif template_name.lower() in ["simple", "basic"]:
                return self.DEFAULT_TEMPLATES["simple_qa"]
            else:
                return self.DEFAULT_TEMPLATES["gpt_qa"]
        else:  # prompt/answer
            # Try to find the best matching answer template
            if template_name in self.DEFAULT_TEMPLATES:
                return self.DEFAULT_TEMPLATES[template_name]
            # Fall back to a reasonable default based on template name
            elif template_name.lower().startswith("llama"):
                return self.DEFAULT_TEMPLATES["llama"]
            elif template_name.lower() in ["simple", "basic"]:
                return self.DEFAULT_TEMPLATES["simple"]
            elif template_name.lower() in ["default", "generic"]:
                return self.DEFAULT_TEMPLATES["default"]
            else:
                return self.DEFAULT_TEMPLATES["gpt"]

    def load_embedding_template(self, custom_path: Optional[str] = None) -> str:
        """
        Load embedding template.

        Args:
            custom_path: Optional custom path to template file

        Returns:
            Template content as string
        """
        if custom_path:
            try:
                # Security validation for custom path
                from ..security import SecurityConfig

                if not SecurityConfig.validate_file_path(custom_path):
                    logger.error(f"Custom embedding template path is unsafe: {custom_path}")
                    return self.load_template("embedding", "embedding") or self.DEFAULT_TEMPLATES["embedding"]

                # Normalize and validate path exists
                from pathlib import Path

                normalized_path = Path(custom_path).resolve()
                if not normalized_path.exists():
                    logger.warning(f"Custom embedding template file not found: {custom_path}")
                    return self.load_template("embedding", "embedding") or self.DEFAULT_TEMPLATES["embedding"]

                # Re-validate after normalization
                if not SecurityConfig.validate_file_path(str(normalized_path)):
                    logger.error(f"Resolved embedding template path is unsafe: {normalized_path}")
                    return self.load_template("embedding", "embedding") or self.DEFAULT_TEMPLATES["embedding"]

                with open(normalized_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    logger.info(f"Loaded custom embedding template from {normalized_path}")
                    return content
            except Exception as e:
                logger.warning(f"Failed to load custom embedding template from {custom_path}: {e}")

        return self.load_template("embedding", "embedding") or self.DEFAULT_TEMPLATES["embedding"]

    def load_qa_template(self, model_type: str, custom_path: Optional[str] = None) -> str:
        """
        Load Q&A generation template.

        Args:
            model_type: Model type (e.g., "gpt", "llama")
            custom_path: Optional custom path to template file

        Returns:
            Template content as string
        """
        if custom_path:
            try:
                # Security validation for custom path
                from ..security import SecurityConfig

                if not SecurityConfig.validate_file_path(custom_path):
                    logger.error(f"Custom Q&A template path is unsafe: {custom_path}")
                    return self.load_template(model_type, "qa") or self.DEFAULT_TEMPLATES["gpt_qa"]

                # Normalize and validate path exists
                from pathlib import Path

                normalized_path = Path(custom_path).resolve()
                if not normalized_path.exists():
                    logger.warning(f"Custom Q&A template file not found: {custom_path}")
                    return self.load_template(model_type, "qa") or self.DEFAULT_TEMPLATES["gpt_qa"]

                # Re-validate after normalization
                if not SecurityConfig.validate_file_path(str(normalized_path)):
                    logger.error(f"Resolved Q&A template path is unsafe: {normalized_path}")
                    return self.load_template(model_type, "qa") or self.DEFAULT_TEMPLATES["gpt_qa"]

                with open(normalized_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    logger.info(f"Loaded custom Q&A template from {normalized_path}")
                    return content
            except Exception as e:
                logger.warning(f"Failed to load custom Q&A template from {custom_path}: {e}")

        return self.load_template(model_type, "qa") or self.DEFAULT_TEMPLATES["gpt_qa"]

    def load_answer_template(self, model_type: str, custom_path: Optional[str] = None) -> str:
        """
        Load answer generation template.

        Args:
            model_type: Model type (e.g., "gpt", "llama")
            custom_path: Optional custom path to template file

        Returns:
            Template content as string
        """
        if custom_path:
            try:
                # Security validation for custom path
                from ..security import SecurityConfig

                if not SecurityConfig.validate_file_path(custom_path):
                    logger.error(f"Custom answer template path is unsafe: {custom_path}")
                    return self.load_template(model_type, "prompt") or self.DEFAULT_TEMPLATES["gpt"]

                # Normalize and validate path exists
                from pathlib import Path

                normalized_path = Path(custom_path).resolve()
                if not normalized_path.exists():
                    logger.warning(f"Custom answer template file not found: {custom_path}")
                    return self.load_template(model_type, "prompt") or self.DEFAULT_TEMPLATES["gpt"]

                # Re-validate after normalization
                if not SecurityConfig.validate_file_path(str(normalized_path)):
                    logger.error(f"Resolved answer template path is unsafe: {normalized_path}")
                    return self.load_template(model_type, "prompt") or self.DEFAULT_TEMPLATES["gpt"]

                with open(normalized_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    logger.info(f"Loaded custom answer template from {normalized_path}")
                    return content
            except Exception as e:
                logger.warning(f"Failed to load custom answer template from {custom_path}: {e}")

        return self.load_template(model_type, "prompt") or self.DEFAULT_TEMPLATES["gpt"]

    def format_template(self, template: str, **kwargs) -> str:
        """
        Format template with provided variables.

        Args:
            template: Template content
            **kwargs: Variables to substitute in template

        Returns:
            Formatted template
        """
        try:
            # Use safe_substitute to handle missing variables gracefully
            from string import Template

            # Convert {var} format to $var format for Template
            template_str = template
            for key, value in kwargs.items():
                template_str = template_str.replace(f"{{{key}}}", f"${key}")

            # Use Template.safe_substitute to handle missing variables
            template_obj = Template(template_str)
            result = template_obj.safe_substitute(**kwargs)

            # Convert back any remaining $var to {var} for consistency
            import re

            result = re.sub(r"\$(\w+)", r"{\1}", result)

            return result
        except Exception as e:
            logger.error(f"Template formatting error: {e}")
            # Fallback: try simple format with available kwargs only
            try:
                import re

                # Find all {var} patterns in template
                pattern = r"\{(\w+)\}"
                matches = re.findall(pattern, template)

                # Only use kwargs that exist in template
                safe_kwargs = {k: v for k, v in kwargs.items() if k in matches}

                # Replace only the variables we have values for
                result = template
                for key, value in safe_kwargs.items():
                    result = result.replace(f"{{{key}}}", str(value))

                return result
            except Exception:
                return template

    def get_available_templates(self) -> Dict[str, list]:
        """
        Get list of available templates in the templates directory.

        Returns:
            Dictionary with template types and available files
        """
        available: Dict[str, List[str]] = {"embedding": [], "qa": [], "answer": []}

        if not self.templates_dir.exists():
            return available

        for file_path in self.templates_dir.glob("*.txt"):
            filename = file_path.name
            if "embedding" in filename:
                available["embedding"].append(filename)
            elif "_qa_" in filename:
                available["qa"].append(filename)
            elif "_template.txt" in filename and "_qa_" not in filename:
                available["answer"].append(filename)

        return available

    def validate_template(self, template: str, template_type: str) -> bool:
        """
        Validate template format and required variables.

        Args:
            template: Template content
            template_type: Type of template to validate

        Returns:
            True if template is valid
        """
        try:
            if template_type == "embedding":
                # Check for embedding-specific variables
                required_vars = ["{content}"]

            elif template_type == "qa":
                # Q&A templates should have %s for question count
                if "%s" not in template and "%d" not in template:
                    logger.warning("Q&A template should contain %s or %d for question count")
                    return False

            elif template_type == "answer":
                # Answer templates should have question and context variables
                required_vars = ["{question}", "{context}"]

                for var in required_vars:
                    if var not in template:
                        logger.warning(f"Answer template missing required variable: {var}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Template validation error: {e}")
            return False

    def get_template_path(self, template_name: str) -> Path:
        """Get the full path to a template file."""
        return self.templates_dir / template_name

    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists."""
        return self.get_template_path(template_name).exists()


def create_template_loader(config: RaftConfig) -> TemplateLoader:
    """Create and return a template loader instance."""
    return TemplateLoader(config)

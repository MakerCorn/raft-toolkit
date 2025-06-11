import time
import uuid
import shutil
import logging
import argparse
import datasets
import pyarrow as pa
import json
import PyPDF2
import random

from mdc import MDC
from tqdm import tqdm
from logconf import log_setup
from typing import Literal, Any
from openai import OpenAI, RateLimitError
from datasets import Dataset, concatenate_datasets
from transformers import AutoTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from client_utils import build_openai_client, build_langchain_embeddings, UsageStats, ChatCompleter
from math import ceil
from format import DatasetConverter, datasetFormats, outputDatasetTypes
from pathlib import Path
from dotenv import load_dotenv
from checkpointing import Checkpointing, checkpointed
from azure.identity import DefaultAzureCredential
from identity_utils import get_azure_openai_token
from pptx import Presentation
from tenacity import retry, wait_exponential, retry_if_exception_type
from raft_utils import load_prompt_template, strip_str, encode_question, encode_question_gen, extract_text_from_pptx

log_setup()

load_dotenv()  # take environment variables from .env.

logger = logging.getLogger("raft")

DocType = Literal["api", "pdf", "json", "txt", "pptx"]


def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command line input.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--datapath", type=Path, default="",
                        help="The path at which the document is located")
    parser.add_argument("--output", type=str, default="./",
                        help="The path at which to save the dataset")
    parser.add_argument("--output-format", type=str, default="hf",
                        help="Format to convert the dataset to. Defaults to hf.", choices=datasetFormats)
    parser.add_argument("--output-type", type=str, default="jsonl",
                        help="Type to export the dataset to. Defaults to jsonl.", choices=outputDatasetTypes)
    parser.add_argument("--output-chat-system-prompt", type=str,
                        help="The system prompt to use when the output format is chat")
    parser.add_argument("--output-completion-prompt-column", type=str, default="prompt",
                        help="The prompt column name to use for the completion format")
    parser.add_argument("--output-completion-completion-column", type=str, default="completion",
                        help="The completion column name to use for the completion format")
    parser.add_argument("--distractors", type=int, default=1,
                        help="The number of distractor documents to include per data point / triplet")
    parser.add_argument("--p", type=float, default=1.0,
                        help="The percentage that the oracle document is included in the context")
    parser.add_argument("--questions", type=int, default=5,
                        help="The number of data points / triplets to generate per chunk")
    parser.add_argument("--chunk_size", type=int, default=512,
                        help="The size of each chunk in number of tokens")
    parser.add_argument("--doctype", type=str, default="pdf",
                        help="The type of the document, must be one of the accepted doctypes", choices=["pdf", "txt", "json", "api", "pptx"])
    parser.add_argument("--openai_key", type=str, default=None,
                        help="Your OpenAI key used to make queries to GPT-3.5 or GPT-4")
    parser.add_argument("--embedding_model", type=str, default="nomic-embed-text",
                        help="The embedding model to use to encode documents chunks (text-embedding-ada-002, ...)")
    parser.add_argument("--completion_model", type=str, default="llama3.2",
                        help="The model to use to generate questions and answers (gpt-3.5, gpt-4, ...)")
    parser.add_argument("--system-prompt-key", default="gpt",
                        help="The system prompt to use to generate the dataset")
    parser.add_argument("--embed-workers", type=int, default=1,
                        help="The number of worker threads to use to generate embeddings")
    parser.add_argument("--workers", type=int, default=1,
                        help="The number of worker threads to use to generate the dataset")
    parser.add_argument("--auto-clean-checkpoints", type=bool, default=False,
                        help="Whether to auto clean the checkpoints after the dataset is generated")
    parser.add_argument("--use-azure-identity", type=bool,
                        default=False, help="Use MS Entra ID for token retrieval")
    parser.add_argument("--pace", type=bool, default=True,
                        help="Whether to pace the calls to the LLM to stay below the Token/Minute limits")
    parser.add_argument("--templates", default="./",
                        help="The system prompt template location")
    parser.add_argument("--chunking-strategy", type=str, default="semantic",
                        help="Chunking strategy to use: semantic, fixed, or sentence")
    parser.add_argument("--chunking-params", type=str, default=None,
                        help="JSON string of extra parameters for the chunker (e.g., '{\"overlap\": 50, \"min_chunk_size\": 200}')")

    args = parser.parse_args()
    return args


prompt_templates = {
    'gpt': 'You are a helpful assistant who can provide an answer given a question and relevant context.',
    'llama': 'You are a a helpful assistant who can provide an answer given a question and relevant context.'
}


def get_chunks(
    data_path: Path,
    doctype: DocType = "pdf",
    chunk_size: int = 512,
    openai_key: str | None = None,
    model: str = None,
    use_azure_identity: bool = True,
    embed_workers: int = 1,
    pace: bool = False,
    chunking_strategy: str = "semantic",
    chunking_params: dict = None,
) -> list[str]:
    """
    Retrieves the document at `data_path`, splits it into chunks using the specified strategy, and returns the chunks.

    Args:
        data_path (Path): Path to the input document or directory.
        doctype (DocType): Type of the document (pdf, txt, json, api, pptx).
        chunk_size (int): Size of each chunk in tokens.
        openai_key (str, optional): OpenAI API key.
        model (str, optional): Embedding model name.
        use_azure_identity (bool): Use Azure identity for authentication.
        embed_workers (int): Number of worker threads for embedding.
        pace (bool): Whether to pace LLM calls.
        chunking_strategy (str): Chunking algorithm to use.
        chunking_params (dict, optional): Extra parameters for the chunker.

    Returns:
        list[str]: List of document chunks as strings.
    """
    chunks = []

    logger.info(
        f"Retrieving chunks from {data_path} of type {doctype} using the {model} model.")

    if doctype == "api":
        with open(data_path) as f:
            api_docs_json = json.load(f)
        chunks = list(api_docs_json)
        chunks = [str(api_doc_json) for api_doc_json in api_docs_json]

        for field in ["user_name", "api_name", "api_call", "api_version", "api_arguments", "functionality"]:
            if field not in chunks[0]:
                raise TypeError(
                    f"API documentation is not in the format specified by the Gorilla API Store: Missing field `{field}`")

    else:
        if (use_azure_identity):
            openai_key = get_azure_openai_token()
        embeddings = build_langchain_embeddings(
            openai_api_key=openai_key, model=model)
        chunks = []
        file_paths = [data_path]
        if data_path.is_dir():
            file_paths = list(data_path.rglob('**/*.' + doctype))

        futures = []
        with tqdm(total=len(file_paths), desc="Chunking", unit="file") as pbar:
            with ThreadPoolExecutor(max_workers=embed_workers) as executor:
                for file_path in file_paths:
                    futures.append(executor.submit(
                        get_doc_chunks, embeddings, file_path, doctype, chunk_size, chunking_strategy, chunking_params))
                    if (pace):
                        time.sleep(15)

                for future in as_completed(futures):
                    doc_chunks = future.result()
                    chunks.extend(doc_chunks)
                    pbar.set_postfix({'chunks': len(chunks)})
                    pbar.update(1)

    return chunks


def get_doc_chunks(
    embeddings: AzureOpenAIEmbeddings,
    file_path: Path,
    doctype: DocType = "pdf",
    chunk_size: int = 512,
    chunking_strategy: str = "semantic",
    chunking_params: dict = None,
) -> list[str]:
    """
    Extracts text from a document and splits it into chunks using the specified chunking strategy and parameters.

    Args:
        embeddings (AzureOpenAIEmbeddings): Embedding model instance.
        file_path (Path): Path to the file to chunk.
        doctype (DocType): Document type.
        chunk_size (int): Target chunk size in tokens.
        chunking_strategy (str): Chunking algorithm ('semantic', 'fixed', 'sentence').
        chunking_params (dict, optional): Extra parameters for the chunker.

    Returns:
        list[str]: List of chunked document strings.
    """
    if chunking_params is None:
        chunking_params = {}
    if doctype == "json":
        with open(file_path, 'r') as f:
            data = json.load(f)
        text = data["text"]
    elif doctype == "pdf":
        text = ""
        logger.info(f"Processing document: {file_path}")
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
    elif doctype == "txt":
        with open(file_path, 'r') as file:
            text = file.read()
    elif doctype == "pptx":
        text = extract_text_from_pptx(file_path)
    elif doctype == "api":
        with open(file_path, 'r') as f:
            data = json.load(f)
        text = str(data)
    else:
        raise TypeError(
            "Document is not one of the accepted types: api, pdf, json, txt, pptx")

    # Select chunking strategy
    if chunking_strategy == "semantic":
        num_chunks = chunking_params.get("number_of_chunks") or ceil(len(text) / chunk_size)
        overlap = chunking_params.get("overlap", 0)
        min_chunk_size = chunking_params.get("min_chunk_size", 0)
        text_splitter = SemanticChunker(
            embeddings,
            number_of_chunks=num_chunks,
            chunk_overlap=overlap,
            min_chunk_size=min_chunk_size
        )
        chunks = text_splitter.create_documents([text])
        chunks = [chunk.page_content for chunk in chunks]
    elif chunking_strategy == "fixed":
        # Simple fixed-size chunking
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    elif chunking_strategy == "sentence":
        # Sentence-based chunking (naive, can be improved)
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) > chunk_size:
                chunks.append(current)
                current = sentence
            else:
                current += (" " if current else "") + sentence
        if current:
            chunks.append(current)
    else:
        raise ValueError(f"Unknown chunking strategy: {chunking_strategy}")
    return chunks


@retry(wait=wait_exponential(multiplier=1, min=10, max=120), reraise=True, retry=retry_if_exception_type(RateLimitError))
def generate_chunk_instructions(chat_completer: ChatCompleter, chunk: Any, x=5, model: str = None) -> list[str]:
    """
    Generates `x` synthetic instructions/questions for an API chunk using an LLM.

    Args:
        chat_completer (ChatCompleter): LLM chat completion client.
        chunk (Any): API chunk (as string or dict).
        x (int): Number of questions/instructions to generate.
        model (str, optional): Model name to use.

    Returns:
        list[str]: List of generated instructions/questions.
    """
    response = chat_completer(
        model=model,
        messages=[
            {"role": "system", "content": "You are a synthetic instruction-api pair generator. Given an API endpoint in the form of a JSON object, generate %s example queries of instructions a user could ask and would be answered by invoking the API call. For example, if the given API call is the `service.users().getProfile(userId='me').execute()` call from the Gmail API, an example query could be 'How can I fetch my Gmail account's email address?'" % (x)},
            {"role": "system", "content": "The API endpoint is a JSON object with required params: user_name, api_name, api_call, api_version, api_arguments, functionality, and optional params: env_requirements, example_code, meta_data, Questions"},
            {"role": "system",
                "content": "For instance, if the api call contains: {'user_name': 'felixzhu555', 'api_name': 'Google Maps - Address Validation', 'api_call': 'Client.addressvalidation(addressLines, regionCode=region_code, locality=locality, enableUspsCass=boolean)', 'api_version': '4.10.0', 'api_arguments': {}, 'functionality': 'Validate an address and its components, standardize the address for mailing, and determine the best known geocode for it.', 'env_requirements': ['googlemaps'], 'example_code': 'client = googlemaps.Client(key='YOUR_API_KEY')\nresponse = client.addressvalidation('1600 Amphitheatre Pk', regionCode='US', locality='Mountain View', enableUspsCass=True)', 'meta_data': {'description': 'The googlemaps python client is an abstraction for the Google Maps API that requires python 3.5+. Each Google Maps web service request requires an API key or client ID. API keys are generated in the 'Credentials' page of the 'APIs & Services' tab of Google Cloud console. This key should be kept secret on your server.'}, 'questions': []}, an example instruction would be 'Validate the following address: University Avenue and, Oxford St, Berkeley, CA 94720.'"},
            {"role": "system", "content": "Don't mention 'API' or use any hints or the name of the API. In one-third of the queries, make sure to include a specific example, like 'Validate this address: 123 Harrison St, Oakland CA'. Include ONLY the queries in your response."},
            {"role": "user", "content": str(chunk)}
        ]
    )

    content = response.choices[0].message.content
    queries = content.split('\n')
    queries = [strip_str(q) for q in queries]
    queries = [q for q in queries if any(c.isalpha() for c in q)]

    return queries


build_qa_messages = {
    "gpt": lambda chunk, x: [
        {"role": "system", "content": prompt_templates["gpt_qa"] % (x)},
        {"role": "system", "content": "The questions should be able to be answered in a few words or less. Include only the questions in your response."},
        {"role": "user", "content": str(chunk)}
    ],
    "llama": lambda chunk, x: [
        {"role": "system", "content": prompt_templates["llama_qa"] % (x)},
        {"role": "system", "content": "The questions should be able to be answered in a few words or less. Include only the questions in your response."},
        {"role": "user", "content": str(chunk)}
    ]
}


@retry(wait=wait_exponential(multiplier=1, min=10, max=120), reraise=True, retry=retry_if_exception_type(RateLimitError))
def generate_instructions_gen(chat_completer: ChatCompleter, chunk: Any, x: int = 5, model: str = None, prompt_key: str = "gpt") -> list[str]:
    """
    Generates `x` synthetic questions for a general chunk (pdf, json, txt) using an LLM.

    Args:
        chat_completer (ChatCompleter): LLM chat completion client.
        chunk (Any): Document chunk as string.
        x (int): Number of questions to generate.
        model (str, optional): Model name to use.
        prompt_key (str): Prompt template key.

    Returns:
        list[str]: List of generated questions.
    """
    response = chat_completer(
        model=model,
        messages=build_qa_messages[prompt_key](chunk, x),
        max_tokens=min(25 * x, 512),  # 25 tokens per question
    )

    content = response.choices[0].message.content
    queries = content.split('\n')
    # queries = [strip_str(q) for q in queries]
    queries = [q for q in queries if any(c.isalpha() for c in q)]

    return queries


def encode_question(question: str, api: Any) -> list[str]:
    """
    Encodes a question and API context into a prompt for the LLM (API case).

    Args:
        question (str): The question/instruction.
        api (Any): API context (as dict or string).

    Returns:
        list[str]: List of prompt messages for the LLM.
    """
    prompts = []

    prompt = question + "\nWrite a python program to call API in " + \
        str(api) + ".\n\nThe answer should follow the format: <<<domain>>> $DOMAIN \n, <<<api_call>>>: $API_CALL \n, <<<api_provider>>>: $API_PROVIDER \n, <<<explanation>>>: $EXPLANATION \n, <<<code>>>: $CODE}. Here are the requirements:\n \n2. The $DOMAIN should be the domain of the API ('N/A' if unknown). The $API_CALL should have only 1 line of code that calls api.\n3. The $API_PROVIDER should be the programming framework used.\n4. $EXPLANATION should be a numbered, step-by-step explanation.\n5. The $CODE is the python code.\n6. Do not repeat the format in your answer."
    prompts.append(
        {"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."})
    prompts.append({"role": "user", "content": prompt})
    return prompts


def encode_question_gen(question: str, chunk: Any, prompt_key: str = "gpt") -> list[str]:
    """
    Encodes a question and chunk context into a prompt for the LLM (general case).

    Args:
        question (str): The question.
        chunk (Any): Document chunk as string.
        prompt_key (str): Prompt template key.

    Returns:
        list[str]: List of prompt messages for the LLM.
    """
    prompts = []

    prompt = prompt_templates[prompt_key].format(
        question=question, context=str(chunk))
    prompts.append(
        {"role": "system", "content": "You are a helpful question answerer who can provide an answer given a question and relevant context."})
    prompts.append(
        {"role": "system", "content": "You will ignore any content that does not comply with Open AI's content filtering policies in the context."})
    prompts.append({"role": "user", "content": prompt})
    return prompts


@retry(wait=wait_exponential(multiplier=1, min=10, max=120), reraise=True, retry=retry_if_exception_type(RateLimitError))
def generate_label(chat_completer: ChatCompleter, question: str, context: Any, doctype: DocType = "pdf", model: str = None, prompt_key: str = "gpt") -> str | None:
    """
    Generates an answer/label for a question using the provided context and LLM.

    Args:
        chat_completer (ChatCompleter): LLM chat completion client.
        question (str): The question.
        context (Any): Context for answering (chunk or API info).
        doctype (DocType): Document type.
        model (str, optional): Model name to use.
        prompt_key (str): Prompt template key.

    Returns:
        str | None: The generated answer/label.
    """
    question = encode_question(question, context) if doctype == "api" else encode_question_gen(
        question, context, prompt_key)
    response = chat_completer(
        model=model,
        messages=question,
        n=1,
        temperature=0,
        max_tokens=512,
    )
    response = response.choices[0].message.content
    return response


def generate_question_cot_answer(
        chat_completer: ChatCompleter,
        chunks: list[str],
        chunk: str,
        chunk_id,
        question,
        doctype: DocType = "api",
        num_distract: int = 3,
        p: float = 0.8,
        model: str = None,
        prompt_key: str = "gpt",
):
    """
    Generates a single QA data point with context, distractors, and answer for a chunk/question.

    Args:
        chat_completer (ChatCompleter): LLM chat completion client.
        chunks (list[str]): All document chunks.
        chunk (str): The current chunk.
        chunk_id (int): Index of the current chunk.
        question (str): The question to answer.
        doctype (DocType): Document type.
        num_distract (int): Number of distractor chunks.
        p (float): Probability of including the oracle chunk.
        model (str, optional): Model name to use.
        prompt_key (str): Prompt template key.

    Returns:
        dict: Data point with question, answer, context, and metadata.
    """
    datapt = {
        "id": None,
        "type": None,
        "question": None,
        "context": None,
        "oracle_context": None,
        "cot_answer": None
    }

    datapt["id"] = str(uuid.uuid4())
    datapt["type"] = "api call" if doctype == "api" else "general"
    datapt["question"] = question

    # add num_distract distractor docs
    docs = [chunk]
    indices = list(range(0, len(chunks)))
    indices.remove(chunk_id)
    for j in random.sample(indices, num_distract):
        docs.append(chunks[j])
    # decides whether to add oracle document
    oracle = random.uniform(0, 1) < p
    if not oracle:
        docs[0] = chunks[random.sample(indices, 1)[0]]
    random.shuffle(docs)

    d = {
        "title": [],
        "sentences": []
    }

    d["title"].append(["placeholder_title"]*(num_distract+1))
    d["sentences"].append(docs)
    datapt["context"] = d
    datapt["oracle_context"] = chunk

    # add answer to q
    datapt["cot_answer"] = generate_label(
        chat_completer, question, chunk, doctype, model=model, prompt_key=prompt_key)

    # construct model instruction
    context = ""
    for doc in docs:
        context += "<DOCUMENT>" + str(doc) + "</DOCUMENT>\n"
    context += question
    datapt["instruction"] = context
    return datapt


def build_or_load_chunks(
        datapath: Path,
        doctype: str,
        CHUNK_SIZE: int,
        OPENAPI_API_KEY: str,
        embedding_model: str,
        checkpoints_dir: Path,
        use_azure_identity: bool,
        embed_workers: int,
        pace: bool,
        chunking_strategy: str = "semantic",
        chunking_params: dict = None,
):
    """
    Loads chunks from checkpoint if available, otherwise builds and saves new chunks.

    Args:
        datapath (Path): Path to the input document or directory.
        doctype (str): Document type.
        CHUNK_SIZE (int): Target chunk size in tokens.
        OPENAPI_API_KEY (str): API key for embedding model.
        embedding_model (str): Embedding model name.
        checkpoints_dir (Path): Directory for checkpoints.
        use_azure_identity (bool): Use Azure identity for authentication.
        embed_workers (int): Number of embedding workers.
        pace (bool): Whether to pace LLM calls.
        chunking_strategy (str): Chunking algorithm.
        chunking_params (dict, optional): Extra parameters for the chunker.

    Returns:
        list[str]: List of document chunks.
    """
    chunks_ds: Dataset = None
    chunks = None
    checkpoints_chunks_path = checkpoints_dir / "chunks"
    logger.info(f"Using checkpoint chunks {checkpoints_chunks_path}")
    if checkpoints_chunks_path.exists():
        chunks_ds = Dataset.load_from_disk(checkpoints_chunks_path)
        chunks = chunks_ds['chunk']

    if not chunks:
        chunks = get_chunks(datapath, doctype, CHUNK_SIZE, OPENAPI_API_KEY, model=embedding_model,
                            use_azure_identity=use_azure_identity, embed_workers=embed_workers, pace=pace,
                            chunking_strategy=chunking_strategy, chunking_params=chunking_params)

    if not chunks_ds:
        chunks_table = pa.table({"chunk": chunks})
        chunks_ds = Dataset(chunks_table)
        chunks_ds.save_to_disk(checkpoints_chunks_path)
    return chunks


def main():
    """
    Main entry point for the RAFT toolkit. Parses arguments, runs chunking, QA generation, and dataset export.
    """

    main_start = time.time()

    # run code
    args = get_args()
    # Parse chunking_params JSON string if provided
    import json as _json
    chunking_params = None
    if args.chunking_params:
        try:
            chunking_params = _json.loads(args.chunking_params)
        except Exception as e:
            logger.error(f"Failed to parse --chunking-params: {e}")
            chunking_params = None
    else:
        chunking_params = None

    # Load system prompt template
    prompt_templates[args.system_prompt_key] = load_prompt_template(
        args.templates + args.system_prompt_key + '_template.txt')
    # Load qa prompt template
    prompt_templates[args.system_prompt_key+"_qa"] = load_prompt_template(
        args.templates + args.system_prompt_key + '_qa_template.txt')

    # Validate arguments
    if args.output_chat_system_prompt and args.output_format != "chat":
        raise Exception(
            "Parameter --output-chat-system-prompt can only be used with --output-format chat")

    if args.use_azure_identity == True:
        credentials = DefaultAzureCredential()
        OPENAPI_API_KEY = get_azure_openai_token()

    client = build_openai_client(
        api_key=OPENAPI_API_KEY
    )
    chat_completer = ChatCompleter(client)

    CHUNK_SIZE = args.chunk_size
    NUM_DISTRACT_DOCS = args.distractors

    output_path = Path(args.output).absolute()

    checkpoints_dir = Path(str(output_path) + "-checkpoints").absolute()
    auto_clean_checkpoints = args.auto_clean_checkpoints
    if auto_clean_checkpoints:
        logger.info(
            f"Checkpoints will be automatically deleted after dataset generation. Remove --auto-clean-checkpoints to deactivate.")

    datapath: Path = args.datapath

    datasets.disable_progress_bar()

    # Chunks
    chunks = build_or_load_chunks(datapath, args.doctype, CHUNK_SIZE, OPENAPI_API_KEY,
                                  args.embedding_model, checkpoints_dir, args.use_azure_identity, args.embed_workers, args.pace,
                                  chunking_strategy=args.chunking_strategy, chunking_params=chunking_params)

    cot_answers_ds = None

    num_chunks = len(chunks)
    num_questions = args.questions
    max_workers = args.workers
    doctype = args.doctype
    completion_model = args.completion_model

    system_prompt_key = args.system_prompt_key

    logger.info(f"Using system prompt key {system_prompt_key}")

    logger.info(f"Using {max_workers} worker threads")

    cot_answers_ds = stage_generate(chat_completer, checkpoints_dir, chunks, num_questions, max_workers, doctype, completion_model,
                                    system_prompt_key, num_distract=NUM_DISTRACT_DOCS, use_azure_identity=args.use_azure_identity, p=args.p)

    # Save as .arrow format
    datasets.enable_progress_bars()
    cot_answers_ds.save_to_disk(str(output_path))

    # Save as .jsonl format
    formatter = DatasetConverter()

    # Extract format specific params
    format_params = {}
    if args.output_chat_system_prompt:
        format_params['system_prompt'] = args.output_chat_system_prompt

    if args.output_format == "completion":
        format_params['prompt_column'] = args.output_completion_prompt_column
        format_params['completion_column'] = args.output_completion_completion_column

    formatter.convert(ds=cot_answers_ds, format=args.output_format, output_path=str(
        output_path), output_type=args.output_type, params=format_params)

    # Warning, this deletes all intermediary checkpoint files
    if auto_clean_checkpoints:
        shutil.rmtree(checkpoints_dir)

    logger.info(
        f"Generated {len(cot_answers_ds)} question/answer/CoT/documents samples")
    logger.info(f"Dataset saved to {output_path}")
    logger.info(f"Done in {time.time() - main_start:.2f}s")


def stage_generate(chat_completer: ChatCompleter, checkpoints_dir, chunks, num_questions, max_workers, doctype, completion_model, system_prompt_key, num_distract, use_azure_identity, p):
    """
    Generates the full dataset by creating QA/distractor triplets for each chunk, with checkpointing and parallelism.

    Args:
        chat_completer (ChatCompleter): LLM chat completion client.
        checkpoints_dir (Path): Directory for checkpoints.
        chunks (list[str]): All document chunks.
        num_questions (int): Number of questions per chunk.
        max_workers (int): Number of worker threads.
        doctype (str): Document type.
        completion_model (str): Model for QA generation.
        system_prompt_key (str): Prompt template key.
        num_distract (int): Number of distractor chunks.
        use_azure_identity (bool): Use Azure identity for authentication.
        p (float): Probability of including the oracle chunk.

    Returns:
        Dataset: HuggingFace Dataset containing all generated data points.
    """

    questions_checkpointing = Checkpointing(checkpoints_dir / "questions")
    answers_checkpointing = Checkpointing(checkpoints_dir / "answers")
    num_chunks = len(chunks)

    @checkpointed(questions_checkpointing)
    @retry(wait=wait_exponential(multiplier=1, min=10, max=120), reraise=True, retry=retry_if_exception_type(RateLimitError))
    def generate_chunk_instructions_ds(chunk: str, chunk_id: int, doctype: str, *args, **kwargs):
        """
        Generates a dataset of instructions for a given chunk.

        Args:
            chunk (str): The document chunk.
            chunk_id (int): The ID/index of the chunk.
            doctype (str): Document type.
            *args: Additional arguments for the instruction generation.
            **kwargs: Additional keyword arguments for the instruction generation.

        Returns:
            Dataset: A dataset containing the generated instructions.
        """
        questions = generate_chunk_instructions(
            chunk=chunk, *args, **kwargs) if doctype == "api" else generate_instructions_gen(chunk=chunk, *args, **kwargs)
        chunk_question_pairs = [
            {"chunk": chunk, "chunk_id": chunk_id, "question": question} for question in questions]
        questions_ds = Dataset.from_list(chunk_question_pairs)
        return questions_ds

    @checkpointed(answers_checkpointing)
    def generate_question_cot_answers(questions_ds, chunk_id: int, chunk: str, *args, **kwargs):
        """
        Generates the CoT answers for a set of questions in a chunk.

        Args:
            questions_ds (Dataset): The dataset of questions.
            chunk_id (int): The ID/index of the chunk.
            chunk (str): The document chunk.
            *args: Additional arguments for the answer generation.
            **kwargs: Additional keyword arguments for the answer generation.

        Returns:
            Dataset: A dataset containing the CoT answers.
        """
        def process_example(chunk, question):
            cot_answer = generate_question_cot_answer(
                chunk=chunk, chunk_id=chunk_id, chunks=chunks, question=question, *args, **kwargs)
            return cot_answer

        results = [process_example(chunk, question) for chunk, question in zip(
            questions_ds['chunk'], questions_ds['question'])]
        table = pa.Table.from_pylist(results)
        ds = Dataset(table)
        return ds

    def process_chunk(i):
        """
        Process a single chunk: generate questions and CoT answers.

        Args:
            i (int): The ID/index of the chunk to process.

        Returns:
            Dataset: A dataset containing the generated CoT answers for the chunk.
        """
        chunk = chunks[i]

        if (use_azure_identity):
            OPENAPI_API_KEY = get_azure_openai_token()
            client = build_openai_client(
                api_key=OPENAPI_API_KEY
            )
            chat_completer = ChatCompleter(client)

        logger.debug(f"Processing chunk id: {i}")
        questions_ds = generate_chunk_instructions_ds(chunk=chunk, chunk_id=i, chat_completer=chat_completer,
                                                      x=num_questions, model=completion_model, doctype=doctype, prompt_key=system_prompt_key)
        answers_ds = generate_question_cot_answers(questions_ds=questions_ds, chunk=chunk, chunk_id=i, chat_completer=chat_completer,
                                                   model=completion_model, doctype=doctype, prompt_key=system_prompt_key, num_distract=num_distract, p=p)
        return answers_ds

    futures = []
    gen_questions_count = 0
    answers_ds_list = []
    usage_stats = UsageStats()

    # we use the checkpointing to keep track of the chunks that have already been processed
    # the answers are generated after the questions so the process might have been stopped in between a batch of answers and matching questions
    # so we need to use the answers checkpointing to keep track of which chunks we need to process
    # if the questions for a given chunk have already been checkpointed, they will just be loaded from the checkpoint
    # we set the tqdm's initial position to avoid having cached data skew the stats
    missing_chunks = answers_checkpointing.missing_checkpoints(num_chunks)

    done_chunks = num_chunks - len(missing_chunks)
    tps = 0
    with tqdm(total=num_chunks, desc="Generating", unit="chunk", initial=done_chunks) as pbar:
        if (max_workers > 1):
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for i in missing_chunks:
                    futures.append(executor.submit(process_chunk, i))

                for future in as_completed(futures):
                    try:
                        answers_ds = future.result()
                        answers_ds_list.append(answers_ds)
                        gen_questions_count += len(answers_ds)
                        stats = chat_completer.get_stats_and_reset()

                        if stats:
                            tps = stats.total_tokens / stats.duration
                            usage_stats += stats
                            if usage_stats.duration > 0:
                                pbar.set_postfix({'qa': gen_questions_count, 'last tok/s': tps,
                                                 'avg tok/s': usage_stats.total_tokens / usage_stats.duration})
                            else:
                                pbar.set_postfix(
                                    {'qa': gen_questions_count, 'last tok/s': tps})

                        pbar.update(1)
                    except Exception as e:
                        logger.error(
                            f"Error processing chunk: {e} ID: {i} Data: {chunks[i]}")
        else:
            for i in missing_chunks:
                try:
                    answers_ds = process_chunk(i)
                    answers_ds_list.append(answers_ds)
                    gen_questions_count += len(answers_ds)
                    stats = chat_completer.get_stats_and_reset()

                    if stats:
                        tps = stats.total_tokens / stats.duration
                        usage_stats += stats
                        if usage_stats.duration > 0:
                            pbar.set_postfix({'qa': gen_questions_count, 'last tok/s': tps,
                                             'avg tok/s': usage_stats.total_tokens / usage_stats.duration})
                        else:
                            pbar.set_postfix(
                                {'qa': gen_questions_count, 'last tok/s': tps})

                    pbar.update(1)
                except Exception as e:
                    logger.error(
                        f"Error processing chunk: {e} ID: {i} Data: {chunks[i]}")

    ds = answers_checkpointing.collect_checkpoints()
    logger.info(
        f"Consumed {usage_stats.prompt_tokens} prompt tokens, {usage_stats.completion_tokens} completion tokens, {usage_stats.total_tokens} total tokens")

    return ds


if __name__ == "__main__":
    with MDC(progress="0%"):
        main()

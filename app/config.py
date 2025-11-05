"""Centralized configuration for the application."""
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load YAML configuration for user-editable settings
_CONFIG_PATH = Path(os.getenv("CONFIG_YAML", "config.yml"))
_yaml_config: dict[str, Any] = {}

if _CONFIG_PATH.exists():
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _yaml_config = yaml.safe_load(f) or {}
else:
    # Fallback to defaults if YAML file doesn't exist
    _yaml_config = {}


def _get_yaml_value(path: str, default: Any = None) -> Any:
    """Get a value from YAML config using dot notation (e.g., 'llm.system_prompts.en')."""
    keys = path.split(".")
    value = _yaml_config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value

# Application metadata
APP_NAME = os.getenv("APP_NAME", "Acme API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
HEALTH_CHECK_PATH = os.getenv("HEALTH_CHECK_PATH", "/health")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE_LLM = float(os.getenv("OPENAI_TEMPERATURE_LLM", "0.3"))
OPENAI_TEMPERATURE_DETECT = float(os.getenv("OPENAI_TEMPERATURE_DETECT", "0"))
OPENAI_TEMPERATURE_TRANSLATE = float(os.getenv("OPENAI_TEMPERATURE_TRANSLATE", "0.3"))
OPENAI_MAX_TOKENS_LLM = int(os.getenv("OPENAI_MAX_TOKENS_LLM", "1000"))
OPENAI_MAX_TOKENS_DETECT = int(os.getenv("OPENAI_MAX_TOKENS_DETECT", "5"))
OPENAI_MAX_TOKENS_TRANSLATE = int(os.getenv("OPENAI_MAX_TOKENS_TRANSLATE", "1000"))

# Embedding model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# Storage configuration
DATA_DIR = Path(os.getenv("DATA_DIR", "app/data"))
INDEX_FILE = DATA_DIR / os.getenv("INDEX_FILE_NAME", "index.faiss")
METADATA_FILE = DATA_DIR / os.getenv("METADATA_FILE_NAME", "metadata.pkl")
DOC_ID_PREFIX = os.getenv("DOC_ID_PREFIX", "doc_")

# Snippet formatting configuration
SNIPPET_MAX_LENGTH = int(os.getenv("SNIPPET_MAX_LENGTH", "160"))
SNIPPET_WORD_BOUNDARY_THRESHOLD = float(os.getenv("SNIPPET_WORD_BOUNDARY_THRESHOLD", "0.7"))

# Search and retrieval configuration
DEFAULT_K = int(os.getenv("DEFAULT_K", "3"))
MAX_K = int(os.getenv("MAX_K", "100"))
SEARCH_K_MULTIPLIER = int(os.getenv("SEARCH_K_MULTIPLIER", "2"))
FAISS_INDEX_TYPE = os.getenv("FAISS_INDEX_TYPE", "IndexFlatL2")

# Language detection configuration
LANGUAGE_DETECTION_THRESHOLD = float(os.getenv("LANGUAGE_DETECTION_THRESHOLD", "0.1"))
LANGUAGE_DETECTION_TEXT_LIMIT = int(os.getenv("LANGUAGE_DETECTION_TEXT_LIMIT", "200"))
LANGUAGE_DEFAULT = os.getenv("LANGUAGE_DEFAULT", "en")
LANGUAGE_DETECTION_PATTERN = os.getenv(
    "LANGUAGE_DETECTION_PATTERN",
    r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"
)

# Supported languages
SUPPORTED_LANGUAGES: list[Literal["en", "ja"]] = ["en", "ja"]

# File upload configuration
ALLOWED_FILE_EXTENSION = os.getenv("ALLOWED_FILE_EXTENSION", ".txt")

# Citation configuration
CITATION_TEMP_FORMAT = os.getenv("CITATION_TEMP_FORMAT", "[doc_{index}]")
CITATION_FINAL_FORMAT = os.getenv("CITATION_FINAL_FORMAT", "[Citation: {doc_id}]")

# LLM prompts (loaded from YAML, fallback to env vars or defaults)
LLM_SYSTEM_PROMPT_EN = os.getenv(
    "LLM_SYSTEM_PROMPT_EN",
    _get_yaml_value("llm.system_prompts.en", "You are a helpful assistant that answers questions using the provided context. Include citations in the format [doc_N] for each piece of information used.")
)
LLM_SYSTEM_PROMPT_JA = os.getenv(
    "LLM_SYSTEM_PROMPT_JA",
    _get_yaml_value("llm.system_prompts.ja", "あなたは質問に答えるアシスタントです。提供されたコンテキスト情報を使用して、質問に正確に答えてください。各回答には[doc_N]形式の引用を含めてください。")
)
LLM_USER_PROMPT_TEMPLATE_EN = os.getenv(
    "LLM_USER_PROMPT_TEMPLATE_EN",
    _get_yaml_value("llm.user_prompt_templates.en", "Question: {query}\n\nContext information:\n{context}\n\nPlease answer the question using the context information above.")
)
LLM_USER_PROMPT_TEMPLATE_JA = os.getenv(
    "LLM_USER_PROMPT_TEMPLATE_JA",
    _get_yaml_value("llm.user_prompt_templates.ja", "質問: {query}\n\nコンテキスト情報:\n{context}\n\n上記のコンテキスト情報を使用して質問に答えてください。")
)

# Empty result messages (loaded from YAML, fallback to env vars or defaults)
EMPTY_RESULT_MESSAGE_EN = os.getenv(
    "EMPTY_RESULT_MESSAGE_EN",
    _get_yaml_value("messages.empty_result.en", "I'm sorry, but I couldn't find any relevant information.")
)
EMPTY_RESULT_MESSAGE_JA = os.getenv(
    "EMPTY_RESULT_MESSAGE_JA",
    _get_yaml_value("messages.empty_result.ja", "申し訳ございませんが、関連する情報が見つかりませんでした。")
)

# Translation prompt template (loaded from YAML, fallback to env vars or defaults)
TRANSLATION_PROMPT_TEMPLATE = os.getenv(
    "TRANSLATION_PROMPT_TEMPLATE",
    _get_yaml_value(
        "translation.prompt_template",
        """Translate the following text from {source_language} to {target_language}.

Important: Preserve all citation markers in the format [Citation: doc_id]. Do not translate citations.

Text to translate:
{text}"""
    )
)

# Language detection prompt template (loaded from YAML, fallback to env vars or defaults)
LANGUAGE_DETECTION_PROMPT_TEMPLATE = os.getenv(
    "LANGUAGE_DETECTION_PROMPT_TEMPLATE",
    _get_yaml_value("language_detection.prompt_template", "Detect the language of this text. Respond with only 'en' for English or 'ja' for Japanese.\n\nText: {text}")
)

# Language name mapping (loaded from YAML, fallback to defaults)
_language_names = _get_yaml_value("languages.names", {})
LANGUAGE_NAME_MAP = {
    "en": _language_names.get("en", "English"),
    "ja": _language_names.get("ja", "Japanese")
}



"""Centralized configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent


class Config:
    # --- ReadMe MCP ---
    README_MCP_URL = os.getenv(
        "README_MCP_URL", "https://interface.autostoresystem.com/mcp"
    )
    README_API_KEY = os.getenv("README_API_KEY", "")

    # --- Azure OpenAI ---
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_API_VERSION = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2024-12-01-preview"
    )

    # --- Outlook / Microsoft Graph ---
    OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID", "")
    OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
    OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "")
    SHARED_MAILBOX = os.getenv("SHARED_MAILBOX", "")  # e.g. support@autostoresystem.com

    # --- Agent behaviour ---
    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    MAX_EMAILS_PER_BATCH = int(os.getenv("MAX_EMAILS_PER_BATCH", "10"))
    ESCALATION_SLA_HOURS = int(os.getenv("ESCALATION_SLA_HOURS", "4"))

    # --- Prompt file paths ---
    SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "system_prompt.md"
    CLASSIFICATION_PROMPT_PATH = PROJECT_ROOT / "prompts" / "classification.md"
    REPLY_TEMPLATES_PATH = PROJECT_ROOT / "prompts" / "reply_templates.md"

    @classmethod
    def load_prompt(cls, path: Path) -> str:
        """Read a prompt file and return its content as a string."""
        return path.read_text(encoding="utf-8")

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of missing required config values."""
        required = {
            "AZURE_OPENAI_ENDPOINT": cls.AZURE_OPENAI_ENDPOINT,
            "AZURE_OPENAI_API_KEY": cls.AZURE_OPENAI_API_KEY,
            "OUTLOOK_CLIENT_ID": cls.OUTLOOK_CLIENT_ID,
            "OUTLOOK_CLIENT_SECRET": cls.OUTLOOK_CLIENT_SECRET,
            "OUTLOOK_TENANT_ID": cls.OUTLOOK_TENANT_ID,
            "SHARED_MAILBOX": cls.SHARED_MAILBOX,
        }
        return [k for k, v in required.items() if not v]
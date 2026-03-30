import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ReadMe MCP
    README_MCP_URL = os.getenv("README_MCP_URL")
    README_API_KEY = os.getenv("README_API_KEY")

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    # Outlook
    OUTLOOK_MCP_URL = os.getenv("OUTLOOK_MCP_URL")
    OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
    OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
    OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID")

    # Agent settings
    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    MAX_EMAILS_PER_BATCH = int(os.getenv("MAX_EMAILS_PER_BATCH", "10"))
    ESCALATION_SLA_HOURS = int(os.getenv("ESCALATION_SLA_HOURS", "4"))

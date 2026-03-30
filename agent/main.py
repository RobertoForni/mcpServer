"""
AutoStore Support Agent — main entry point.

Polls a shared Outlook inbox, classifies emails, retrieves relevant
documentation from the ReadMe MCP server, generates draft replies
using Azure OpenAI, and saves them in the mailbox for human review.
"""

import asyncio
import json
import logging
from datetime import datetime

from openai import AsyncAzureOpenAI

from config import Config
from readme_client import ReadMeClient
from outlook_client import OutlookClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Categories that should NOT generate a doc-based reply
ESCALATE_CATEGORIES = {"Error or Bug", "Out of Scope", "Urgent or Angry"}
REDIRECT_CATEGORIES = {"Hardware/Service"}


# ---------------------------------------------------------------------------
# Step 1: Classify the email
# ---------------------------------------------------------------------------
async def classify_email(
    openai_client: AsyncAzureOpenAI, email: dict
) -> dict:
    """
    Send the email through the classification prompt and return
    a structured result: {"category": "...", "action": "...",
    "search_terms": [...], "confidence": "..."}.
    """
    classification_prompt = Config.load_prompt(Config.CLASSIFICATION_PROMPT_PATH)

    email_text = (
        f"From: {email['sender_name']} <{email['sender_email']}>\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body']}"
    )

    response = await openai_client.chat.completions.create(
        model=Config.AZURE_OPENAI_DEPLOYMENT,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    f"{classification_prompt}\n\n"
                    "Respond with JSON: {\"category\": \"...\", "
                    "\"action\": \"search_docs|escalate|redirect\", "
                    "\"search_terms\": [\"term1\", \"term2\"], "
                    "\"confidence\": \"high|medium|low\"}"
                ),
            },
            {"role": "user", "content": email_text},
        ],
    )

    result_text = response.choices[0].message.content or "{}"
    result = json.loads(result_text)
    logger.info(
        "Classified as: %s (action: %s, confidence: %s)",
        result.get("category"),
        result.get("action"),
        result.get("confidence"),
    )
    return result


# ---------------------------------------------------------------------------
# Steps 2-3: Search and fetch documentation
# ---------------------------------------------------------------------------
async def retrieve_docs(
    readme_client: ReadMeClient, classification: dict
) -> str:
    """
    Use the search terms from classification to search the ReadMe MCP
    server, then fetch full page content for context.

    Implements the search strategy from system_prompt.md:
      Step 1 — Broad search with topic keywords
      Step 2 — Targeted search with specific terms
      Step 3 — Fetch full pages to cross-reference
    """
    search_terms = classification.get("search_terms", [])
    category = classification.get("category", "")

    if not search_terms:
        # Fallback: use the category name as a search term
        search_terms = [category]

    docs_content = await readme_client.search_and_fetch(
        queries=search_terms, max_pages=3
    )

    if not docs_content:
        logger.warning("No documentation found for terms: %s", search_terms)

    return docs_content


# ---------------------------------------------------------------------------
# Step 4: Generate the reply
# ---------------------------------------------------------------------------
async def generate_reply(
    openai_client: AsyncAzureOpenAI,
    email: dict,
    classification: dict,
    docs_context: str,
) -> str:
    """
    Generate a draft reply using the system prompt, retrieved docs,
    and email content.
    """
    system_prompt = Config.load_prompt(Config.SYSTEM_PROMPT_PATH)
    reply_templates = Config.load_prompt(Config.REPLY_TEMPLATES_PATH)

    category = classification.get("category", "General")
    confidence = classification.get("confidence", "medium")

    # Build the context message with retrieved documentation
    context_parts = [
        f"Classification: {category} (confidence: {confidence})",
        f"SLA hours for escalation: {Config.ESCALATION_SLA_HOURS}",
    ]
    if docs_context:
        context_parts.append(
            f"Retrieved documentation:\n\n{docs_context}"
        )
    else:
        context_parts.append(
            "No relevant documentation was found. Use the "
            "'Information Not Available' reply template."
        )

    email_text = (
        f"From: {email['sender_name']} <{email['sender_email']}>\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body']}"
    )

    response = await openai_client.chat.completions.create(
        model=Config.AZURE_OPENAI_DEPLOYMENT,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    f"{system_prompt}\n\n"
                    f"---\nReply Templates:\n{reply_templates}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{chr(10).join(context_parts)}\n\n"
                    f"---\nCustomer email:\n{email_text}\n\n"
                    "Draft a reply following the system prompt rules."
                ),
            },
        ],
    )

    reply = response.choices[0].message.content or ""
    logger.info("Generated reply (%d chars) for: %s", len(reply), email["subject"])
    return reply


# ---------------------------------------------------------------------------
# Step 5: Save draft in Outlook
# ---------------------------------------------------------------------------
async def save_draft(
    outlook_client: OutlookClient, email: dict, reply_text: str
) -> str | None:
    """Create a draft reply in the shared mailbox and mark original as read."""
    draft_id = await outlook_client.create_draft_reply(email["id"], reply_text)
    if draft_id:
        await outlook_client.mark_as_read(email["id"])
    return draft_id


# ---------------------------------------------------------------------------
# Process a single email (full pipeline)
# ---------------------------------------------------------------------------
async def process_email(
    email: dict,
    openai_client: AsyncAzureOpenAI,
    readme_client: ReadMeClient,
    outlook_client: OutlookClient,
) -> dict:
    """
    Run the full agent pipeline for one email:
    classify → search docs → generate reply → save draft.
    """
    result = {
        "email_id": email["id"],
        "subject": email["subject"],
        "category": None,
        "action": None,
        "confidence": None,
        "draft_created": False,
        "draft_id": None,
        "error": None,
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        # Step 1: Classify
        classification = await classify_email(openai_client, email)
        result["category"] = classification.get("category")
        result["action"] = classification.get("action")
        result["confidence"] = classification.get("confidence")

        # Step 2-3: Retrieve documentation (skip for redirects)
        docs_context = ""
        action = classification.get("action", "search_docs")
        if action == "search_docs":
            docs_context = await retrieve_docs(readme_client, classification)
        elif action == "escalate":
            # Still search docs — escalation replies can include partial info
            docs_context = await retrieve_docs(readme_client, classification)

        # Step 4: Generate reply
        reply_text = await generate_reply(
            openai_client, email, classification, docs_context
        )

        # Step 5: Save draft
        draft_id = await save_draft(outlook_client, email, reply_text)
        result["draft_created"] = draft_id is not None
        result["draft_id"] = draft_id

    except Exception as e:
        logger.exception("Error processing email %s: %s", email["id"], e)
        result["error"] = str(e)

    return result


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------
async def poll_loop() -> None:
    """
    Continuously poll the shared mailbox, process new emails,
    and log results.
    """
    # Validate configuration before starting
    missing = Config.validate()
    if missing:
        logger.error("Missing required config: %s", ", ".join(missing))
        raise SystemExit(1)

    # Initialize clients
    openai_client = AsyncAzureOpenAI(
        azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
        api_key=Config.AZURE_OPENAI_API_KEY,
        api_version=Config.AZURE_OPENAI_API_VERSION,
    )

    readme_client = ReadMeClient(
        mcp_url=Config.README_MCP_URL,
        api_key=Config.README_API_KEY,
    )

    outlook_client = OutlookClient(
        tenant_id=Config.OUTLOOK_TENANT_ID,
        client_id=Config.OUTLOOK_CLIENT_ID,
        client_secret=Config.OUTLOOK_CLIENT_SECRET,
        shared_mailbox=Config.SHARED_MAILBOX,
    )

    logger.info(
        "Agent started. Polling %s every %ds (batch size: %d)",
        Config.SHARED_MAILBOX,
        Config.POLL_INTERVAL_SECONDS,
        Config.MAX_EMAILS_PER_BATCH,
    )

    try:
        while True:
            try:
                # Fetch unread emails
                emails = await outlook_client.get_unread_emails(
                    max_count=Config.MAX_EMAILS_PER_BATCH
                )

                # Process each email sequentially
                # (sequential to avoid MCP connection contention)
                for email in emails:
                    logger.info(
                        "Processing: [%s] from %s",
                        email["subject"],
                        email["sender_email"],
                    )
                    result = await process_email(
                        email, openai_client, readme_client, outlook_client
                    )
                    status = "✅" if result["draft_created"] else "❌"
                    logger.info(
                        "%s %s — category: %s, confidence: %s, draft: %s",
                        status,
                        result["subject"],
                        result["category"],
                        result["confidence"],
                        result["draft_id"] or "none",
                    )

                if not emails:
                    logger.info("No unread emails found")

            except Exception as e:
                logger.exception("Error during poll cycle: %s", e)

            # Wait before next poll
            logger.info("Sleeping %ds...", Config.POLL_INTERVAL_SECONDS)
            await asyncio.sleep(Config.POLL_INTERVAL_SECONDS)

    finally:
        await outlook_client.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(poll_loop())
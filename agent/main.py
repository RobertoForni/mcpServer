import asyncio
from config import Config


async def process_email(email: dict) -> dict:
    # Step 1: Classify the email topic
    # TODO: Implement with Azure OpenAI + classification.md prompt

    # Step 2: Search AutoStore docs via ReadMe MCP
    # TODO: Implement with readme_client.py

    # Step 3: Fetch relevant documentation pages
    # TODO: Implement with readme_client.py

    # Step 4: Generate reply using Azure OpenAI
    # TODO: Implement with system_prompt.md + retrieved docs

    # Step 5: Create draft reply in Outlook
    # TODO: Implement with outlook_client.py

    # Step 6: Log the action
    # TODO: Implement logging

    return {"status": "draft_created", "email_id": email.get("id")}


async def main():
    print("AutoStore Support Agent starting...")
    print(f"ReadMe MCP:    {Config.README_MCP_URL}")
    print(f"Azure OpenAI:  {Config.AZURE_OPENAI_ENDPOINT or 'Not configured'}")
    print(f"Outlook MCP:   {Config.OUTLOOK_MCP_URL or 'Not configured'}")
    print(f"Poll interval: {Config.POLL_INTERVAL_SECONDS}s")

    # TODO: Implement polling loop
    # 1. Connect to Outlook MCP
    # 2. Fetch unread emails from support inbox
    # 3. For each email, call process_email()
    # 4. Sleep for POLL_INTERVAL_SECONDS
    # 5. Repeat

    print("Agent skeleton ready. Implement TODOs when dependencies are provisioned.")


if __name__ == "__main__":
    asyncio.run(main())

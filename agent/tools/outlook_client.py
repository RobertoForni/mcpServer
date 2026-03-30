import httpx
from config import Config


class OutlookClient:
    def __init__(self):
        self.mcp_url = Config.OUTLOOK_MCP_URL
        self.client_id = Config.OUTLOOK_CLIENT_ID
        self.tenant_id = Config.OUTLOOK_TENANT_ID

    async def list_unread(self, folder: str = "inbox", limit: int = 10) -> list:
        # TODO: Call Outlook MCP list-mail-messages tool
        # Returns list of unread emails
        raise NotImplementedError("Waiting for IT to provision Outlook MCP")

    async def get_message(self, message_id: str) -> dict:
        # TODO: Call Outlook MCP get-mail-message tool
        # Returns full email content
        raise NotImplementedError("Waiting for IT to provision Outlook MCP")

    async def create_draft_reply(self, message_id: str, body: str) -> dict:
        # TODO: Call Outlook MCP create-draft-reply tool
        # Creates a draft reply in Outlook
        raise NotImplementedError("Waiting for IT to provision Outlook MCP")

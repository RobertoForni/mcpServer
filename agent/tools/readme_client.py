import httpx
from config import Config


class ReadMeClient:
    def __init__(self):
        self.base_url = Config.README_MCP_URL
        self.api_key = Config.README_API_KEY

    async def search(self, query: str) -> list:
        # TODO: Call ReadMe MCP search tool
        # Returns list of matching doc pages with titles and IDs
        raise NotImplementedError("Waiting for AI Booster Pack activation")

    async def fetch(self, page_id: str) -> str:
        # TODO: Call ReadMe MCP fetch tool
        # Returns full markdown content of a doc page
        raise NotImplementedError("Waiting for AI Booster Pack activation")

    async def list_endpoints(self) -> list:
        # TODO: Call ReadMe MCP list-endpoints tool
        # Returns all API paths and methods
        raise NotImplementedError("Implement when ready")

"""Client for the ReadMe MCP server — search and fetch AutoStore docs."""

import logging
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class ReadMeClient:
    """Wraps the ReadMe MCP server to provide search and fetch operations."""

    def __init__(self, mcp_url: str, api_key: str = ""):
        self.mcp_url = mcp_url
        self.headers = {}
        if api_key:
            self.headers["x-readme-auth"] = f"bearer {api_key}"

    async def search(self, query: str) -> list[dict]:
        """
        Search AutoStore docs using the MCP 'search' tool.

        Returns a list of matching pages with titles and IDs.
        """
        logger.info("MCP search: %s", query)
        result = await self._call_tool("search", {"query": query})
        return self._parse_results(result)

    async def fetch(self, page_id: str) -> str:
        """
        Fetch the full content of a documentation page by its ID.

        Returns the page content as a string.
        """
        logger.info("MCP fetch: %s", page_id)
        result = await self._call_tool("fetch", {"id": page_id})
        # The fetch tool returns the full page content as text
        if result and result.content:
            return "\n".join(
                block.text for block in result.content if hasattr(block, "text")
            )
        return ""

    async def search_and_fetch(self, queries: list[str], max_pages: int = 3) -> str:
        """
        Run multiple searches, deduplicate results, and fetch top pages.

        This implements Steps 1-3 of the system prompt search strategy:
        1. Broad search with topic keywords
        2. Targeted search with specific terms
        3. Fetch full pages to cross-reference

        Returns concatenated page content for use as LLM context.
        """
        # Collect unique page IDs across all search queries
        seen_ids = set()
        pages_to_fetch = []

        for query in queries:
            results = await self.search(query)
            for page in results:
                page_id = page.get("id", "")
                if page_id and page_id not in seen_ids:
                    seen_ids.add(page_id)
                    pages_to_fetch.append(page)

        # Fetch full content for top results
        fetched_content = []
        for page in pages_to_fetch[:max_pages]:
            content = await self.fetch(page["id"])
            if content:
                title = page.get("title", "Unknown")
                slug = page.get("slug", "")
                fetched_content.append(
                    f"--- Page: {title} (slug: {slug}) ---\n{content}"
                )
                logger.info("Fetched page: %s (%s)", title, slug)

        return "\n\n".join(fetched_content)

    async def _call_tool(self, tool_name: str, arguments: dict):
        """Open an MCP session and call a single tool."""
        async with streamablehttp_client(
            self.mcp_url, headers=self.headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await session.call_tool(tool_name, arguments)

    @staticmethod
    def _parse_results(result) -> list[dict]:
        """Extract structured page info from MCP search results."""
        pages = []
        if not result or not result.content:
            return pages
        for block in result.content:
            if hasattr(block, "text"):
                # Parse the search result text into page metadata
                # ReadMe MCP returns results with title, id, and slug
                pages.append({"text": block.text, "id": "", "title": "", "slug": ""})
        # If the result contains structured data, prefer that
        if hasattr(result, "structuredContent") and result.structuredContent:
            return result.structuredContent
        return pages
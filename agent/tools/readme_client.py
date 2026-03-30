"""Client for the ReadMe MCP server — search and fetch AutoStore docs."""

import json
import logging
from contextlib import asynccontextmanager

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(self, query: str, session: ClientSession) -> list[dict]:
        """
        Search AutoStore docs using the MCP 'search' tool.

        Returns a list of dicts with at least: id, title, slug.
        """
        logger.info("MCP search: %s", query)
        result = await session.call_tool("search", {"query": query})

        if result.isError:
            logger.error("MCP search error for '%s': %s", query, result.content)
            return []

        return self._parse_results(result)

    async def fetch(self, page_id: str, session: ClientSession) -> str:
        """
        Fetch the full content of a documentation page by its ID.

        Returns the page content as a string.
        """
        logger.info("MCP fetch: %s", page_id)
        result = await session.call_tool("fetch", {"id": page_id})

        if result.isError:
            logger.error("MCP fetch error for '%s': %s", page_id, result.content)
            return ""

        if result and result.content:
            return "\n".join(
                block.text for block in result.content if hasattr(block, "text")
            )
        return ""

    async def search_and_fetch(self, queries: list[str], max_pages: int = 3) -> str:
        """
        Run multiple searches, deduplicate results, and fetch top pages.

        Uses a single MCP session for all calls to avoid opening
        a new connection per tool call.

        Implements Steps 1-3 of the system prompt search strategy:
        1. Broad search with topic keywords
        2. Targeted search with specific terms
        3. Fetch full pages to cross-reference

        Returns concatenated page content for use as LLM context.
        """
        try:
            async with self._connect() as session:
                # Step 1-2: Collect unique pages across all search queries
                seen_ids: set[str] = set()
                pages_to_fetch: list[dict] = []

                for query in queries:
                    results = await self.search(query, session)
                    for page in results:
                        page_id = page.get("id", "")
                        if page_id and page_id not in seen_ids:
                            seen_ids.add(page_id)
                            pages_to_fetch.append(page)

                if not pages_to_fetch:
                    logger.warning(
                        "No pages found for queries: %s", queries
                    )
                    return ""

                # Step 3: Fetch full content for top results
                fetched_content: list[str] = []
                for page in pages_to_fetch[:max_pages]:
                    content = await self.fetch(page["id"], session)
                    if content:
                        title = page.get("title", "Unknown")
                        slug = page.get("slug", "")
                        fetched_content.append(
                            f"--- Page: {title} (slug: {slug}) ---\n{content}"
                        )
                        logger.info("Fetched page: %s (%s)", title, slug)

                return "\n\n".join(fetched_content)

        except Exception as e:
            logger.exception("MCP connection error: %s", e)
            return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def _connect(self):
        """Open a single MCP session for reuse across multiple tool calls."""
        async with streamablehttp_client(
            self.mcp_url, headers=self.headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _parse_results(result) -> list[dict]:
        """
        Extract structured page info from MCP search results.

        The ReadMe MCP search tool returns content blocks as text.
        Each block may be a JSON string with page metadata, or a
        plain-text description. This method tries JSON first, then
        falls back to text extraction.
        """
        pages: list[dict] = []
        if not result or not result.content:
            return pages

        for block in result.content:
            if not hasattr(block, "text") or not block.text:
                continue

            text = block.text.strip()

            # Attempt 1: the entire block is a JSON array of pages
            if not pages and text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and item.get("id"):
                                pages.append({
                                    "id": str(item["id"]),
                                    "title": item.get("title", ""),
                                    "slug": item.get("slug", ""),
                                })
                        if pages:
                            return pages
                except json.JSONDecodeError:
                    pass

            # Attempt 2: the block is a single JSON object
            if text.startswith("{"):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and parsed.get("id"):
                        pages.append({
                            "id": str(parsed["id"]),
                            "title": parsed.get("title", ""),
                            "slug": parsed.get("slug", ""),
                        })
                        continue
                except json.JSONDecodeError:
                    pass

            # Attempt 3: plain text — log it for debugging so we can
            # see the actual format and improve parsing later
            logger.debug("Unparsed MCP search block: %.200s", text)

        if not pages:
            logger.warning(
                "Could not extract page IDs from %d search result blocks. "
                "Run with DEBUG logging to see raw content.",
                len(result.content),
            )

        return pages
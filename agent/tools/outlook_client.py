"""Client for Microsoft Graph API — read emails and create drafts."""

import logging
import re

from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.users.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)
from msgraph.generated.users.item.messages.item.create_reply.create_reply_post_request_body import (
    CreateReplyPostRequestBody,
)
from kiota_abstractions.native_response_handler import NativeResponseHandler
from kiota_abstractions.request_option import RequestOption

logger = logging.getLogger(__name__)

# Simple regex to strip HTML tags for plain-text extraction.
# Not a full HTML parser, but sufficient for email bodies.
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\n{3,}")


def _html_to_text(html: str) -> str:
    """Convert HTML email body to readable plain text."""
    # Replace common block elements with newlines
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</tr>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = _HTML_TAG_RE.sub("", text)
    # Clean up whitespace
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = _WHITESPACE_RE.sub("\n\n", text)
    return text.strip()


class OutlookClient:
    """Read from and draft replies in a shared Outlook mailbox."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        shared_mailbox: str,
    ):
        self.shared_mailbox = shared_mailbox
        self._credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        self._client = GraphServiceClient(
            self._credential,
            scopes=["https://graph.microsoft.com/.default"],
        )

    async def get_unread_emails(self, max_count: int = 10) -> list[dict]:
        """
        Fetch unread emails from the shared mailbox.

        Returns a list of dicts with: id, subject, body (plain text),
        sender_email, sender_name, received_at, conversation_id.
        """
        logger.info(
            "Polling %s for up to %d unread emails",
            self.shared_mailbox,
            max_count,
        )

        query_params = (
            MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                filter="isRead eq false",
                top=max_count,
                orderby=["receivedDateTime asc"],
                select=[
                    "id",
                    "subject",
                    "body",
                    "from",
                    "receivedDateTime",
                    "conversationId",
                ],
            )
        )
        config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params,
            headers={"Prefer": 'outlook.body-content-type="text"'},
        )

        try:
            result = await (
                self._client.users.by_user_id(self.shared_mailbox)
                .messages.get(request_configuration=config)
            )
        except Exception as e:
            logger.exception("Failed to fetch emails from %s: %s", self.shared_mailbox, e)
            return []

        emails = []
        if result and result.value:
            for msg in result.value:
                sender_email = ""
                sender_name = ""
                if msg.from_ and msg.from_.email_address:
                    sender_email = msg.from_.email_address.address or ""
                    sender_name = msg.from_.email_address.name or ""

                # Extract body — prefer the text from the Prefer header,
                # fall back to HTML stripping if Graph ignores the header.
                raw_body = msg.body.content if msg.body else ""
                if msg.body and msg.body.content_type == BodyType.Html:
                    body = _html_to_text(raw_body)
                else:
                    body = raw_body

                emails.append(
                    {
                        "id": msg.id,
                        "subject": msg.subject or "(no subject)",
                        "body": body,
                        "sender_email": sender_email,
                        "sender_name": sender_name,
                        "received_at": str(msg.received_date_time or ""),
                        "conversation_id": msg.conversation_id or "",
                    }
                )

        logger.info("Found %d unread emails", len(emails))
        return emails

    async def create_draft_reply(
        self, message_id: str, reply_body: str
    ) -> str | None:
        """
        Create a draft reply to a specific email.

        Returns the draft message ID, or None on failure.
        """
        logger.info("Creating draft reply for message %s", message_id)

        request_body = CreateReplyPostRequestBody(
            message=Message(
                body=ItemBody(
                    content_type=BodyType.Html,
                    content=_text_to_html(reply_body),
                ),
            ),
        )

        try:
            draft = await (
                self._client.users.by_user_id(self.shared_mailbox)
                .messages.by_message_id(message_id)
                .create_reply.post(request_body)
            )
        except Exception as e:
            logger.exception(
                "Failed to create draft reply for %s: %s", message_id, e
            )
            return None

        draft_id = draft.id if draft else None
        logger.info("Draft created: %s", draft_id)
        return draft_id

    async def mark_as_read(self, message_id: str) -> None:
        """
        Mark an email as read so it's not processed again.

        Failures are logged but not raised — a missed mark_as_read
        means the email will be reprocessed (creating a duplicate
        draft), which is safer than losing an email entirely.
        """
        try:
            update = Message(is_read=True)
            await (
                self._client.users.by_user_id(self.shared_mailbox)
                .messages.by_message_id(message_id)
                .patch(update)
            )
            logger.info("Marked message %s as read", message_id)
        except Exception as e:
            logger.error(
                "Failed to mark message %s as read: %s — "
                "email may be reprocessed on next poll",
                message_id, e,
            )

    async def close(self) -> None:
        """Clean up the credential session."""
        await self._credential.close()


def _text_to_html(text: str) -> str:
    """
    Convert the agent's plain-text reply to simple HTML so it
    renders correctly in Outlook (preserving line breaks and
    paragraphs).
    """
    # Escape HTML entities
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Convert double newlines to paragraphs, single newlines to <br>
    paragraphs = text.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p:
            p = p.replace("\n", "<br>\n")
            html_parts.append(f"<p>{p}</p>")
    return "\n".join(html_parts)
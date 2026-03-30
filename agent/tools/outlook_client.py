"""Client for Microsoft Graph API — read emails and create drafts."""

import logging
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

logger = logging.getLogger(__name__)


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

        Returns a list of dicts with: id, subject, body, sender, received_at,
        conversation_id.
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
        )

        result = await (
            self._client.users.by_user_id(self.shared_mailbox)
            .messages.get(request_configuration=config)
        )

        emails = []
        if result and result.value:
            for msg in result.value:
                sender_email = ""
                sender_name = ""
                if msg.from_ and msg.from_.email_address:
                    sender_email = msg.from_.email_address.address or ""
                    sender_name = msg.from_.email_address.name or ""

                emails.append(
                    {
                        "id": msg.id,
                        "subject": msg.subject or "(no subject)",
                        "body": msg.body.content if msg.body else "",
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
                    content_type=BodyType.Text,
                    content=reply_body,
                ),
            ),
        )

        draft = await (
            self._client.users.by_user_id(self.shared_mailbox)
            .messages.by_message_id(message_id)
            .create_reply.post(request_body)
        )

        draft_id = draft.id if draft else None
        logger.info("Draft created: %s", draft_id)
        return draft_id

    async def mark_as_read(self, message_id: str) -> None:
        """Mark an email as read so it's not processed again."""
        update = Message(is_read=True)
        await (
            self._client.users.by_user_id(self.shared_mailbox)
            .messages.by_message_id(message_id)
            .patch(update)
        )
        logger.info("Marked message %s as read", message_id)

    async def close(self) -> None:
        """Clean up the credential session."""
        await self._credential.close()
"""
Endpoint '/webhook' handler and associated classes
"""

import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from aiohttp.web import Response

if TYPE_CHECKING:
    from aiohttp.web import Request


async def webhook_endpoint_handler(request: "Request") -> "Response":
    """
    Handler for webhook endpoint. Serves as starting point to analysing webhook event and action to
    take on. NOT SUPPOSED TO BE INVOKED OUTSIDE OF AIOHTTP CONTEXT
    """

    event_dict = await request.json()

    try:
        event = WebhookEventModel(event_dict)
    except (InvalidWebhookEvent, InvalidWebhookEventMessage) as e:
        logging.error("Failed to process webhook body with error: %s", e)
        return Response(status=400, text="Invalid event")

    response_status = 400
    response_text = "Don't know what to do with event"

    match event.message:
        case WebhookEventMessageTextModel():
            response_status = 200
            response_text = f"You sent: {event.message.text}"

    return Response(status=response_status, text=response_text)


class InvalidWebhookEvent(Exception):
    """
    Raised by WebhookEventModel if failed to process event dict
    """


class WebhookEventModel:
    """
    Model WhatsApp API webhook event into an object

    Based on technical details provided in:
    https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages

    :raises InvalidWebhookEvent: If failed for any reason
    """

    __event: dict[str, Any]
    __phone_number: str
    __phone_id: str
    __message: "WebhookEventMessageModel"

    @property
    def event(self) -> dict[str, Any]:
        """
        Copy of event this object was created with
        """

        return deepcopy(self.__event)

    @property
    def phone_number(self) -> str:
        """
        Phone number from where message was sent
        """

        return self.__phone_number

    @property
    def phone_id(self) -> str:
        """
        WhatsApp Phone UID from where message was sent
        """

        return self.__phone_id

    @property
    def timestamp(self) -> str:
        """
        Mirror `timestamp` from :class:`WebhookEventMessageModel`. Timestamp at which message was
        sent
        """

        return self.__message.timestamp

    @property
    def message(self) -> "WebhookEventMessageModel":
        """
        :class:`WebhookEventMessageModel` object this object created with
        """

        return self.__message

    def __init__(self, event: dict[str, Any], /):
        self._event = event

        # Value of event.entry[0].changes[0] is main object of event. Extract it for further process
        try:
            entry = event["entry"][0]["changes"][0]["value"]
        except (KeyError, IndexError) as e:
            raise InvalidWebhookEvent(
                "Failed to extract 'entry' value from 'event' dict"
            ) from e

        # Validate event is WhatsApp event, as we could be receiving many different events
        try:
            messaging_product = entry["messaging_product"]
        except KeyError as e:
            raise InvalidWebhookEvent(
                "Failed to extract 'messaging_product' value from 'event' dict"
            ) from e

        if messaging_product != "whatsapp":
            raise InvalidWebhookEvent(
                f"Unknown 'messaging_product' '{messaging_product}'"
            )

        # Extract end-user phone number, and unique WhatsApp-assigned ID
        try:
            self.__phone_number = entry["metadata"]["display_phone_number"]
            self.__phone_id = entry["metadata"]["phone_number_id"]
        except KeyError as e:
            raise InvalidWebhookEventMessage(
                (
                    "Failed to extract 'metadata.display_phone_number' or "
                    "'metadata.phone_number_id' values from 'message' dict"
                )
            ) from e

        # Extract and modelise message value messages[0]
        try:
            message = entry["messages"][0]
        except (KeyError, IndexError) as e:
            raise InvalidWebhookEvent(
                "Failed to extract 'messages' value from 'event' dict"
            ) from e

        try:
            message_type = message["type"]
        except KeyError as e:
            raise InvalidWebhookEvent(
                "Failed to extract 'type' value from 'message' dict"
            ) from e

        if message_type not in ["text"]:
            raise InvalidWebhookEvent("Unknown value for 'type' of 'message' dict")

        match message_type:
            case "text":
                self.__message = WebhookEventMessageTextModel(message)


class WebhookEventMessageModel(ABC):
    # pylint: disable=too-few-public-methods
    """
    Abstract base class to all WhatsApp webhook events messages
    """

    @property
    @abstractmethod
    def timestamp(self):
        """
        Timestamp at which message was sent
        """

    @abstractmethod
    def __init__(self, message: dict[str, Any], /):
        raise Exception(
            "WebhookEventMessageModel can't be instancised directly without inheritance",
        )


class InvalidWebhookEventMessage(Exception):
    """
    Raised by WebhookEventMessageModel if failed to process message dict
    """


class WebhookEventMessageTextModel(WebhookEventMessageModel):
    """
    Model WhatsApp API webhook event message into an object

    Based on technical details provided in:
    https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages

    :raises InvalidWebhookEventMessage: If failed for any reason
    """

    __text: str
    __timestamp: int

    @property
    def text(self) -> str:
        """
        Text content of message
        """

        return self.__text

    @property
    def timestamp(self) -> int:
        return self.__timestamp

    def __init__(self, message: dict[str, Any], /):
        try:
            message_type = message["type"]
        except KeyError as e:
            raise InvalidWebhookEventMessage(
                "Failed to extract 'type' value from 'message' dict"
            ) from e

        if message_type != "text":
            raise InvalidWebhookEventMessage(
                f"Value of 'message' type is '{message_type}'. Expected 'text'"
            )

        try:
            self.__timestamp = message["timestamp"]
            self.__text = message["text"]["body"]
        except KeyError as e:
            raise InvalidWebhookEventMessage(
                "Failed to extract 'timestamp' or 'text.body' values from 'message' dict"
            ) from e

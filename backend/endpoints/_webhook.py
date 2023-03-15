"""
Endpoint '/webhook' handler and associated classes
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import openai
import requests
from aiohttp.web import Response

from ._shared import MESSAGES
from .sql_reporting_northwind import nl_to_sql

if TYPE_CHECKING:
    from aiohttp.web import Request


async def webhook_get_endpoint_handler(request: "Request") -> "Response":
    """
    Handler for webhook GET endpoint. Used by WhatsApp API for verification purposes. NOT SUPPOSED
    TO BE INVOKED OUTSIDE OF AIOHTTP CONTEXT
    """

    hub_mode = request.query["hub.mode"]
    hub_challenge = request.query["hub.challenge"]
    hub_token = request.query["hub.verify_token"]

    if hub_token != "token":
        return Response(status=403, text="Invalid token")

    if hub_mode != "subscribe":
        return Response(status=400, text="Unknwon hub.mode")

    return Response(text=hub_challenge)


async def webhook_post_endpoint_handler(request: "Request") -> "Response":
    """
    Handler for webhook POST endpoint. Serves as starting point to analysing webhook event and
    action to take on. NOT SUPPOSED TO BE INVOKED OUTSIDE OF AIOHTTP CONTEXT
    """

    event_dict = await request.json()

    try:
        event = WebhookEventModel(event_dict)
    except (InvalidWebhookEvent, InvalidWebhookEventMessage) as e:
        logging.error("Failed to process webhook body with error: %s", e)
        return Response(status=400, text="Invalid event")

    response_status = 400

    match event.message:
        case WebhookEventMessageTextModel():
            response_status = 200
            asyncio.create_task(
                process_message(
                    phone_number=event.phone_number,
                    message=event.message.text,
                )
            )

    return Response(status=response_status)


async def process_message(*, phone_number: str, message: str) -> None:
    """
    Primitively process message against general or data query

    This function is invoked as first act after receiving a message on event on webhook. A message
    is data query if prefixed by "data: " or else a general query
    """

    if message.startswith("data: "):
        asyncio.create_task(
            process_message_data(phone_number=phone_number, message=message)
        )
        return

    asyncio.create_task(
        process_message_general(phone_number=phone_number, message=message)
    )


async def process_message_general(*, phone_number: str, message: str) -> None:
    """
    Send message to OpenAI API to generate general response

    This function is invoked as second act of receiving a message of general query. Message is
    prefixed with last 9 messages sent from same phone number in order to generate contextual
    response
    """

    if phone_number not in MESSAGES:
        MESSAGES[phone_number] = []

    answer = openai.Completion.create(
        model="text-davinci-003",
        prompt="\n".join(list(reversed(MESSAGES[phone_number]))[:10])
        + f"\nQ: {message}\nA: ",
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    response_text = answer["choices"][0]["text"]

    MESSAGES[phone_number].append(f"Q: {message}\nA: {response_text}")

    asyncio.create_task(send_message(phone_number=phone_number, message=response_text))


async def process_message_data(*, phone_number: str, message: str) -> None:
    """
    Send message to OpenAI API to format SQL query out of natural-language text and execute it
    against Database

    This function is invoked as second act of receiving a message of data query.
    """

    result = await nl_to_sql(message.replace("data: ", ""))
    asyncio.create_task(send_message(phone_number=phone_number, message=f"{result}"))


async def send_message(*, phone_number: str, message: str) -> None:
    """
    Report response of received message to runtime Output

    If runtime Output (Set with env variable `OUTPUT`) is set to `WHATSAPP`,
    :func:`send_message_whatsapp` will be invoked, else response will be logged to `stdout`
    """

    if os.getenv("OUTPUT") == "WHATSAPP":
        asyncio.create_task(
            send_message_whatsapp(phone_number=phone_number, message=message)
        )
        return

    logging.info("Response to message from '%s' is: %s", phone_number, message)


async def send_message_whatsapp(*, phone_number: str, message: str) -> None:
    """
    Send WhatsApp message using WhatsApp API

    This function is invoked as as final act of processing a message should Backend be set to Output
    to WhatsApp
    """

    r = requests.post(
        f"https://graph.facebook.com/v15.0/{os.getenv('WHATSAPP_APP_ID')}/messages",
        headers={
            "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            # Slice the message to satisfy max of 4096 set by WhatsApp API
            "text": {"body": message[:4095]},
        },
        timeout=30,
    )

    if r.status_code != 200:
        logging.warning(
            "Request to send message failed with error code: %s, response: %s",
            r.status_code,
            r.text,
        )


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
        Mirror `phone_number` from :class:`WebhookEventMessageModel`. Phone number which message
        sent from
        """

        return self.__message.phone_number

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
    def phone_number(self):
        """
        Phone number the message was sent from
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

    __phone_number: str
    __text: str
    __timestamp: int

    @property
    def phone_number(self) -> str:
        return self.__phone_number

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
            self.__phone_number = message["from"]
            self.__timestamp = message["timestamp"]
            self.__text = message["text"]["body"]
        except KeyError as e:
            raise InvalidWebhookEventMessage(
                "Failed to extract 'timestamp' or 'text.body' values from 'message' dict"
            ) from e

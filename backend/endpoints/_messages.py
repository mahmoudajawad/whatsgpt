"""
Endpoint '/messages/{phone}' handler
"""

import json
from typing import TYPE_CHECKING

from aiohttp.web import Response

from ._shared import MESSAGES

if TYPE_CHECKING:
    from aiohttp.web import Request


async def messages_endpoint_handler(request: "Request") -> "Response":
    """
    Handler for messages endpoint. Lists messages send by and received by certain number. Used for
    debugging. NOT SUPPOSED TO BE INVOKED OUTSIDE OF AIOHTTP CONTEXT
    """

    phone = request.match_info["phone"]

    if phone not in MESSAGES:
        return Response(status=400, text="Phone is invalid")

    return Response(
        headers={"Content-Type": "application/json; charset=utf-8"},
        text=json.dumps(MESSAGES[phone]),
    )

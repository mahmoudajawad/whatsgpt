"""
Endpoint '/'
"""

from typing import TYPE_CHECKING

from aiohttp.web import Response

if TYPE_CHECKING:
    from aiohttp.web import Request


async def root_endpoint_handler(_):
    """
    Handler for root endpoint. Serves as imperative health check. NOT SUPPOSED TO BE INVOKED OUTSIDE
    OF AIOHTTP CONTEXT
    """

    return Response(text="WhatsGPT Backend is up and running...")

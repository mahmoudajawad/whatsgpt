"""
Endpoint '/'
"""

from aiohttp.web import Response


async def root_endpoint_handler(_):
    """
    Handler for root endpoint. Serves as imperative health check. NOT SUPPOSED TO BE INVOKED OUTSIDE
    OF AIOHTTP CONTEXT
    """

    return Response(text="WhatsGPT Backend is up and running...")

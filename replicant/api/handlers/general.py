from aiohttp import web
from aiohttp import ClientSession, ClientConnectionError, ServerTimeoutError


async def is_available(request: web.Request, node_ip: str):  # noqa: E501
    session: ClientSession = request.app['session']
    try:
        resp = await session.get(f'http://{node_ip}/status', timeout=5)
    except Exception:
        return {'available': False}

    if resp.status == 200:
        return {'available': True}
    return {'available': False}


async def status(request: web.Request):  # noqa: E501
    replicant = request.app['replicant']
    return replicant.status


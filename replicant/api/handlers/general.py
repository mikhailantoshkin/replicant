from aiohttp import web
from aiohttp import ClientSession
from replicant.utils import run_cmd, set_privileges
import pwd


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


async def node_info(request: web.Request):
    cmd = 'pg_controldata'
    pw_record = pwd.getpwnam('postgres')
    user_uid = pw_record.pw_uid
    user_gid = pw_record.pw_gid
    stdout, stderr = await run_cmd(cmd, '/', preexec_fn=set_privileges(user_uid, user_gid))
    return web.Response(text=f'STDOUT:\n{stdout}\nSTDERR:\n{stderr}')

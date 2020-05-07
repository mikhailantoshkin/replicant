import asyncio
import enum
import pwd

from replicant.config import configuration
from replicant.utils import run_forever
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectionError
from replicant.utils import cancel_and_stop_task, run_cmd, set_privileges, init_db
import logging

logger = logging.getLogger(__name__)


class Status(enum.Enum):
    AVAILABLE = 0
    UNAVAILABLE = 1


class Node:
    def __init__(
            self, name: str, addr: str,
            status: Status, master: bool, priority: int
    ):
        self.name = name
        self.addr = addr
        self.status = status
        self.master = master
        self.priority = priority


class Replicant:

    def __init__(self, session: ClientSession):
        self._mode = configuration['mode']
        self._arbiter_addr = configuration['arbiter_addr']
        self.master = configuration['master']
        self._priority = configuration['priority']
        self._nodes = [Node(name, addr, Status.UNAVAILABLE, False, -1) for name, addr in configuration['nodes'].items()]
        self._session = session
        self._background_task = None
        self._background_db = None

    @property
    def nodes_statuses(self):
        return {node.name: node.status.name for node in self._nodes}

    @property
    def status(self):
        return {'mode': self._mode, 'master': self.master, 'priority': self._priority, 'nodes': self.nodes_statuses}

    async def start(self):
        # init DB
        if self.master:
            cmd = 'bash /docker-entrypoint.sh postgres'
        else:
            cmd = 'bash /replica-setup.sh gosu postgres postgres'
        self._background_db = asyncio.create_task(run_cmd(cmd, '/root'))
        self._background_task = asyncio.create_task(self.check_neighbours())
        if self.master:
            retries = 0
            while retries < 10:
                try:
                    await init_db()
                except Exception:
                    retries += 1
                    await asyncio.sleep(10)
                else:
                    break
            else:
                raise RuntimeError('db init failed')

    async def stop(self):
        await cancel_and_stop_task(self._background_task)
        # stop DB
        await cancel_and_stop_task(self._background_db)

    async def ask_arbiter_if_available(self, node: Node) -> bool:
        try:
            async with self._session.get(
                    f'http://{self._arbiter_addr}:8080/is_available',
                    params={'node_ip': node.addr}, timeout=5) as resp:

                assert resp.status == 200
                data = await resp.json()
                logger.exception(data)
                return data['available']
        except ClientConnectionError:
            raise RuntimeError('Arbiter is unavailable. guess I\' die')

    async def _promote(self):
        # promote, raise priority
        cmd = 'pg_ctl promote'
        pw_record = pwd.getpwnam('postgres')
        user_uid = pw_record.pw_uid
        user_gid = pw_record.pw_gid
        data = await run_cmd(cmd, '/', preexec_fn=set_privileges(user_uid, user_gid))
        logger.debug(data)
        self.master = True

    async def _update_nodes(self):
        for node in self._nodes:
            try:
                logger.debug(f'Checking {node.addr}')
                async with self._session.get(f'http://{node.addr}:8080/status', timeout=5) as resp:

                    assert resp.status == 200
                    node.status = Status.AVAILABLE
                    data = await resp.json()
                    node.master = data['master']
                    node.priority = data['priority']
            except Exception as err:
                logger.error(err)
                node.status = Status.UNAVAILABLE

    @run_forever(repeat_delay=10, failure_delay=5)
    async def check_neighbours(self):
        print('checking neighbours')
        await self._update_nodes()
        if all([node.status == Status.UNAVAILABLE for node in self._nodes]):
            raise RuntimeError('Im blind')
        if self._mode == 'arbiter':
            return
        available_nodes = [node for node in self._nodes if node.status == Status.AVAILABLE]
        unavailable_nodes = [node for node in self._nodes if node.status == Status.UNAVAILABLE]
        for node in available_nodes:
            if self.master and node.master:
                pass
        for node in unavailable_nodes:
            if await self.ask_arbiter_if_available(node):
                #exit(1)
                raise RuntimeError('Im blind bois')
            if node.master:
                if self._priority < min([node.priority for node in available_nodes]):
                    await self._promote()
                    node.master = False



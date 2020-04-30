import asyncio
import enum

from replicant.config import configuration
from replicant.utils import run_forever
from aiohttp import ClientSession
from replicant.utils import cancel_and_stop_task
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

    @property
    def nodes_statuses(self):
        return {node.name: node.status.name for node in self._nodes}

    @property
    def status(self):
        return {'mode': self._mode, 'master': self.master, 'priority': self._priority}

    async def start(self):
        # init DB
        self._background_task = asyncio.create_task(self.check_neighbours())

    async def stop(self):
        await cancel_and_stop_task(self._background_task)
        #stop DB

    async def ask_arbiter_if_dead(self, node: Node) -> bool:
        pass

    async def ask_arbiter_for_promotion(self):
        pass

    async def promote(self):
        # promote, raise priority
        pass

    async def demote(self):
        pass

    async def _update_nodes(self):
        for node in self._nodes:
            try:
                logger.debug(f'Checking {node.addr}')
                async with self._session.get(f'http://{node.addr}/status', timeout=5) as resp:

                    assert resp.status == 200
                    node.status = Status.AVAILABLE
                    data = await resp.json()
                    node.master = data['master']
                    node.priority = data['priority']
            except Exception:
                node.status = Status.UNAVAILABLE

    @run_forever(repeat_delay=60)
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
                await self.ask_arbiter_for_promotion()
        for node in unavailable_nodes:
            if not await self.ask_arbiter_if_dead(node):
                raise RuntimeError('Im blind bois')
            if node.master:
                if self._priority < min([node.priority for node in available_nodes]):
                    await self.promote()




import logging

import aiohttp
from aiohttp.web import Application
from aiohttp_apiset.swagger.operations import OperationIdMapping

from aiohttp import web
from aiohttp_apiset import SwaggerRouter
from aiohttp_apiset.middlewares import jsonify

from replicant.api.handlers import general
from replicant.replicant import Replicant

logger = logging.getLogger(__name__)

spec_dir = 'replicant/api'
spec_file = 'swagger.yml'


def main():

    async def on_startup(app: Application) -> None:
        app['session'] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout())
        app['replicant'] = Replicant(app['session'])
        await app['replicant'].start()

    async def on_cleanup(app: Application) -> None:
        await app['replicant'].stop()
        await app['session'].close()

    opmap = OperationIdMapping()
    opmap.add(general)

    router = SwaggerRouter(swagger_ui='/ui/', search_dirs=[spec_dir])
    router.include(spec=spec_file, operationId_mapping=opmap)

    app = web.Application(router=router, middlewares=[jsonify])

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    logger.debug('Server is starting')
    web.run_app(app)


if __name__ == '__main__':
    main()

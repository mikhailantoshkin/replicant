import asyncio
import configparser
import datetime
import os
from asyncio import CancelledError, sleep, Task
from distutils import util
from functools import wraps
from typing import Dict, Any, Callable, Coroutine, Tuple
import logging
import asyncpg

logger = logging.getLogger(__name__)


def parse_config(conf_path) -> Dict[str, str]:
    config = configparser.ConfigParser()
    if not config.read(conf_path):
        raise RuntimeError('Configuration file cannot be read')
    conf = config['CONFIGURATION']
    nodes = config['NODES']
    configuration: Dict[str: Any] = {
        'mode': conf['REPLICANT_MODE'],
        'arbiter_addr': conf['ARBITER_ADDR'],
        'nodes': {node_name: node_addr for node_name, node_addr in nodes.items()},
        'master': bool(util.strtobool(conf.get('IS_MASTER', 'false'))),
        'priority': conf['PRIORITY']
    }
    return configuration


def run_forever(repeat_delay: int = 0, failure_delay: int = None):
    if failure_delay is None:
        failure_delay = repeat_delay

    def decorator(func: Callable[..., Coroutine]):
        @wraps(func)
        async def task_wrapper(*args, **kwargs):
            logger.debug('Starting endless task')

            while True:
                try:
                    await func(*args, **kwargs)

                except CancelledError:
                    logger.debug('Endless task canceled')
                    raise

                except Exception as err:
                    logger.exception(f'Unexpected error during task ({err}):')
                    await sleep(failure_delay)

                else:
                    await sleep(repeat_delay)

        return task_wrapper

    return decorator


async def run_cmd(cmd: str, cwd: str, **kwargs: Any) -> Tuple[str, str]:
    env = os.environ.copy()

    proc = await asyncio.create_subprocess_exec(
        *cmd.split(),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env=env, cwd=cwd,
        **kwargs
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode:
        raise RuntimeError(stderr.decode("utf-8", "replace"))
    return stdout.decode('utf-8'), stderr.decode('utf-8')


async def cancel_and_stop_task(task: Task):
    """
    Отменяет задачу и ожидает её завершения.
    """
    if task.cancelled():
        logger.debug('Task already canceled')
        return

    task.cancel()

    try:
        await task

    except CancelledError:
        logger.debug('Task has been canceled')
        # WARN: Здесь НЕЛЬЗЯ делать `raise' потому что тогда данная функция никогда не закончится.

    except Exception as err:
        logger.exception(f'Task finished with error ({err}):')

    else:
        logger.debug('Task finished successfully')


def set_privileges(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return result


async def init_db():
    user = os.environ.get('POSTGRES_USER')
    db = os.environ.get('POSTGRES_DB')
    conn = await asyncpg.connect(user=user, database=db)
    await conn.execute('''
          CREATE TABLE users(
              id serial PRIMARY KEY,
              name text,
              dob date
          )
      ''')
    await conn.execute('''
            INSERT INTO users(name, dob) VALUES($1, $2)
        ''', 'Bob', datetime.date(1984, 3, 1))
    await conn.close()
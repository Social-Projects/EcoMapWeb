# coding=utf-8
"""
This module contains class for creating database connection pool.
Class DBPool generates new connections if needed, else returns
connections from Pool._connection_pool. After connection is closed
it returns to Pool._connection_pool.
"""
import threading
from contextlib import contextmanager
import time

import MySQLdb

from config import Config, Singleton
from ecomap.src.python.ecomap.utils import logger

CONFIG = Config().get_config()

# HOST = CONFIG['db.host']
# PORT = CONFIG['db.port']
USER = CONFIG['db.user']
PASSWD = CONFIG['db.password']
DB_NAME = CONFIG['db.db_name']
USING_POOL = CONFIG['db.using_pool']
POOL_SIZE = CONFIG['db.pool_size']
CONNECTION_LIFETIME = CONFIG['db.connection_lifetime']


class OutOfConnectionsError(Exception):
    """
    Exception raised for errors that are related to the
    pool overflow.
    """
    def __init__(self, *args, **kwargs):
        pass
# """
# Exception в manager. Retry - 3 спроби
# 	try:
# 	exception: якщо є експешн - зробити raise і закрити конект
# 	finally: якщо нема експепш - повернути в пул
# decorator Retry:
# 	def retry(retry_quantity, delay):
# 	exceptions:
# 	1) пул занятий
#     2)проблема в конекті до БД(MySQLBaseException)
# декоратор робить 3 спроби потім записує ексепшн в лог.
# якщо всі 3 спроби отримано помилики, то raise error наверх
# """

def retry(retry_quantity, delay):
    def inner_deco(method):
        def wrap(self):
            print 'start %s retries, %s sec' % (retry_quantity, delay)
            try:
                return method(self)
            except:
                for i in xrange(retry_quantity):
                    time.sleep(delay)
                    try:
                        return method(self)
                    except MySQLdb.Error as error:
                        self._log.info('Wrong connection parameters.'
                                       ' Detailed: %s' % error)
                    except OutOfConnectionsError as out:
                        self._log.error('log %s' % out)
                else:
                    self._log.error('error %s')
                    raise
        return wrap
    return inner_deco


def retry2(retry_quantity, delay):
    def inner_deco(method):
        def wrap(self):
            print 'start %s retries, %s sec' % (retry_quantity, delay)
            try:
                for i in xrange(retry_quantity):
                    try:
                        return method(self)
                    except MySQLdb.Error as error:
                        time.sleep(delay)
                        self._log.error('Wrong connection parameters.'
                                       ' Detailed: %s' % error)
                    except OutOfConnectionsError as error:
                        time.sleep(delay)
                        self._log.error('log %s', error)
                else:
                    self._log.exception('error %s' % error)
                    # raise
            except:
                raise
        return wrap
    return inner_deco


class DBPool(object):
    """
    DBPool class represents DB pool, which
    handles and manages work with database
    connections.
    """
    __metaclass__ = Singleton

    def __init__(self,  user, passwd,
                 db_name, conn_lifetime, pool_size):
        self._connection_pool = []
        self.connection_pointer = 0
        self._pool_size = pool_size
        # self._host = host
        # self._port = port
        self._user = user
        self._passwd = passwd
        self._db_name = db_name
        self.connection_open_time = conn_lifetime
        self._log = logger
        self.lock = threading.RLock()

    def __del__(self):
        # for conn in self._connection_pool:
        #     self._close_conn(conn)
        # логику в метод клозе
        [x['connection'].close() for x in self._connection_pool]

    def _create_conn(self):
        """
        Method _create_conn creates connection object.
            :returns opened connection
            :raises MySQLdb.OperationalError
        """
        # try:
        conn = MySQLdb.connect(user=self._user, passwd=PASSWD,
                               db=self._db_name)
        self._log.info('Created connection object: %s.' % conn)
        return {
            'connection': conn,
            'is_used': 0, # ???
            'TTL': time.time()
        }
        # except MySQLdb.Error as error:
        #     self._log.info('Wrong connection parameters. Detailed: %s'
        #                    % error)
            # raise error

    @retry2(3, 5)
    def _get_conn(self):
        """
        Method _get_conn gets connection from the pool or from
        method _create_conn if pool is empty.
            :returns opened connection
            :raises Exception if all connectionsare busy
        """
        if [con for con in self._connection_pool if not con['is_used']]: # ??? is used
            connection = self._connection_pool.pop()
            self.connection_pointer += 1
            connection['is_used'] = 1
            self._log.info('Popped connection %s from the pool.'
                           % connection)
        elif self.connection_pointer < self._pool_size:
            connection = self._create_conn()
            self.connection_pointer += 1
            connection['is_used'] = 1
        else:
            self._log.info('Out of connections.')
            raise OutOfConnectionsError('Out of connections.')
        return connection

        # if not self._connection_pool:
        #     if self.connection_pointer < self._pool_size:
        #         conn = self._create_conn()
        #         self.connection_pointer += 1
        #         return conn
        #     else:
        #         self._log.info('Out of connections')
        #         raise Exception('Out of connections')
        # else:
        #     conn = self._connection_pool.pop()
        #     self.connection_pointer += 1
        #     self._log.info('Popped connection {0} from the pool'
        #                    .format(conn))
        #     return conn

    @contextmanager
    def manager(self):
        """
        Generator manager manages work with connections.
            :yeilds opened connection
        """
        with self.lock:
            conn = self._get_conn()
        yield conn
        if not time.time() - conn['TTL'] > self.connection_open_time:
            self._push_conn(conn)
        else:
            self._close_conn(conn)

    def _close_conn(self, conn):
        """
        Method _close_conn closes connection.
            params:
            - conn - connection that has to be closed
        """
        self._log.info('Closed connection with lifetime %s.' % (time.time() - conn['TTL']))
        self.connection_pointer -= 1
        # conn['is_used'] = 0
        conn['connection'].close()

    def _push_conn(self, conn):
        """
        Method _push_conn pushes connection to pool.
            params:
            - conn - connection that has to be pushed to pool
        """
        self._log.info('Returning connection %s to pool.' % conn)
        self.connection_pointer -= 1
        conn['is_used'] = 0
        self._connection_pool.append(conn)

pool_obj = DBPool(USER, PASSWD, DB_NAME, CONNECTION_LIFETIME, POOL_SIZE)
# with pool_obj.manager() as conn:
#     q1 = conn['connection'].cursor()
#     q1.execute('show tables;')
#     print q1.fetchall()

POOL = DBPool(USER, PASSWD, DB_NAME, CONNECTION_LIFETIME, POOL_SIZE)
#
# def func():
#     "Simple test of connection"
#     print '=' * 20
#     # print POOL.connection_pool
#     # print POOL.outer_connections
#     with POOL.manager() as conn:
#         time.sleep(5)
#         # print POOL.connection_pool
#         # print POOL.outer_connections
#         try:
#             q1 = conn['connection'].cursor()
#             q1.execute('show tables;')
#             # print conn.fetchall()
#         except MySQLdb.ProgrammingError:
#             pass
#     # print POOL.connection_pool
#     # print POOL.outer_connections
#
# threading.Thread(target=func).start()
# threading.Thread(target=func).start()
# threading.Thread(target=func).start()
# threading.Thread(target=func).start()
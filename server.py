# This is data structure for server info in this application.

from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor
import random
import json
import time

from loguru import logger
from ping3 import ping
import requests

import config


# 这里定义了一个名为 ServerInfo 的元组，元组中包含三个字段：available 表示服务器是否可用，
# delay 表示本地机器与服务器之间的延迟，timestamp 表示记录该服务器信息的时间戳。

class ServerInfo(NamedTuple):
    available: bool
    # A delay between host and remove server tested by ping command
    # If not available, delay = 0.0 ms
    delay: float
    # Unix timestamp created by time.time()
    timestamp: float


# 这是一个Python类，用于管理一组服务器的IP地址。以下是这个类的主要功能：
#
# 可以从文件中加载服务器列表，也可以从列表中添加服务器。
# 可以选择一个可用服务器，支持随机选择和选择最小延迟的服务器。
# 可以将服务器列表转换为不带服务器名称的IP地址列表。
# 还提供了其他一些与管理服务器IP地址相关的功能，例如检查服务器是否在列表中，添加或删除单个IP地址以及打印服务器列表。
class Server:

    # 这段代码定义了一个名为Server的类，它包含两个属性serverName和serverIP，分别表示服务器的名称和IP地址。
    # 还有一个availability属性，它是一个列表，用于表示该服务器过去可连接或不可连接的历史记录。
    # 列表中的每个项都是一个名为ServerInfo的命名元组，
    # 其中包含了该服务器当前是否可用、测试时计算出的主机和远程服务器之间的延迟时间以及创建时的时间戳。
    # 注释中还有一行被注释掉的代码，它会在创建Server对象时打印一条日志消息。
    def __init__(self, name, ip):
        self.serverName: str = name
        self.serverIP: str = ip

        # self.availability use a list to represents the history
        # of this server can connect or not.
        # items are NamedTuple: ServerInfo
        self.availability: list = list()

        # logger.info(f"Create {self.__repr__()}")


    # __repr__() 是一个魔术方法（magic method），当我们在调试程序时打印一个对象时会被调用。在这个类中，
    # __repr__() 会返回一个字符串，展示 Server 类的实例的名称和 IP 地址。
    def __repr__(self):
        return f"Server({self.serverName}, {self.serverIP})"

    # 这个函数定义了Server类的相等性比较操作，当两个Server的serverIP相同时，即认为这两个Server是相等的，返回True，否则返回False。
    def __eq__(self, other):
        """
        Check whether Server1 is equal to Server2, depends on their serverIP.

        If you define a __eq__() method, you must define a __hash__() method.
        """
        return self.serverIP == other.serverIP

    # __hash__() 方法用来返回服务器实例的哈希值，它是基于它的 serverIP。
    # 哈希值的目的是使我们有可能将服务器实例作为字典中的键。
    # hash()函数被用来计算serverIP的哈希值。
    def __hash__(self):
        return hash(self.serverIP)

    # test_availability()方法会测试当前服务器是否可用，使用的是ping命令，然后将结果添加到self.availability列表中。
    # 如果服务器不可用，则返回False。否则，将ServerInfo对象添加到self.availability列表中，并返回True。
    # 其中，ServerInfo是一个NamedTuple，用于表示服务器的可用性、延迟和时间戳。
    def test_availability(self):
        """
        Using ping command to test availability of this server,
        then add results to self.availability: list.

        :return: Bool Type: True if test success, else False.
        """
        logger.info(f"Testing server availability: {self.__repr__()}")
        # if host unknown, return False
        # if timeout, return None
        # if success, return delay in ms
        response = ping(f"{self.serverIP}", unit="ms")
        if not response:
            logger.info(f"Testing server availability failed: unknown host {self.__repr__()}")
            self.availability.append(ServerInfo(False, 0, time.time()))
            return False
        elif response is None:
            logger.info(f"Testing server availability failed: timeout {self.__repr__()}")
            self.availability.append(ServerInfo(False, 0, time.time()))
            return False
        else:
            logger.info(f"Testing server availability success: server {self.__repr__()}, time {response}ms")
            self.availability.append(ServerInfo(True, response, time.time()))
            return True


class ServerList:
    # 这段代码定义了一个名为 ServerList 的类。该类负责读取 config.py 文件中的服务器列表，
    # 并在内部维护这些服务器的信息。具体而言，该类包含一个名为 serverList 的列表，其中包含了所有服务器的信息，
    # 每个服务器都是一个 Server 类型的实例。类的构造函数会根据传入的参数从 config.py 中读取指定配置的服务器列表。
    # 该函数将读取到的服务器信息作为 Server 类型的实例添加到 serverList 中。函数执行完毕后，将会记录读取到的服务器数量并返回。
    def __init__(self, cfg: str = "default"):
        """
        Initial a server list instance according to config.py by reading Config.server_list.
        If not specify cfg str, use default Config class.

        :param cfg: config str, mapping to a config class in config.py
        """
        # self.serverList is a list contains Server instances.
        self.serverList = list()
        # read_cnt = self.read_server_list_from_config()
        self.read_server_list_from_config(cfg)
        logger.info(f"Successfully create a {self.__class__.__name__} instance using [config]")

    def read_server_list_from_config(self, cfg: str):

        cnt = 0
        config_cls = config.config[cfg]
        for name, ip_addr in config_cls.server_list.items():
            self.serverList.append(Server(name, ip_addr))
            cnt += 1
        logger.info(f"Successfully reading {cnt} server list from config file")
        return cnt

    # 这是一个在ServerList类中的方法。它使用给定的列表参数lst更新self.serverList，并在更新后将可用的服务器添加到self.serverList中。
    # 在添加之前，它删除旧的不可用服务器。如果这个新服务器是可用的，那么就将它加入到列表中。
    # 最后，它从self.serverList中删除重复的项目。
    def update_server_list_using_list(self, lst: list, server_name: str = "AddedByUser"):
        """
        Update self.serverList with a list param.
        :return: None
        """
        logger.info(f"Update current server list using given list {lst}")
        # Remove old unavailable servers
        self.serverList = [server for server in self.serverList if server.test_availability()]
        for item in lst:
            server = Server(server_name, item)
            # if this server is available, add it to self.serverList
            if server.test_availability():
                self.serverList.append(server)
        # Remove repeated items in self.serverList
        self.serverList = list(set(self.serverList))
        logger.info(f"Successfully update server list, current count is {self.len()}")

    # 返回服务器列表的长度。
    def len(self):
        return len(self.serverList)

    # 检查给定IP地址是否在服务器列表中。
    def contains_ip(self, ip: str):
        """
        Check if given ip is in this class instance.
        Cause of self.serverList contains instance type: Server,
        Server.__eq__() method compares two instances' ip address,
        so, need to construct a Server("temp", ip) instance and then
        check if in self.serverList.

        :param ip: An ip address to check if in self.serverList.
        :return: True or False.
        """
        return Server("temp", ip) in self.serverList

    # 将给定的IP地址添加到服务器列表中。
    def add_ip(self, ip):
        """
        Add single ip by construct a list, and use self.update_server_list_using_list()
        :param ip: An ip address to be added to self.serverList.
        :return: None
        """
        add_list = [ip]
        self.update_server_list_using_list(add_list)

    # 该方法从服务器列表中删除给定的IP地址。它首先构造一个列表，然后调用update_server_list_using_list()方法。
    def remove_ip(self, ip: str):
        """
        Remove item which ip satisfied given ip.
        :param ip: An ip address to be removed in self.serverList.
        :return: None.
        """
        del_server = Server("deleted", ip)
        self.serverList.remove(del_server)

    # 打印当前的服务器列表。
    def print_all_servers(self):
        """
        Print all server info in ServerList.
        :return: None
        """
        for server in self.serverList:
            print(server)

    def ping(self, server: Server):
        """
        Use ping3.ping() method to test ping time.
        Cause of ping3.ping() return value:
            If normal, return [delay: float] in seconds;
            If unknown host, return [False: bool];
            If timeout, return [None].
        :param server: A Server instance (ServerName, ServerIP)
        :return:
        """
        pass

    # 这是一个名为 select_min_ping_server 的方法，用于选择延迟最小的服务器。
    # 方法内部定义了一个线程池，用于并发地执行所有服务器的 ping 测试，并返回延迟最小的那个服务器。
    #
    # 在方法开始时，定义了一个最小延迟变量和一个最小延迟服务器变量。
    # 然后，方法循环遍历服务器列表，并使用线程池并发地测试每个服务器的可用性。
    # 测试结果存储在 server.availability 属性中。一旦所有测试完成，方法再次循环遍历服务器列表，
    # 查找延迟最小的服务器，并将其赋值给 min_ping_server 变量。
    # 最后返回该服务器实例。
    #
    # 如果没有可用的服务器，该方法将返回 None。
    def select_min_ping_server(self):
        """
        If choose_server algorithm is "minimum ping delay",
        use this function to select server.
        :return: If found, return a Server instance, else None.
        """
        # a thread pool to submit tasks for ping command
        pool = ThreadPoolExecutor(max_workers=len(self.serverList))
        # store all futures returned by pool.submit() method
        futures = []

        # default max is 3000.0 ms = 3 s
        min_ping: float = 3000.0
        # default min_ping_server is None, if all server is not available,
        # just return None, let calling function deal with None.
        min_ping_server: Server = None

        for server in self.serverList:
            future = pool.submit(server.test_availability)
            futures.append(future)
        # wait all thread get the result
        [future.result() for future in futures]

        for server in self.serverList:
            this_delay = server.availability[0].delay
            if isinstance(this_delay, float):
                if this_delay < min_ping:
                    min_ping = this_delay
                    min_ping_server = server
        return min_ping_server

    # 随机选择一个服务器。
    def select_random_server(self):
        """
        Using random.choice() method to select and return a random Server.
        :return: A random Server instance in self.ServerList.
        """
        return random.choice(self.serverList)

    # 将可用的决策函数映射到其名称。
    def map_decision_func(self):
        """
        This is a map for <str, func>. Use this to get correct decision function.

        When you have new decision function, update here and config.py



        :return: A dict with <funcName: str, func>
        """
        d = {
            "select_random_server": self.select_random_server,
            "select_min_ping_server": self.select_min_ping_server,
        }
        return d

    # 将服务器列表转换为不带服务器名称的IP地址列表。
    def convert_to_ip_list(self):
        """
        Convert current self.serverList to a IP list without serverName.
        :return: a list of serverIP in self.serverList.
        """
        ret = list()
        for server in self.serverList:
            ret.append(server.serverIP)
        # delete duplicate IP address in self.serverList
        ret = list(set(ret))
        return ret

    # 这个类是用来管理服务器列表的，包含了添加、删除、打印、以及选择最优服务器等方法。
    # 它使用了一个 Server 类来表示服务器，每个服务器有名称和 IP 地址。
    # 其中，add_ip 方法可以用来添加单个 IP 地址，remove_ip 方法可以根据给定的 IP 地址删除服务器，
    # print_all_servers 方法可以打印所有服务器的信息。
    # 而 select_min_ping_server 和 select_random_server 方法则分别用于选择最优服务器，
    # 其中 select_min_ping_server 方法会使用多线程来进行 ping 测试并找到延迟最低的服务器，
    # 而 select_random_server 方法则随机返回一个服务器。map_decision_func 方法则是将选择服务器的方法名称和实际方法进行映射，
    # 用于在 config.py 中读取用户选择的方法。specify_server_list 方法是另一种构造方法，
    # 可以根据给定的服务器列表字典来创建一个 ServerList 实例。
    @classmethod
    def specify_server_list(cls, server_list: dict):
        """
        Another constructor for ServerList class, and I do not use
        __init__() method here.
        Use this method to specify server_list in a dict.
        :param server_list: A dict with <serverName, ServerIP> paris.
        :return: A ServerList instance created by this constructor.

        Or you don't need to use this classmethod, just let __init__()
        has a parameter server_list, and check whether it is None.
        If None, read server list info from config file,
        else use this parameter to initial self.serverList.
        """
        instance = cls.__new__(cls)
        instance.serverList = list()
        for serverName, serverIP in server_list.items():
            instance.serverList.append(Server(serverName, serverIP))
        # Remove duplicated serverIP
        instance.serverList = list(set(instance.serverList))
        logger.info(f"Successfully create a {cls.__name__} instance using [specify_server_list]")
        return instance


# 这是一个继承自ServerList类的FlaskTestServerList类。
# 它重写了父类的__init__方法，用一个名为FlaskTestConfig的配置文件来初始化服务器列表。
# 除了使用配置文件，还可以通过init_server_list_from_url这个类方法从一个特定的url获取服务器列表。
# 在这个方法中，它向指定的url发送一个请求来获取服务器列表，解析返回的数据，然后使用这个列表来初始化self.serverList，
# 最后返回这个FlaskTestServerList实例。
# 如果有多个服务器使用同一个IP，它会在初始化时将它们去重。
class FlaskTestServerList(ServerList):
    def __init__(self):
        """
        A instance of this class can also be created by
        instance = ServerList("FlaskTestConfig")
        """
        super().__init__("FlaskTestConfig")

    @classmethod
    def init_server_list_from_url(cls, url: str):
        """
        ServerList initialization by requesting a specific url that server provide
        to get all servers.
        In FlaskTestInterface, the request url is

        "http://server:ip/getdserverlists",

        Returned data is

        {
        "data": [
            "127.0.0.1",
            "192.168.56.2"
        ]
        }

        Purpose of this method is to request this interface, get data back, parse it,
        use this list to initialize self.serverList, and return this ServerList instance.

        :param url: The url that server provides that this function request to get
        all servers.
        :return: A FlaskTestServerList instance.
        """
        logger.info(f"Starting create a {cls.__name__} instance by getting server from {url}")
        r = requests.get(url)
        # According to response data, get a server list
        response_servers = json.loads(r.text).get("data")

        instance = cls.__new__(cls)
        instance.serverList = list()
        instance.update_server_list_using_list(lst=response_servers,
                                               server_name="AddedFromRemote")
        # Remove duplicated serverIP
        instance.serverList = list(set(instance.serverList))
        logger.info(f"Successfully create a {cls.__name__} instance using [init_server_list_from_url]")
        return instance


# 这是一个继承自ServerList的类BDContractServerList。
# 在初始化时，它通过调用父类构造函数，传入配置文件名SmartContractConfig来初始化服务器列表。
# 这个类没有其他的特别方法或属性，只是继承了ServerList类的所有方法和属性。
class BDContractServerList(ServerList):
    def __init__(self):
        super().__init__("SmartContractConfig")

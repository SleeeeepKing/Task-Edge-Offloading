import bisect
import copy
import time
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

import requests
from loguru import logger

from config import Config
from server import Server, ServerList


# TaskInfo是一个NamedTuple，它有三个属性：server、task和port。
# 它是一个用于存储任务相关信息的数据结构，其中server是一个Server对象，表示服务器的IP地址和名称，
# task是一个字符串，表示要执行的任务，port是一个整数，表示要连接的服务器端口号。
# 这个类的实例通常会被传递给任务提交引擎（DecisionEngine）以便执行任务。
class TaskInfo(NamedTuple):
    server: Server
    task: str
    port: int


class DecisionEngine:

    # 这段代码是定义了一个名为DecisionEngine的class。它有以下几个属性：
    #
    # decision_algorithm: 根据配置文件中的算法名，获取相应的算法函数。
    # server_list: 服务器列表对象。
    # pool: 线程池对象，最大工作线程数量为max_workers。
    # consider_throughout: 是否考虑吞吐量的标志位。
    # default_throughput_period: 吞吐量计算周期的默认时间间隔。
    # expected_throughput: 预期吞吐量。
    # req_time_lst: 请求时间列表。
    # 其中，初始化函数__init__中，使用logger记录了初始化DecisionEngine的一些信息。
    def __init__(
            self,
            *,
            decision_algorithm: str,
            server_list: ServerList,
            max_workers: int = 20,
            consider_throughput: bool = False,
    ):
        self.decision_func = Config.decision_algorithm[decision_algorithm]
        self.server_list = server_list
        self.pool = ThreadPoolExecutor(max_workers)

        self.consider_throughout = consider_throughput
        self.default_throughput_period: int = Config.DEFAULT_THROUGHPUT_PERIOD
        self.expected_throughput: int = Config.EXPECTED_THROUGHPUT
        self.req_time_lst = list()

        logger.info(
            f"Initial DecisionEngine with decision_algorithm: [{decision_algorithm}], [{max_workers}] workers, throughput period [{self.default_throughput_period}] s"
        )

    # 这段代码定义了一个名为 cal_throughput() 的函数，它计算了过去一段时间内的请求吞吐量（throughput），
    # 即该时间段内完成的请求数量。计算方法是：获取当前时间 cur_time，根据设定的默认吞吐量时间间隔
    # self.default_throughput_period 确定开始时间 start_time，并将请求时间戳 self.req_time_lst 按升序排列，
    # 然后通过二分查找找到时间戳在 start_time 和 cur_time 之间的请求数量，即为过去一段时间内的请求吞吐量。最后将吞吐量作为函数的返回值。
    def cal_throughput(self):
        cur_time = time.time()
        start_time = cur_time - self.default_throughput_period

        self.req_time_lst.sort()
        req_st_index = bisect.bisect_right(self.req_time_lst, start_time)
        throughput = len(self.req_time_lst) - req_st_index

        return throughput

    # 这个方法的作用是根据传入的算法函数选择服务器。如果函数返回 None，
    # 那么说明选择失败，返回 None；否则返回选择的服务器。同时会打印一些相关的日志信息。
    def _choose_server_according_to_func(self, func):
        chosen_server = func()
        if chosen_server is None:
            logger.info(f"Failed to choose server using {self.decision_func}")
            return None
        else:
            logger.info(
                f"Successfully choose server {chosen_server} using {self.decision_func}"
            )
            return chosen_server

    # 这段代码中的_choose_server_except_localhost函数是用来选择除了本地主机（IP地址为127.0.0.1）以外的服务器的。
    # 首先，代码通过深拷贝self.server_list得到一个新的服务器列表new_server_list，然后从这个列表中移除本地主机的IP地址。
    # 如果新列表为空，则返回None表示选择失败；否则，从新列表中通过配置的决策算法self.decision_func选择一个服务器作为结果返回。
    def _choose_server_except_localhost(self):
        new_server_list = copy.deepcopy(self.server_list)
        new_server_list.remove_ip("127.0.0.1")
        if new_server_list.len() == 0:
            return None
        else:
            func = new_server_list.map_decision_func().get(self.decision_func)
            chosen_server = func()
            return chosen_server

    # 这是一个名为DecisionEngine的类，它实现了智能合约的任务分配。在初始化时，需要传入一些参数，例如决策算法、服务器列表、最大线程数等等。
    # 其中，decision_algorithm参数表示决策算法，这里的算法包括“随机选择”、“轮询选择”、“负载均衡选择”等等。
    # server_list参数表示服务器列表，即可供选择的服务器IP地址列表。max_workers参数表示最大线程数，用于指定任务执行的最大线程数。
    # consider_throughput参数用于指定是否考虑吞吐量。
    #
    # 该类有一个方法choose_server，用于根据指定的决策算法和服务器列表选择可用的服务器。其中，如果consider_throughput为True，
    # 且服务器列表包含本地服务器（IP地址为127.0.0.1），则会根据当前的吞吐量情况，判断是否需要选择除本地服务器外的其他服务器，
    # 从而达到负载均衡的效果。如果吞吐量超过预期值，则选择除本地服务器外的其他服务器；否则选择本地服务器。
    # 如果consider_throughput为False，则直接根据指定的决策算法和服务器列表进行选择。
    #
    # 此外，类中还实现了一些辅助方法，例如cal_throughput用于计算当前吞吐量；
    # _choose_server_except_localhost用于从除本地服务器外的其他服务器中选择可用的服务器；
    # _choose_server_according_to_func用于根据指定的决策算法选择可用的服务器。
    def choose_server(self):
        func = self.server_list.map_decision_func().get(self.decision_func)

        if self.consider_throughout and self.server_list.contains_ip("127.0.0.1"):
            logger.info("Choose server consider throughput")

            if self.cal_throughput() > self.expected_throughput:

                logger.info(
                    "Current throughput is larger than expected throughput, "
                    + "choose an server except local device"
                )
                return self._choose_server_except_localhost()
            else:

                logger.info(
                    "Current throughput is not larger than expected throughput, "
                    + "choose local device as execution location"
                )
                return Server("LocalDevice", "127.0.0.1")
        else:

            return self._choose_server_according_to_func(func)

    # 这个函数是用来提交任务的。首先，根据传入的ip和port选择执行任务的服务器，
    # 如果没有传入ip则通过DecisionEngine类中的choose_server()函数来选择。
    # 如果未选择到服务器，则函数返回None。
    # 如果选择到了服务器，函数返回一个由ThreadPoolExecutor类的submit方法返回的Future对象和被选中的服务器的IP地址。
    def submit_task(self, task: str, port: int = 80, ip: str = None):

        chosen_server = Server("UserSpecific", ip) if ip else self.choose_server()
        if chosen_server is None:
            logger.info(f"Failed to submit task, chosen server is None")
            return None
        task_added = TaskInfo(chosen_server, task, port)
        logger.info(f"Successfully submit task {task_added} to ThreadPool")

        return self.pool.submit(self.offload_task, task_added), chosen_server.serverIP

    # 这段代码定义了一个offload_task方法，用于在指定的服务器上执行任务。它会根据传入的TaskInfo对象中的服务器IP、任务和端口号，
    # 发出一个GET请求，将任务分配给指定的服务器。
    #
    # 在执行前，offload_task方法会记录当前时间cur_time，并检查任务是否被分配到了本地设备（Server("temp", "127.0.0.1")）。
    # 如果是本地设备，它将当前时间添加到req_time_lst列表中，以便后续计算吞吐量。
    #
    # 最后，该方法返回requests.get方法返回的响应。
    def offload_task(self, data: TaskInfo):

        cur_time = time.time()

        if data.server == Server("temp", "127.0.0.1"):
            self.req_time_lst.append(cur_time)

        logger.info(f"Get task {data} and start offloading." +
                    f" Current time is {cur_time:.2f}, add to req_time_lst")

        server = data.server
        task = data.task
        port = data.port

        logger.info(f"Call remote server {server.serverIP}:{port} with task=\'{task}\'")
        r = requests.get(f"http://{server.serverIP}:{port}/{task}")

        return r

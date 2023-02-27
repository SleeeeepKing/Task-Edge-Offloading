import time
import copy
import bisect
from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
import requests

from config import Config
from server import Server, ServerList


class TaskInfo(NamedTuple):

    server: Server
    task: str
    port: int


class DecisionEngine:
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

    def cal_throughput(self):
        """
        Calculate throughput in a time period:
            throughput = request_count_in_a_certain_time / default_throughput_period

        All requests' timestamp is in self.req_time_lst, use bisection algorithm to
        get the index that upper than start_time. Use length of self.req_time_lst minus
        index get the request counts in this time period.

        :return: A float value of request processing per second.
        """
        cur_time = time.time()
        start_time = cur_time - self.default_throughput_period

        self.req_time_lst.sort()
        req_st_index = bisect.bisect_right(self.req_time_lst, start_time)
        throughput = len(self.req_time_lst) - req_st_index

        return throughput

    def _choose_server_according_to_func(self, func):
        """
        Accoding to func, choose a server.
        :param func: A choose_server function in ServerList.map_decision_func().values.
        :return: A Server instance.
        """
        chosen_server = func()
        if chosen_server is None:
            logger.info(f"Failed to choose server using {self.decision_func}")
            return None
        else:
            logger.info(
                f"Successfully choose server {chosen_server} using {self.decision_func}"
            )
            return chosen_server

    def _choose_server_except_localhost(self):
        new_server_list = copy.deepcopy(self.server_list)
        new_server_list.remove_ip("127.0.0.1")
        if new_server_list.len() == 0:
            return None
        else:
            func = new_server_list.map_decision_func().get(self.decision_func)
            chosen_server = func()
            return chosen_server

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

    def submit_task(self, task: str, port: int = 80, ip: str = None):

        chosen_server = Server("UserSpecific", ip) if ip else self.choose_server()
        if chosen_server is None:
            logger.info(f"Failed to submit task, chosen server is None")
            return None
        task_added = TaskInfo(chosen_server, task, port)
        logger.info(f"Successfully submit task {task_added} to ThreadPool")

        return self.pool.submit(self.offload_task, task_added), chosen_server.serverIP

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

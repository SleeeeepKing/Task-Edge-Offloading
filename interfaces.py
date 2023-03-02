import abc

from loguru import logger


from config import Config, FlaskTestConfig, SmartContractConfig


# 这是一个抽象基类(Base Class)，需要子类实现其抽象方法来提供具体的接口实现。
#
# 在该基类中，定义了一个名为list_all_interfaces的抽象方法，但是并没有给出具体的实现。子类需要继承这个基类并实现它的所有抽象方法，否则子类也必须声明为抽象类。
class BaseInterfaces(abc.ABC):

    @abc.abstractmethod
    def list_all_interfaces(self):
        raise NotImplementedError("Interfaces must implement a printAllInterfaces method")


# 这段代码定义了一个继承自BaseInterfaces的类FlaskTestInterfaces，
# 它覆盖了BaseInterfaces中的list_all_interfaces方法。
# FlaskTestInterfaces的实例化时会默认使用FlaskTestConfig中的端口号。
class FlaskTestInterfaces(BaseInterfaces):
    default_port: int = FlaskTestConfig.port

    # list_all_interfaces方法输出了该类中的所有可调用函数的方法名。该方法使用Python的反射机制（dir和getattr）来实现。
    def list_all_interfaces(self):
        logger.info("Get all interfaces of class: FlaskTestInterfaces")
        method_list = [func for func in dir(FlaskTestInterfaces) if
                       callable(getattr(FlaskTestInterfaces, func)) and not func.startswith("__")]
        for method in method_list:
            print(method)

    # 这是FlaskTestInterfaces类中的三个静态方法：
    #
    # hello_world(): 返回字符串"hello"。
    # get_double(num): 将传入的数字num转换为字符串后返回"offloading/num"，
    # 这里似乎应该是要将num插入到字符串中，即返回字符串"offloading/3"或"offloading/5"之类的。
    # get_server(): 返回字符串"getserverlists"。
    @staticmethod
    def hello_world():
        return f"hello"

    @staticmethod
    def get_double(num):
        return f"offloading/{num}"

    @staticmethod
    def get_server():
        return f"getserverlists"

# 这段代码是定义了一个名为BDInterfaces的类，该类继承了BaseInterfaces类，因此实现了list_all_interfaces()方法。
# 在该类中还定义了两个静态变量：default_port和url_prefix。
class BDInterfaces(BaseInterfaces):
    default_port: int = SmartContractConfig.port
    url_prefix: str = "SCIDE/"

    # list_all_interfaces()方法的实现打印该类中的所有可调用方法。可调用方法的定义是函数对象可以调用，即该函数对象是一个函数或方法。
    # 通过内置的dir()函数获取类中所有属性的列表，然后对每个属性进行判断：如果该属性是可调用的并且不是魔术方法（以“__”开头），则打印该属性名。
    # 这样就可以得到BDInterfaces类中所有可调用的方法名。
    def list_all_interfaces(self):
        logger.info("Get all interfaces of class: BDInterfaces")
        method_list = [func for func in dir(BDInterfaces) if
                       callable(getattr(BDInterfaces, func)) and not func.startswith("__")]
        for method in method_list:
            print(method)

    # 这个类是用于与区块链相关的接口，其中定义了默认端口以及url前缀。
    # 此类中也实现了 list_all_interfaces 方法，可以打印出该类中所有的静态方法。
    #
    # 其中 ping_pong 方法返回一个执行 ping 操作的url，list_CProcess 方法返回当前运行中的智能合约进程列表，
    # hello_world 方法返回该类的url前缀。
    @staticmethod
    def ping_pong():
        return BDInterfaces.url_prefix + "SCManager?action=ping"

    @staticmethod
    def list_CProcess():
        return BDInterfaces.url_prefix + "SCManager?action=listContractProcess"

    @staticmethod
    def hello_world():
        return BDInterfaces.url_prefix

    # 这是一个静态方法 execute_contract，接受四个参数：
    #
    # contractID：合约的ID
    # operation：操作的名称
    # arg：操作的参数
    # request_id：请求的ID
    # 根据这些参数，返回一个URL，用于执行指定合约的指定操作，并传递给操作的参数。如果arg或request_id未指定，则相应的参数将不包括在URL中。
    @staticmethod
    def execute_contract(*, contractID: str, operation: str, arg: str = None, request_id: str = None):
        if arg:
            return BDInterfaces.url_prefix + f"SCManager?action=executeContract&contractID={contractID}&" \
                                             f"operation={operation}&arg={arg}&requestID={request_id}"
        else:
            return BDInterfaces.url_prefix + f"SCManager?action=executeContract&contractID={contractID}&" \
                                             f"operation={operation}"

    def interfaces2(self):
        pass

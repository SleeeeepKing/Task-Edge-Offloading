# 这段代码定义了一个名为 Config 的类，用于存储配置信息。其中，包括以下成员变量：
#
# server_list：一个字典，包含了服务器名称及其对应的 IP 地址；
# decision_algorithm：一个字典，包含了不同的决策算法及其对应的名称；
# DEFAULT_THROUGHPUT_PERIOD：一个默认的吞吐量计算周期，以秒为单位；
# EXPECTED_THROUGHPUT：预期吞吐量，以任务每秒完成的数量为单位。
# 通过这个类，可以方便地管理整个应用的配置信息，包括服务器列表、决策算法等。
class Config:
    server_list = {
        "LocalDevice": "127.0.0.1",
        "vagrant-ubuntu": "192.168.56.2",
    }

    decision_algorithm = {
        "default": "select_random_server",
        "minimum_ping_delay": "select_min_ping_server",
    }

    DEFAULT_THROUGHPUT_PERIOD = 1

    EXPECTED_THROUGHPUT = 25

# 这段代码定义了一个名为 FlaskTestConfig 的类，它继承自 Config 类，所以包含了 Config 中定义的成员变量和方法，
# 并且可以对其中的成员变量进行重写。
#
# 在 FlaskTestConfig 中，重写了 server_list 和 port 两个成员变量。其中，server_list 表示服务器列表，
# 包含了三台服务器的名称及其对应的 IP 地址。port 表示应用监听的端口号，这里设置为 5000。通过重写这两个成员变量，可
# 以实现不同配置环境下的不同设置。
class FlaskTestConfig(Config):
    server_list = {
        "LocalDevice": "127.0.0.1",
        "vagrant-ubuntu1": "192.168.56.2",
        "vagrant-ubuntu2": "192.168.56.3",
    }

    port = 5000

# 这段代码定义了一个名为 SmartContractConfig 的类，它继承自 Config 类，所以也包含了 Config 中定义的成员变量和方法，
# 并且可以对其中的成员变量进行重写。
#
# 在 SmartContractConfig 中，重写了 offloadingFlag、server_list 和 port 三个成员变量。
# 其中，server_list 表示服务器列表，包含了两台服务器的名称及其对应的 IP 地址。port 表示应用监听的端口号，
# 这里设置为 18000。offloadingFlag 则是一个字典，用于标识某个智能合约是否需要进行卸载处理，其默认为空字典。
#
# 通过重写这三个成员变量，SmartContractConfig 可以实现自己特定的配置需求，这里包括定义特定的服务器列表、监听端口和处理某些智能合约的卸载标记。
class SmartContractConfig(Config):
    offloadingFlag = dict()

    server_list = {
        "ubuntu2004": "192.168.0.106",
        "manjaro": "192.168.0.102",
    }

    port = 18000

# 这段代码定义了一个 config 字典，它包含了三个键值对，分别对应了三个不同的配置类，这些配置类的作用是在不同的情况下使用不同的配置参数，
# 以满足不同的需求。
#
# 其中，键为 "default" 的值是 Config 类，它表示默认的配置类，如果没有特定的配置类被指定，
# 则使用这个默认的配置类；键为 "FlaskTestConfig" 的值是 FlaskTestConfig 类，它用于在测试 Flask 应用程序时使用；
# 键为 "SmartContractConfig" 的值是 SmartContractConfig 类，它是专门用于智能合约卸载的配置类。
#
# 通过这种方式，我们可以方便地切换不同的配置类，而不需要手动修改配置参数，从而使得应用程序更加灵活、可配置化。
config = {
    "default": Config,
    "FlaskTestConfig": FlaskTestConfig,
    "SmartContractConfig": SmartContractConfig,
}

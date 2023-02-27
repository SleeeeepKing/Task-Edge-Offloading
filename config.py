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


class FlaskTestConfig(Config):
    server_list = {
        "LocalDevice": "127.0.0.1",
        "vagrant-ubuntu1": "192.168.56.2",
        "vagrant-ubuntu2": "192.168.56.3",
    }

    port = 5000


class SmartContractConfig(Config):
    offloadingFlag = dict()

    server_list = {
        "ubuntu2004": "192.168.0.106",
        "manjaro": "192.168.0.102",
    }

    port = 18000


config = {
    "default": Config,
    "FlaskTestConfig": FlaskTestConfig,
    "SmartContractConfig": SmartContractConfig,
}

import time

from flask import Flask, jsonify, request
from loguru import logger

from engine import DecisionEngine, TaskInfo
from server import ServerList, BDContractServerList
from interfaces import BDInterfaces


# 这段代码创建了一个 Flask 应用程序实例，命名为 app。接下来创建了一个 BDContractServerList 的实例，
# 存储在 server_list 变量中，该实例用于存储可用的服务器列表。然后，创建了一个 DecisionEngine 的实例 de，
# 并将其初始化为使用 minimum_ping_delay 决策算法进行任务决策。server_list 参数是可用的服务器列表，max_workers 参数指定最大工作线程数，
# consider_throughput 参数是一个布尔值，指定是否应考虑吞吐量来选择服务器。
app = Flask(__name__)
server_list = BDContractServerList()
de = DecisionEngine(decision_algorithm="minimum_ping_delay",
                    server_list=server_list,
                    max_workers=20,
                    consider_throughput=True)


# 这段代码定义了一个错误处理程序，用于处理在应用程序中遇到的所有 404 错误。如果应用程序处理过程中遇到 404 错误，
# 则调用 resource_not_found 函数，该函数返回 JSON 响应，包含错误信息和 HTTP 状态码。
# 然后，使用 app.register_error_handler() 函数将这个错误处理程序注册到 Flask 应用程序中。
# 这意味着当应用程序遇到 404 错误时，将自动调用该函数。
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error="404 Not Found"), 404

# 这段代码用于将之前定义的 resource_not_found 函数注册为 Flask 应用程序的 404 错误处理程序。
# 这意味着如果应用程序处理过程中遇到 404 错误，将会自动调用 resource_not_found 函数来处理该错误。
# 此函数返回一个包含错误信息和 HTTP 状态码的 JSON 响应。由于使用 app.errorhandler() 函数定义了该函数作为错误处理程序，
# 因此它只能处理应用程序中遇到的 404 错误。
app.register_error_handler(404, resource_not_found)

# 这个 ping_pong() 函数是一个 Flask 端点（endpoint），当用户访问 "/ping" 时，这个函数将被调用。
# 这个函数的作用是与 BDContracts 合约交互，调用 BDContracts 的 ping_pong() 函数，返回函数的执行结果。
#
# 在函数内部，首先使用日志记录器（logger）记录了函数被调用的信息。然后获取当前时间，调用 BDContracts 的 ping_pong() 函数，
# 并通过决策引擎（DecisionEngine）将任务提交给最优的服务器进行执行。
# 最后，解析执行结果并计算函数总共执行的时间（即从获取当前时间到得到任务执行结果的时间差）。
# 函数将执行结果和时间等信息通过 JSON 格式返回给用户。如果开启了 consider_throughput 选项，
# 则还会计算当前决策引擎的吞吐量（throughput）并返回。
@app.route("/ping")
def ping_pong():
    logger.info("Client interface ping_pong(route'/ping') has been called")
    st = time.time()
    task = BDInterfaces.ping_pong()
    ret, server = de.submit_task(task=task, port=BDInterfaces.default_port)
    data = ret.result().text
    total_time = time.time() - st
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time,
        throughput=de.cal_throughput(),
    )

# 这是一个Flask应用程序，它提供了一些接口，允许客户端与远程服务器进行通信和交互。在这个应用程序中，主要有以下几个接口：
#
# /ping：向服务器发送ping请求，并返回服务器的响应时间以及当前系统的吞吐量。
# /listcontractprocess：查询指定服务器上运行的所有智能合约进程列表。
# /getserverlists：获取服务器列表。
# /listservers：列出所有可用的服务器。
# /updateservers：从远程服务器列表更新本地服务器列表。
# 在应用程序中，还有一些配置类，用于配置服务器列表和决策算法。
# 应用程序使用 DecisionEngine 来选择最佳服务器。
# 同时，应用程序还注册了404错误处理程序，以处理访问不存在的接口的情况。
@app.route("/listcontractprocess")
def list_contract_process():
    """
    Call this interface for specific server:
        curl http://localhost:port/listcontractprocess?server=[serverIP]
    """
    logger.info(f"Client interface list_contract_process(url: {request.url}) has been called")
    st = time.time()
    server_ip = request.args.get("server")
    task = BDInterfaces.list_CProcess()
    ret, server = de.submit_task(task, port=BDInterfaces.default_port, ip=server_ip)
    data = ret.result().text
    total_time = time.time() - st
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time,
        throughput=de.cal_throughput(),
    )

# 这个函数是一个Flask的路由函数，当客户端发送HTTP请求到"/execcontract"时，就会调用该函数来处理请求。
# 这个接口的作用是执行一个智能合约。函数从HTTP请求中获取智能合约的ID、操作名、参数、请求ID和服务器IP地址等信息，
# 然后使用这些信息调用BDInterfaces中的execute_contract方法来执行智能合约。执行结果会被包装成一个JSON响应返回给客户端。
# 同时，这个函数还会计算请求的响应时间和吞吐量。
@app.route("/execcontract")
def execute_contract():
    """
    Call this interface:
        curl http://localhost:port/execcontract?contractID=[contractID]&operation=[operation] \
        &arg=[arg]&requestID=[requestID]&server=[serverIP]
    An example is :
        curl http://localhost:port/execcontract?contractID=-620602333&operation=main&arg=hhh
    """
    logger.info(f"Client interface execute_contract(url: {request.url}) has been called")
    st = time.time()
    contract_id = request.args.get("contractID")
    operation = request.args.get("operation")
    arg = request.args.get("arg")
    request_id = request.args.get("requestID")
    server_ip = request.args.get("server")
    task = BDInterfaces.execute_contract(contractID=contract_id, operation=operation, arg=arg, request_id=request_id)
    ret, server = de.submit_task(task, port=BDInterfaces.default_port, ip=server_ip)
    data = ret.result().text
    total_time = time.time() - st
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time,
        throughput=de.cal_throughput(),
    )

# 这个接口实现了一个简单的 hello world 方法，调用的是一个叫做 "Hello" 的智能合约的 "hello" 方法。可以通过以下方式调用：
#
# javascript
# Copy code
# curl http://127.0.0.1:port/hello?server=[serverIP]
# 其中，port 是客户端监听的端口号，serverIP 是智能合约运行的服务器 IP。
@app.route("/hello")
def hello_world():
    """
    Construct hello method on smart contract.

    An example is :
        curl http://127.0.0.1:8899/hello?server=[serverIP]
    """
    logger.info(f"Client interface hello(url: {request.url}) has been called")
    st = time.time()
    task = BDInterfaces.execute_contract(
        contractID="Hello",
        operation="hello",
        arg="hhh",
        request_id="123456",
    )
    server_ip = request.args.get("server")
    ret, server = de.submit_task(task, port=BDInterfaces.default_port, ip=server_ip)
    data = ret.result().text
    total_time = time.time() - st
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time,
        throughput=de.cal_throughput(),
    )

# 这个接口会返回当前服务器列表中的所有服务器IP地址。如果我们在浏览器或者用 curl 发送 GET 请求到该接口，
# 服务器会记录该请求，然后返回 JSON 格式的服务器 IP 列表。
@app.route("/listservers")
def list_servers():
    """
    List current servers in current server list.
    :return: example: {
        "data": [
            "127.0.0.1",
            "192.168.56.2"
        ]
    }
    """
    logger.info(f"Client interface list_servers(route'/listservers') has been called")
    return jsonify(data=de.server_list.convert_to_ip_list())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8899)

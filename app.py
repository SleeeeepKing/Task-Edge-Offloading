import json
import time

from flask import Flask, jsonify
from loguru import logger

from engine import DecisionEngine, TaskInfo
from server import ServerList, FlaskTestServerList
from interfaces import FlaskTestInterfaces

# 这段代码使用 Python 编写，主要作用是创建一个基于 Flask 框架的 Web 应用程序，并初始化一些变量。
#
# 具体来说，代码中的第一行创建了一个名为 app 的 Flask 应用程序实例，用于处理客户端请求和生成响应。
# __name__ 参数表示应用程序的名称，通常是当前 Python 模块的名称。
#
# 第二行创建了一个名为 server_list 的 FlaskTestServerList 实例，该实例用于存储应用程序需要使用的服务器列表。
#
# 第三行创建了一个名为 de 的 DecisionEngine 实例，该实例用于决策应用程序在哪个服务器上运行。
# 其中，decision_algorithm 参数设置了决策算法的类型，这里使用了 "minimum_ping_delay"（最小延迟）算法。
# server_list 参数指定了 DecisionEngine 实例使用的服务器列表。max_workers 参数设置了 DecisionEngine 实例中最大的工作线程数。
# consider_throughput 参数用于指定是否将服务器吞吐量考虑在内。
app = Flask(__name__)
server_list = FlaskTestServerList()

de = DecisionEngine(
    decision_algorithm="minimum_ping_delay",
    server_list=server_list,
    max_workers=20,
    consider_throughput=True
)

# 这段代码定义了 Flask 应用程序的路由和错误处理函数。
#
# 首先，代码中使用 @app.errorhandler(404) 装饰器定义了当客户端请求一个不存在的路由时的处理函数，
# 即 resource_not_found 函数。该函数返回一个包含错误信息的 JSON 格式的响应，HTTP 状态码为 404。
#
# 接下来，使用 app.register_error_handler(404, resource_not_found) 注册了 404 错误处理函数，
# 当客户端请求的路由不存在时会自动调用该函数。
#
# 然后，使用 @app.route("/") 装饰器定义了应用程序的根路由，即 /。该路由对应的处理函数为 hello_world。
# 该函数使用了 FlaskTestInterfaces 类的 hello_world 方法获取数据，然后使用 de.submit_task 方法将任务提交给决策引擎 de 进行处理。
# 该方法返回一个元组，其中第一个元素为异步处理结果，第二个元素为被选中的服务器对象。
#
# 在处理完任务后，该函数计算任务的总时间，并返回一个 JSON 格式的响应，其中包含了获取的数据、处理数据的服务器、HTTP 状态码、任务的总时间
# 以及通过调用 de.cal_throughput() 方法计算得出的服务器吞吐量。
# 同时，在函数中还记录了日志，用于输出当前客户端请求的信息。
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error="404 Not Found"), 404


app.register_error_handler(404, resource_not_found)

# 在上面
@app.route("/")
def hello_world():
    logger.info("Client interface hello_world(route'/') has been called")
    # offloading start time
    st = time.time()
    task = FlaskTestInterfaces.hello_world()
    ret, server = de.submit_task(task=task, port=FlaskTestInterfaces.default_port)
    data = ret.result().text
    # get the result from offloading task, then calculate total time
    total_time = time.time() - st
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time,
        throughput=de.cal_throughput(),
    )


# 这段代码定义了一个名为 square 的路由，即 /square/<num>，对应的处理函数为 square。
@app.route("/square/<num>")
def square(num):
    logger.info(
        f"Client interface square(route'/square/<num>') has been called with param {num}"
    )
    st = time.time()
    task = FlaskTestInterfaces.get_double(num)
    ret, server = de.submit_task(task=task, port=FlaskTestInterfaces.default_port)
    data = ret.result().text
    total_time = time.time() - st
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time,
        throughput=de.cal_throughput(),
    )


# 这段代码定义了一个名为 get_server_lists 的路由，即 /getserverlists，对应的处理函数为 get_server_lists。
# 该函数会向决策引擎提交一个 FlaskTestInterfaces 类的 get_server() 方法，获取当前服务器列表。
# 提交任务后，函数会等待异步任务完成，计算总时间，并返回服务器列表信息和一些其他信息的 JSON 格式响应。
#
# 在函数中，首先记录了日志，输出当前客户端请求的信息。接下来，使用 time.time() 获取当前时间作为任务开始时间 st。
# 然后，使用 de.submit_task 方法将任务提交给决策引擎，该方法会返回一个元组，其中第一个元素为异步处理结果，第二个元素为被选中的服务器对象。
#
# 等待任务完成后，使用 ret.result().text 获取任务处理结果的文本形式，然后使用 json.loads() 将结果转换为 Python 对象。
# 最后，将服务器列表等信息构造成 JSON 格式的响应返回给客户端。同时，在函数中还计算了任务总时间，用于记录处理该请求所需的总时间。
@app.route("/getserverlists")
def get_server_lists():
    logger.info(
        "Client interface getserverlists(route'/getserverlists') has been called"
    )
    st = time.time()
    task = FlaskTestInterfaces.get_server()
    ret, server = de.submit_task(task, port=FlaskTestInterfaces.default_port)
    data = ret.result().text
    total_time = time.time() - st
    data = json.loads(data)["data"]
    return jsonify(
        data=data, server=server, status_code=ret.result().status_code, time=total_time
    )


# 这段代码定义了一个名为 list_servers 的路由，即 /listservers，对应的处理函数为 list_servers。
# 该函数会返回决策引擎 de 中的服务器列表信息。
#
# 在函数中，首先记录了日志，输出当前客户端请求的信息。
# 然后，调用 de.server_list.convert_to_ip_list() 方法将服务器列表转换为 IP 地址列表，并将其构造成 JSON 格式的响应返回给客户端。
@app.route("/listservers")
def list_servers():
    logger.info(f"Client interface list_servers(route'/listservers') has been called")
    return jsonify(data=de.server_list.convert_to_ip_list())


# 这段代码定义了一个名为 update_servers_from_remote 的路由，即 /updateservers，
# 对应的处理函数为 update_servers_from_remote。该函数会向决策引擎提交一个 FlaskTestInterfaces 类的 get_server() 方法，
# 获取最新的服务器列表信息。然后，将这个列表更新到决策引擎的服务器列表中。
#
# 在函数中，首先记录了日志，输出当前客户端请求的信息。接下来，使用 time.time() 获取当前时间作为任务开始时间 st。
# 然后，使用 de.submit_task 方法将任务提交给决策引擎，该方法会返回一个元组，其中第一个元素为异步处理结果，第二个元素为被选中的服务器对象。
#
# 等待任务完成后，使用 ret.result().text 获取任务处理结果的文本形式，然后使用 json.loads() 将结果转换为 Python 对象。
# 接着，调用 de.server_list.update_server_list_using_list() 方法将获取到的服务器列表更新到决策引擎的服务器列表中。
# 最后，将服务器列表等信息构造成 JSON 格式的响应返回给客户端。同时，在函数中还计算了任务总时间，用于记录处理该请求所需的总时间。
@app.route("/updateservers")
def update_servers_from_remote():
    logger.info(f"Starting update local servers from remote server lists")
    st = time.time()
    task = FlaskTestInterfaces.get_server()
    ret, server = de.submit_task(task, port=FlaskTestInterfaces.default_port)
    data = ret.result().text
    total_time = time.time() - st
    ret_json = json.loads(data)
    de.server_list.update_server_list_using_list(ret_json["data"])
    return jsonify(
        data=de.server_list.convert_to_ip_list(), server=server, time=total_time
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8899)

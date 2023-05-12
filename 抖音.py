# -*- encoding=utf8 -*-

import socket

import yaml
import logging
import random
import signal

from airtest.core.api import *
from multiprocessing import Process
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

logging.getLogger("airtest").setLevel(logging.ERROR)
logging.getLogger("poco").setLevel(logging.ERROR)
logging.getLogger("adb").setLevel(logging.ERROR)
global devices, go_live_room, api_server_process
devices = {}
go_live_room = False
api_server_process = Process()
douYinAppID = "com.ss.android.ugc.aweme"
auto_setup(__file__)


def init_douyin():
    # 停止抖音
    stop_app(douYinAppID)
    print("设备{}: 启动抖音".format(num))
    start_app(douYinAppID)

    for _ in range(5):
        # 个人信息保护指引
        if poco(text="个人信息保护指引").exists():
            poco(text="同意").click()
            print("设备{}: 个人信息保护指引 -> 同意".format(num))
        if poco(text="允许抖音获取此设备的位置信息吗？").exists():
            poco(text="不允许").click()
            print("设备{} 获取此设备的位置信息 -> 不允许".format(num))
        if poco(text="允许“抖音”拨打电话和管理通话吗？").exists():
            poco(text="不允许").click()
            print("设备{} 拨打电话和管理通话 -> 不允许".format(num))
        # TODO 青少年模式
        if poco(text="青少年模式").exists():
            poco(text="我知道了").click()
            print("设备{} 青少年模式 -> 我知道了".format(num))
        if poco(text="抖音登录").exists():
            poco(desc="关闭，按钮").click()
        poco.swipe([0.52, 0.62], [0.42, 0.12], duration=0.7)

    # 提示登录账号
    # def login():
    #     sleep(1)
    #     poco(text="密码登录").click()
    #     sleep(1)
    #     poco(text="请输入手机号").click()
    #     poco(text="请输入手机号").set_text("18888888888")
    #     poco(text="请输入密码").click()
    #     poco(text="请输入密码").set_text("18888888888")
    #     # 用户协议 勾选
    #     poco("com.ss.android.ugc.aweme:id/o7g").click()
    #     poco(text="登录").click()
    #     if poco(text="系统繁忙，请稍后再试").exists():
    #         print("系统繁忙，请稍后再试")

    # if poco(text="抖音登录").exists():
    #     poco(text="立即登录").click()
    #     login()
    # if poco(text="我", desc="我，按钮"):
    #     poco(text="我", desc="我，按钮").click()
    #     login()
    watch_time = random.randint(1800, 3000)
    print("设备{} 看{}分钟".format(num, round(watch_time / 60), 2))
    for i in range(watch_time):  # 看30-50 分钟休息一会
        if poco(name="com.ss.android.ugc.aweme:id/ct").exists():
            print("设备{}: 视频底部加载动画".format(num))  # TODO 这里 有一个视频底部加载动画，需要注意
            return
        wait_time = random.randint(5, 10)
        poco.swipe([0.52, 0.62], [0.42, 0.12], duration=0.7)
        video_user_name = poco(name="com.ss.android.ugc.aweme:id/user_avatar")
        '''
        姓名:
            过滤:
                剧,剧场
            停留:
                美女,穿搭,变装,兄弟,跳舞,舞蹈,御姐,女人味,身材,美腿,美臀,美胸,裙,喜欢,实名观看,可以吗,心动,心动推荐
        '''
        if video_user_name.exists():
            video_user_name = video_user_name.attr("desc")
        else:
            video_user_name = "未知"
        video_desc = poco(name="com.ss.android.ugc.aweme:id/desc")
        if video_desc.exists():
            video_desc = video_desc.attr("text")
        else:
            video_desc = "未知"
        # guan_zhu_bottom = poco(name="com.ss.android.ugc.aweme:id/f9j", desc="关注")
        # if guan_zhu_bottom.exists():
        #     print("设备{}: 用户名: {} {}".format(num, user_name, "未关注"))
        # else:
        #     print("设备{}: 用户名: {} {}".format(num, user_name, "已关注"))
        #     wait_time = 10  # 自己人多看一会
        print("设备{}: 描述: {} 用户名: {} 观看{}秒".format(num, video_desc, video_user_name, wait_time))
        sleep(wait_time)
    sleep_time = random.randint(2000, 6000)
    print("设备{}: 看完了，休息{}分钟".format(num, round(sleep_time / 60), 2))
    sleep(sleep_time)  # 休息一会


def live_room():
    print("设备{} 进入直播间".format(num))
    handler(signal.SIGTERM, None)


def handler(signum, frame):
    for n in devices:
        os.kill(devices[n]["process"].pid, signal.SIGUSR1)
        sleep(1)
        devices[n]["process"].terminate()
        devices[n]["process"].join()
    # 关闭 API服务
    api_server_process.terminate()
    api_server_process.join()
    print("程序退出")
    os.kill(os.getpid(), signal.SIGTERM)


def handler_sub_process(signum, frame):
    print("设备{}: 子线程退出".format(num))
    stop_app(douYinAppID)


def douyin_sub_process(id, ipaddress, port):
    global poco, times, num
    times = 0
    num = id
    device_info = "android:///{}:{}".format(ipaddress, port)
    print("设备{}: 连接设备 {}".format(num, device_info))
    connect_device(device_info)
    poco = AndroidUiautomationPoco(use_airtest_input=True, screenshot_each_action=False)
    signal.signal(signal.SIGUSR1, handler_sub_process)  # TODO 这你需要做异常拦截，防止子线程 崩溃
    # TODO 继续任务，不要浪费时间 重复观看
    while True:
        if go_live_room:
            live_room()
        else:
            init_douyin()


def api_server():
    # TODO go_live_room 全局共享变量
    host, port = '0.0.0.0', 9999
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((host, port))
    listen_socket.listen(1)
    print('服务启动中 端口: %s ...' % port)

    while True:
        client_connection, client_address = listen_socket.accept()
        try:
            url_path = client_connection.recv(1024).decode("utf-8").split("\r\n")[0].split(' ')[1]
        except UnicodeDecodeError:
            print("api_server UnicodeDecodeError")
            url_path = "Error"

        if url_path == '/api':
            client_connection.send(b"""HTTP/1.1 200 OK\n\n{"code": "200"}""")
            go_live_room = True  # 进入直播间信号 // TODO 修改外部变量
            print("接收到请求 -> 重启子进程, 即将进入直播间")
            print(devices, go_live_room)
            # TODO 此处的 devices 非 daemon 内部的 devices，即 daemon 内部的 devices 与 外部的 devices 不是同一个对象
            for n in devices:
                devices[n]["process"].terminate()
            sleep(1)
            for n in devices:
                devices[n]["process"].start()
        else:
            client_connection.send(b"""HTTP/1.1 404 NOT FOUND\n\n{"code": "404"}""")
        client_connection.close()


def daemon():
    global devices, api_server_process
    # os.system("adb kill-server > /dev/null 2>&1")
    # os.system("adb devices > /dev/null 2>&1")
    sleep(3)
    f = open('config.yaml', 'r')
    devices = yaml.load(f, Loader=yaml.FullLoader)

    # douyin_sub_process(0, devices[0]["ipaddress"], devices[0]["port"])
    # exit(0)
    for n in devices:
        devices[n]["process"] = Process(target=douyin_sub_process, args=(n, devices[n]["ipaddress"], devices[n]["port"]))
        devices[n]["process"].start()

    api_server_process = Process(target=api_server)
    api_server_process.start()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    daemon()

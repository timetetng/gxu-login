#!/usr/bin/env python3
"""单次 DrCOM Portal 认证；仅使用 Python 标准库与 curl。"""
import argparse
import getpass
import ipaddress
import json
import re
import subprocess
import sys
import urllib.parse


def parse_response(text):
    """解析 JSON 或固定回调 JSONP，不执行服务端代码。"""
    text = text.strip()
    if text.startswith("dr1003("):
        match = re.fullmatch(r"dr1003\((.*)\)\s*;?", text, re.S)
        if not match:
            raise ValueError("无效 JSONP")
        text = match[1]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("响应不是对象")
    return value


def make_query(username, password, operator, wan_ip):
    ipaddress.IPv4Address(wan_ip)
    account = username + ("@" + operator if operator else "")
    return urllib.parse.urlencode({
        "callback": "dr1003", "login_method": "1",
        "user_account": account, "user_password": password,
        "wlan_user_ip": wan_ip, "wlan_user_ipv6": "",
        "wlan_user_mac": "000000000000", "wlan_ac_ip": "",
        "wlan_ac_name": "", "jsVersion": "4.2.1", "terminal_type": "1",
        "lang": "zh-cn",
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", required=True, help="认证请求实际经过的接口")
    parser.add_argument("--wan-ip", required=True, help="待认证设备的校园网 WAN IPv4")
    parser.add_argument("--operator", choices=["campus", "cmcc", "unicom", "telecom"], default="campus")
    parser.add_argument("--username", help="不提供则交互输入")
    parser.add_argument("--allow-http", action="store_true", help="确认接受学校 HTTP 明文认证")
    args = parser.parse_args()
    if not args.allow_http:
        parser.error("学校接口使用 HTTP，凭据在校内链路明文传输；确认后加 --allow-http")
    if not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,64}", args.interface):
        parser.error("接口名无效")
    try:
        ipaddress.IPv4Address(args.wan_ip)
        username = args.username or input("校园网账号: ").strip()
        if not username or "@" in username:
            parser.error("请输入不含运营商后缀的账号")
        password = getpass.getpass("校园网密码: ")
        if not password:
            parser.error("密码不能为空")
        query = make_query(username, password, "" if args.operator == "campus" else args.operator, args.wan_ip)
        # 完整 URL 通过标准输入交给 curl，避免密码进入进程参数。
        url = "http://172.17.0.2:801/eportal/portal/login?" + query
        config = 'url = "' + url + '"\n'
        result = subprocess.run([
            "curl", "--disable", "--config", "-", "--silent", "--fail",
            "--noproxy", "*", "--interface", "if!" + args.interface,
            "--proto", "=http", "--connect-timeout", "5", "--max-time", "15",
            "--max-filesize", "65536",
        ], input=config, text=True, capture_output=True, timeout=20, check=False)
        if result.returncode:
            print("认证请求失败；请检查接口、路由和学校服务（不输出含凭据的诊断）。", file=sys.stderr)
            return 1
        response = parse_response(result.stdout)
        # 不回显原始响应：服务端可能在其中包含账号等信息。
        if response.get("result") in (1, "1"):
            print("认证服务器报告成功；本脚本不探测公网连通性。")
            return 0
        print("认证服务器未报告成功；请核对账号、密码、运营商、余额及 WAN IP。", file=sys.stderr)
        return 1
    except (ValueError, OSError, subprocess.TimeoutExpired):
        print("请求或响应处理失败；未输出原始请求与响应。", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())

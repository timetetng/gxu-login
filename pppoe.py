#!/usr/bin/env python3
"""单次启动使用者已配置好的 NetworkManager PPPoE 连接。"""
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("uuid", help="已有 PPPoE 连接的 UUID（不是连接名）")
    args = parser.parse_args()
    import uuid
    try:
        connection = str(uuid.UUID(args.uuid))
    except ValueError:
        parser.error("需要有效的连接 UUID")
    try:
        result = subprocess.run(
            ["nmcli", "-g", "connection.type", "connection", "show", "uuid", connection],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if result.returncode or result.stdout.strip() != "pppoe":
            print("指定连接不存在或不是 PPPoE；未发起拨号。", file=sys.stderr)
            return 1
        # 凭据由 NetworkManager 保存或交互询问，不由脚本处理。
        return subprocess.run(
            ["nmcli", "--ask", "--wait", "45", "connection", "up", "uuid", connection],
            timeout=120, check=False,
        ).returncode
    except (OSError, subprocess.TimeoutExpired):
        print("无法完成拨号命令；请检查 NetworkManager、权限和连接状态。", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已取消等待；连接状态请通过 NetworkManager 确认。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())

# GXU Login

GXU 校园网登录与运营商 PPPoE 拨号脚本。

- **2023 年后运营商套餐**：默认采用 PPPoE 接入，使用 `pppoe.py`。
- **校园网及旧运营商套餐代拨**：使用 `campus.py`。校园网账号连接校园网；2023 年前办理、尚未到期的运营商套餐仍可按运营商参数代拨。

两个脚本均执行一次操作，不包含网络配置、自动重连或定时保活。

## 依赖

Linux、Python 3.10+。

- 校园网认证：curl 8.9+。
- PPPoE：NetworkManager、nmcli。

无需安装 Python 第三方库。

## 运营商 PPPoE 拨号

### 创建拨号连接

账号、密码由运营商办理套餐时提供。以电信为例，电信账号以 `yz777` 开头，**PPPoE 服务名（service name）填写 `dx`**。本机连接名可自行指定，下面用 `campus-telecom`。

先查看网卡名称，找到接运营商线路的有线网卡：

```sh
nmcli device status
```

以下以电信、网卡 `eth0` 为例创建连接。将网卡和账号替换为自己的实际值：

```sh
sudo nmcli connection add type pppoe ifname eth0 con-name campus-telecom pppoe.service dx username 'YOUR_TELECOM_ACCOUNT' connection.autoconnect no
```

这里 `pppoe.service dx` 指定电信服务名，`con-name campus-telecom` 只是本机连接名；账号填写运营商提供的完整 `yz777…` 账号。关闭自动连接，仅在手动执行时拨号。

### 拨号

直接使用 NetworkManager 拨号：

```sh
nmcli --ask connection up id campus-telecom
```

按提示输入运营商密码及所需授权，即可发起 PPPoE 拨号。也可以在系统网络设置或 `nm-connection-editor` 中编辑 `campus-telecom` 并保存密码，之后不用每次输入。

移动、联通的服务名、账号和密码按运营商提供的信息填写。

### 使用脚本拨号

`pppoe.py` 是已有连接的单次拨号入口，不负责创建连接；实际 PPPoE 拨号由 NetworkManager 完成。

查看连接 UUID：

```sh
nmcli -f NAME,UUID,TYPE connection show
```

找到类型为 `pppoe` 的连接，将 UUID 传给脚本：

```sh
python3 pppoe.py YOUR_CONNECTION_UUID
```

需要密码或授权时，按终端提示输入。连接配置及重连策略由 NetworkManager 管理。

## 校园网认证代拨

先连接校园有线网络或校园 Wi-Fi，准备：

- 请求实际经过的网卡名称。
- 待认证设备的校园网 WAN IPv4：直连填本机校园网地址；经路由器代拨填路由器 WAN 地址，不填内网 LAN 地址。

执行：

```sh
python3 campus.py --interface eth0 --wan-ip YOUR_WAN_IP --allow-http
```

将 `eth0` 和 `YOUR_WAN_IP` 替换为实际值，随后输入账号、密码。账号不带运营商后缀，由 `--operator` 自动添加：

| 接入类型 | 参数 | 账号后缀 |
| --- | --- | --- |
| 校园网 | `--operator campus`（默认） | 无 |
| 移动旧套餐 | `--operator cmcc` | `@cmcc` |
| 联通旧套餐 | `--operator unicom` | `@unicom` |
| 电信旧套餐 | `--operator telecom` | `@telecom` |

例如，电信旧套餐代拨：

```sh
python3 campus.py --interface eth0 --wan-ip YOUR_WAN_IP --operator telecom --allow-http
```

学校认证接口使用明文 HTTP，因此需要 `--allow-http` 确认。运营商代拨适用于 2023 年前办理且尚未到期的旧套餐；新套餐使用上面的 PPPoE 方式。

认证地址为 `172.17.0.2:801`。如与 Docker、VPN 网段冲突，请自行处理路由。脚本显示成功表示认证服务器已接受请求。

## 测试

```sh
python3 -m unittest -v
```

测试不发送认证请求，也不实际拨号。

## 许可证

MIT，见 [LICENSE](LICENSE)。

# Rapoo MT760 双 2.4G 接收器切换工具

> 在 Linux 与 Windows 两台电脑之间自由切换雷柏 MT760 鼠标 —— 一条命令、一个热键、或鼠标上的自定义按键。
> 无需雷柏官方软件（雷柏没有 Linux 版），全程免 sudo。

## 功能特性

- **双向切换**：Linux ⇄ Windows，鼠标在 2.4G 信道之间**瞬间**切换
- **免 sudo**：通过 udev 规则，普通用户即可直接操作接收器
- **三种触发方式**：
  - 命令行：`./switch.sh 2`
  - 双侧热键：`Ctrl+Pause`（键盘）
  - 鼠标自定义键（实测鼠标宏发送的是 `Ctrl+Break`，本项目已兼容）
- **可选项**：`edge-switch.py` 光标顶住屏幕边缘自动切换（不是原博客方案，按需使用）
- **零第三方依赖**：Linux 端仅需仓库自带的 `hidapitester` 二进制 + Python 标准库

## 原理

雷柏 MT760 附带**两个 2.4G USB 接收器**：各插一台电脑，鼠标通过切换信道决定连接哪台。官方切换依赖雷柏 Windows 管理软件，而雷柏**没有 Linux 版**，Linux 用户无法切换。

本项目逆向复刻自 [phreer 的博客](https://phreer.github.io/2024/08/11/mouse-switcher-rapoo.html)：

1. 用 Wireshark 抓包官方软件的切换命令
2. 发现它是一条 **32 字节的 HID output report**，**第 8 字节就是目标信道 ID**
3. 用 [hidapitester](https://github.com/todbot/hidapitester/) 直接发送，无需解绑驱动、无需官方软件

| 关键参数 | 值 |
|---|---|
| VID:PID | `24ae:1870`（雷柏 MT760） |
| 跨平台 usage | `usagePage 0xff00 / usage 0x0e` |
| report 长度 | 32 字节，第 8 字节 = 目标信道 |
| 实测信道 | `1` = Linux 接收器，`2` = Windows 接收器 |

> `usagePage 0xff00`（厂商自定义区间）是**跨平台的关键**：Linux 上几乎任意 usage 都能发，但 Windows 上只有厂商 usage 才与 report descriptor 匹配，`--usage 1` 会写入失败（`wrote -1 bytes`）。

## 目录结构

```
rapoo-switch/
├── switch.sh             # Linux 切换命令（核心）
├── hidapitester          # Linux 版工具（来自 todbot/hidapitester）
├── 42-rapoo.rules        # udev 规则：普通用户免 root 访问接收器
├── edge-switch.py        # [可选] 光标顶住屏幕边缘自动切换
├── windows/
│   ├── hidapitester.exe        # Windows 版工具
│   ├── switch_to_linux.bat     # Windows 上切回 Linux 的命令
│   ├── switch_to_linux.vbs     # .bat 的隐藏窗口包装（不弹黑框）
│   ├── switch_back_to_linux.ahk# AutoHotkey v2 热键脚本
│   └── README.txt              # Windows 侧安装/调试说明
├── README.md
└── LICENSE
```

## 安装

### Linux

```bash
# 1. 安装 udev 规则（让普通用户免 root 操作接收器）
sudo cp 42-rapoo.rules /usr/lib/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
# 若权限仍未生效，拔插一次接收器

# 2. 验证普通用户可访问（应能列出设备而非权限错误）
./hidapitester --vidpid 24ae:1870 --list-detail

# 3. 测试切换（信道 2 = Windows 接收器，按你的实测调整）
./switch.sh 2
```

> `switch.sh` 默认使用仓库内的 `hidapitester`；也可装到 `~/.local/bin` 或通过环境变量 `HIDAPITESTER` 指定。

### Windows

1. 安装 [AutoHotkey v2](https://www.autohotkey.com/)
2. 把 `windows/` 整个文件夹拷到 Windows 机器
3. 双击 `switch_to_linux.bat` 手动验证（鼠标应切回 Linux）
4. 双击 `switch_back_to_linux.ahk` 启用热键（托盘出现绿色 H 图标，可加入开机自启）

## 使用

```bash
./switch.sh 1     # 切到信道 1（Linux 接收器）
./switch.sh 2     # 切到信道 2（Windows 接收器）
```

**信道号需要自行实测**：逐个试 `0 / 1 / 2 / 3`，切走后鼠标出现在另一台电脑的那个号就是对的。切走后当前电脑会暂时失去鼠标，属正常现象。

## 双侧热键 `Ctrl+Pause`

两台机器用**同一个组合键**，各自执行"切到对面"：

| 侧 | 绑定方式 | 动作 |
|---|---|---|
| Linux | GNOME 自定义快捷键 `<Control>Pause` → `switch.sh 2` | 切去 Windows |
| Windows | AutoHotkey `^Pause` + `^sc146` + `^vk03` → `switch_to_linux.vbs` | 切回 Linux |

**为什么 Windows 端绑了三个键**：实测鼠标自定义键（经雷柏驱动宏注入）在 Windows 上发的是 `Ctrl+Break`（按下 VK 03 / 扫描码 146，松开才变成 Pause），而不是标准的 `Ctrl+Pause`。物理键盘发标准 Pause（VK 13），故 `^Pause` 抓键盘、`^sc146`/`^vk03` 抓鼠标宏，三路都要。

**为什么不用 `Super+` 组合**：Linux GNOME (X11) 上 `Super` 单键被 shell 抓去开"活动概览"，任何 `Super` 组合键都会被 shell 先拦截，自定义快捷键触发不了。`Ctrl+Pause` 在 Linux GNOME X11 与 Windows 上都无默认占用、可可靠触发。

## 可选：屏幕边缘自动切换

`edge-switch.py` 模拟官方软件的"鼠标移到屏幕边缘即切换"（原博客未做此功能）：

```bash
python3 edge-switch.py --dry-run   # 只检测不切换（先验证）
python3 edge-switch.py             # 运行
```

用 `--debug` 可查看详细日志；在脚本顶部 `CONFIG` 里配置各边缘对应的信道。

## FAQ

**Q: 没有 udev 规则时能工作吗？**
不行。`/dev/hidraw*` 默认 `root:root 600`，需要 udev 规则（`uaccess` + `plugdev` 组）授予普通用户读写。

**Q: Windows 上键盘 `Ctrl+Pause` 有效，鼠标自定义键无效？**
鼠标宏注入的是 `Ctrl+Break` 而非 `Ctrl+Pause`（Pause/Break 键在 Windows 上的著名怪癖：按下是 VK_CANCEL/SC 146，松开才变 VK_PAUSE）。请使用仓库内已包含 `^sc146` / `^vk03` 的 `switch_back_to_linux.ahk`。若仍无效，可在雷柏驱动里把该键改为发送 `Ctrl+F12`，并同步修改 AHK 与 Linux 的 gsettings。

**Q: 信道号怎么找？**
逐个试 `./switch.sh 0 / 1 / 2 / 3`，鼠标切到另一台电脑的那个号即目标。两台机器各有各的信道。

## 参考

- [phreer: Linux 上雷柏 MT760 鼠标 2.4G 接收器切换](https://phreer.github.io/2024/08/11/mouse-switcher-rapoo.html) —— 本项目方案的出处
- [todbot/hidapitester](https://github.com/todbot/hidapitester/) —— 发送 HID output report 的工具
- [marcelhoffs/input-switcher](https://github.com/marcelhoffs/input-switcher/) —— 罗技版同类方案，本项目参考其 .bat/.vbs/udev 模式
- [Who-T: Understanding HID report descriptors](https://who-t.blogspot.com/2018/12/understanding-hid-report-descriptors.html) —— HID 协议背景

## License

[MIT](LICENSE)

> 仓库中的 `hidapitester` / `hidapitester.exe` 为 [todbot/hidapitester](https://github.com/todbot/hidapitester/) 的预编译产物，版权归其作者所有。

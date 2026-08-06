# Rapoo MT760 双 2.4G 接收器切换工具

**[English](README.en.md) | 中文**

> 在 Linux 与 Windows 两台电脑之间自由切换雷柏 MT760 鼠标：一条命令、一个热键、或鼠标上的自定义按键。无需雷柏官方软件（它没有 Linux 版），部署完成后日常使用免 sudo。

---

## 目录

- [原理介绍](#原理介绍)
  - [问题背景](#问题背景)
  - [切换原理](#切换原理)
  - [关键参数](#关键参数)
  - [跨平台要点](#跨平台要点)
  - [热键方案的设计原理](#热键方案的设计原理)
  - [参考文献](#参考文献)
- [部署方式](#部署方式)
  - [系统环境](#系统环境)
  - [目录结构](#目录结构)
  - [Linux 部署](#linux-部署)
  - [Windows 部署](#windows-部署)
  - [键盘热键绑定](#键盘热键绑定)
  - [鼠标自定义键绑定（推荐）](#鼠标自定义键绑定推荐)
  - [使用命令](#使用命令)
  - [边缘自动切换（可选）](#边缘自动切换可选)
  - [常见问题 FAQ](#常见问题-faq)
- [License](#license)

---

## 原理介绍

### 问题背景

雷柏 MT760 附带**两个 2.4G USB 接收器**，设计上各插一台电脑，鼠标通过切换信道决定连接哪台。官方切换功能依赖雷柏 Windows 管理软件，而雷柏**没有 Linux 版**——这就是 Linux 用户无法切换鼠标连接设备的根源。

### 切换原理

本项目的做法是**逆向复刻官方软件的切换命令**：

1. 用 Wireshark 抓包官方软件的切换过程，发现 `URB_CONTROL out` 是一条 **32 字节的 HID output report**
2. 逐一对比数据包内容，确定 **第 8 字节就是目标信道 ID**
3. 用 [hidapitester](https://github.com/todbot/hidapitester/) 直接发送这条 report——无需解绑驱动，也无需官方软件

### 关键参数

| 参数 | 值 |
|---|---|
| VID:PID | `24ae:1870`（雷柏 MT760） |
| 跨平台 usage | `usagePage 0xff00 / usage 0x0e` |
| report 长度 | 32 字节 |
| 信道位置 | 第 8 字节（索引 7） |
| 实测信道 | `1` = Linux 接收器，`2` = Windows 接收器 |

### 跨平台要点

`usagePage 0xff00`（厂商自定义区间）是**跨平台工作的关键**：

- Linux 的 usbhid 驱动对 usage 校验宽松，几乎任意 usage 都能写入成功
- Windows 上 output report 必须与 report descriptor 匹配，`--usage 1` 会写入失败（`wrote -1 bytes`），只有厂商 usage `0xff00/0x0e` 在两边都可用

### 热键方案的设计原理

切换本身只需一条命令，但日常使用需要**随手可触发的入口**。本项目提供双侧热键 `Ctrl+Pause`：

| 触发入口 | 实际发送的内容 |
|---|---|
| Linux 物理键盘 `Ctrl+Pause` | 标准 Pause（VK 13） |
| Windows 物理键盘 `Ctrl+Pause` | 标准 Pause（VK 13） |
| Windows 鼠标自定义键（雷柏驱动宏） | **Ctrl+Break**（按下 VK 03 / 扫描码 146，松开才变 Pause） |

**为什么 Windows 端要绑三个热键（`^Pause` + `^sc146` + `^vk03`）**：实测鼠标宏在 Windows 上发送的是 `Ctrl+Break` 而非 `Ctrl+Pause`——这是 Windows 对 Pause/Break 键的著名怪癖（按下是 VK_CANCEL，松开才变 VK_PAUSE）。`^Pause` 抓物理键盘，`^sc146`/`^vk03` 抓鼠标宏，三路缺一不可。

**为什么不用 `Super+` 组合键**：Linux GNOME (X11) 上 `Super` 单键被 Shell 抓去打开"活动概览"，任何 `Super` 组合键都会被 Shell 先拦截，自定义快捷键无法触发。`Ctrl+Pause` 在 Linux GNOME X11 与 Windows 上都没有默认占用、可可靠触发。

### 参考文献

| 文献 | 对本项目的作用 |
|---|---|
| [phreer: Linux 上雷柏 MT760 鼠标 2.4G 接收器切换](https://phreer.github.io/2024/08/11/mouse-switcher-rapoo.html) | **方案出处**：抓包 → 定位 HID output report → hidapitester 发送 → udev 规则，全链路方法论 |
| [todbot/hidapitester](https://github.com/todbot/hidapitester/) | **发送工具**：向接收器写入 HID output report 的命令行工具，本项目依赖它 |
| [marcelhoffs/input-switcher](https://github.com/marcelhoffs/input-switcher/) | **跨平台模式参考**：.bat + .vbs 隐藏窗口包装、udev 规则、双侧同键位切换的做法 |
| [Who-T: Understanding HID report descriptors](https://who-t.blogspot.com/2018/12/understanding-hid-report-descriptors.html) | **协议背景**：理解 Usage / Usage Page、report descriptor，以及为何厂商 usage 区间跨系统有效 |

---

## 部署方式

### 系统环境

| 项目 | Linux | Windows |
|---|---|---|
| 操作系统 | 本方案实测于 Ubuntu 22.04 + GNOME **X11** 会话 | Windows 10 / 11 |
| 鼠标 | Rapoo MT760（VID `24ae:1870`），**两个 2.4G 接收器分别插两台电脑** | 同左 |
| 额外软件 | 无需安装（`hidapitester` 仓库自带；可选 `edge-switch.py` 需要 Python 3） | 需安装 [AutoHotkey v2](https://www.autohotkey.com/) |
| 权限要求 | 安装 udev 规则需要一次 `sudo` | 无需管理员 |

> ⚠️ Linux 建议使用 **X11** 会话。`Super` 组合键的冲突源于 GNOME X11 的 Shell 抓取；本项目已规避（改用 `Ctrl+Pause`），但整个方案按 X11 实测。

### 目录结构

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

### Linux 部署

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

> `switch.sh` 默认使用仓库内的 `hidapitester`；也可装到 `~/.local/bin`，或通过环境变量 `HIDAPITESTER` 指定路径。

### Windows 部署

1. 安装 [AutoHotkey v2](https://www.autohotkey.com/)
2. 把 `windows/` 整个文件夹拷到 Windows 机器
3. 双击 `switch_to_linux.bat` 手动验证（鼠标应切回 Linux）
4. 双击 `switch_back_to_linux.ahk` 启用热键（托盘出现绿色 H 图标，可加入开机自启）

### 键盘热键绑定

| 侧 | 绑定方式 | 动作 |
|---|---|---|
| Linux | GNOME 自定义快捷键：`<Control>Pause` → `bash /home/<user>/rapoo-switch/switch.sh 2` | 切去 Windows |
| Windows | AutoHotkey（`switch_back_to_linux.ahk`）：`^Pause` + `^sc146` + `^vk03` → `switch_to_linux.vbs` | 切回 Linux |

Linux 上在 设置 → 键盘 → 自定义快捷键 里配置；Windows 上运行 `.ahk` 后即生效。

### 鼠标自定义键绑定（推荐）

把鼠标上的自定义按键（如 DPI 键或侧键）绑成同一触发命令，实现"按一下鼠标键就切换"。**雷柏没有 Linux 软件，绑键只能在 Windows 的雷柏管理软件里做一次，宏写入鼠标板载内存后 Linux 侧同样生效。**

1. 在 Windows 上打开雷柏管理软件 → 按键自定义 / 宏设置
2. 选择鼠标自定义键，设为发送 **`Ctrl+Pause`**
3. 保存并写入鼠标（板载存储）
4. 之后两台机器上的行为：
   - 鼠标在 Linux 接收器上，按此键 → 切去 Windows
   - 鼠标在 Windows 接收器上，按此键 → 切回 Linux

> 注意：雷柏驱动宏在 Windows 上实际发送的是 `Ctrl+Break`（而非 `Ctrl+Pause`），这正是 `switch_back_to_linux.ahk` 里同时绑定 `^sc146` / `^vk03` 的原因——Windows 端已兼容，无需额外配置。

### 使用命令

```bash
./switch.sh 1     # 切到信道 1（Linux 接收器）
./switch.sh 2     # 切到信道 2（Windows 接收器）
```

**信道号需要自行实测**：逐个试 `0 / 1 / 2 / 3`，切走后鼠标出现在另一台电脑的那个号就是对的。切走后当前电脑会暂时失去鼠标，属正常现象。

### 边缘自动切换（可选）

`edge-switch.py` 模拟官方软件的"鼠标移到屏幕边缘即切换"（原博客未实现，本项目补充）：

```bash
python3 edge-switch.py --dry-run   # 只检测不切换（先验证）
python3 edge-switch.py             # 运行
```

用 `--debug` 可查看详细日志；在脚本顶部 `CONFIG` 里配置各边缘对应的信道。

### 常见问题 FAQ

**Q: 没有 udev 规则时能工作吗？**
不行。`/dev/hidraw*` 默认 `root:root 600`，需要 udev 规则（`uaccess` + `plugdev` 组）授予普通用户读写。

**Q: Windows 上键盘 `Ctrl+Pause` 有效，鼠标自定义键无效？**
鼠标宏注入的是 `Ctrl+Break` 而非 `Ctrl+Pause`（Pause/Break 键在 Windows 上的怪癖：按下是 VK_CANCEL / SC 146，松开才变 VK_PAUSE）。请使用仓库内已包含 `^sc146` / `^vk03` 的 `switch_back_to_linux.ahk`。若仍无效，可在雷柏驱动里把该键改为发送 `Ctrl+F12`，并同步修改 AHK 与 Linux 的 gsettings。

**Q: 信道号怎么找？**
逐个试 `./switch.sh 0 / 1 / 2 / 3`，鼠标切到另一台电脑的那个号即目标。

---

## License

[MIT](LICENSE)

> 仓库中的 `hidapitester` / `hidapitester.exe` 为 [todbot/hidapitester](https://github.com/todbot/hidapitester/) 的预编译产物，版权归其作者所有。

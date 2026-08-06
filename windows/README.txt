Rapoo MT760 Windows 侧切换工具
===============================

把这整个 windows 文件夹拷到 Windows 机器上（任意位置，建议放
C:\Users\<你>\rapoo-switch\ 之类，路径里别有中文/空格更省心）。

文件说明
--------
- hidapitester.exe         切信道的工具（Linux 侧同款）
- switch_to_linux.bat      发"信道 1"命令，把鼠标切回 Linux 那台电脑
- switch_to_linux.vbs      .bat 的隐藏窗口包装（不弹黑框）
- switch_back_to_linux.ahk AutoHotkey 脚本：绑定 Ctrl+Pause 热键

一次性设置（两步）
------------------
1. 安装 AutoHotkey v2：https://www.autohotkey.com/ （装好后重启桌面会话）
2. 双击 switch_back_to_linux.ahk 启动（托盘中会出现绿色 H 图标，常驻即可）

使用方法
--------
- 按 Ctrl+Pause（Ctrl + Pause/Break 键）=> 鼠标切回 Linux
- 验证：先双击运行 switch_to_linux.bat，鼠标立刻切走即成功；
  再按热键，应达到同样效果。

开机自启（可选）
----------------
把 switch_back_to_linux.ahk 的快捷方式放进：
  Win+R 输入 shell:startup  回车
然后把快捷方式拖入打开的文件夹即可。

调试提示
--------
- 若热键无反应：确认托盘有绿色 H 图标；右键图标可以 Reload。
- 鼠标自定义键实测（见 log.txt，AHK Key History 导出）：
  鼠标宏实际发的是 Ctrl+Break（按下 VK 03 / SC 146，松开才变 Pause）。
  脚本已绑定 ^Pause（物理键盘）+ ^sc146 + ^vk03（鼠标宏），Reload 后两路都识别。
- 若 Reload 后鼠标键仍不触发，重新导出 Key History 对比（AHK v2 路径：
  托盘右键 → Open → 脚本主窗口菜单 View → Key history）。
- 兜底方案：若 Pause 类键始终不识别，改雷柏驱动里该键发送 Ctrl+F12，
  并同步改 AHK 与 Linux 的 gsettings 为 Ctrl+F12。
- 若第一次运行 AHK 提示"脚本需要 AutoHotkey v2"，去装 v2 而不是 v1。
- 信道号：本文用的是 1（= Linux 接收器）。若你的两台机器信道映射不同，
  编辑 switch_to_linux.bat 里 8 号字节（0x01）为对应信道（0/2/3）。

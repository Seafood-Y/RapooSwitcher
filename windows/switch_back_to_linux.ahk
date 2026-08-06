#Requires AutoHotkey v2.0
; ============================================================
; Rapoo MT760 — 在 Windows 上把鼠标切回 Linux（信道 1）
; ------------------------------------------------------------
; 根据 Key History 实测（log.txt）：鼠标宏实际发送
;   LControl Down → CtrlBreak Down (VK 03 / SC 146) → LControl Up → Pause Up
; 触发键是 CtrlBreak，所以必须按扫描码 146 / 虚拟键码 03 绑定。
; 物理键盘 Ctrl+Pause 由 ^Pause 命中，鼠标宏由 ^sc146/^vk03 命中。
; 堆叠热键共享同一函数体（大括号写法）。
; Ctrl = ^
; 需安装 AutoHotkey v2: https://www.autohotkey.com/
; ============================================================
InstallKeybdHook()
KeyHistory(200)

^Pause::
^sc146::
^vk03::
{
    Run Format("{}\switch_to_linux.vbs", A_ScriptDir)
}

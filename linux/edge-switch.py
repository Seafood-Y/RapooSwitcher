#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapoo MT760 屏幕边缘自动切换守护脚本

当光标顶到屏幕边缘并持续顶住一小段时间(默认 0.4s)时，自动调用
同目录下的 switch.sh 切换到对应信道，把鼠标"甩"到另一台电脑的接收器上。
模拟了雷柏官方软件"鼠标移到屏幕边缘即切换"的行为。

实现说明: 通过 ctypes 直接调用系统自带的 libX11 (XQueryPointer) 轮询光标位置，
零第三方依赖，不需要 pip / 不需要 input 组权限。

用法:
    python3 edge-switch.py            # 前台运行
    python3 edge-switch.py --dry-run  # 只打印检测结果，不真正切换(先验证用)
    python3 edge-switch.py --debug    # 打印详细日志

配置见下方 CONFIG。信道号请先用 switch.sh 手动试出哪个对应哪台电脑。
"""
import argparse
import ctypes
import ctypes.util
import os
import subprocess
import sys
import time

# 本脚本所在目录（与 switch.sh 同目录，保证相对路径可移植）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    # 每个边缘对应的目标信道。不需要的边缘设为 None。
    "right_edge_channel": 1,   # 光标顶到右边缘 -> 切到信道 1
    "left_edge_channel": 0,    # 光标顶到左边缘 -> 切到信道 0
    "top_edge_channel": None,  # 顶部/底部默认不启用
    "bottom_edge_channel": None,
    # 光标需要在边缘"顶住"多久才触发(秒)。调大可减少误触(例如滑动条就在屏幕边缘)。
    "dwell_seconds": 0.4,
    # 轮询间隔(秒)。越小越灵敏。
    "poll_interval": 0.02,
    # 触发后的冷却时间(秒)，期间不再触发。
    "cooldown_seconds": 2.0,
    # 切换脚本路径（与 edge-switch.py 同目录下的 switch.sh）
    "switch_script": os.path.join(_SCRIPT_DIR, "switch.sh"),
}

# 边缘名 -> CONFIG 键
EDGE_ATTRS = {
    "right": "right_edge_channel",
    "left": "left_edge_channel",
    "top": "top_edge_channel",
    "bottom": "bottom_edge_channel",
}


class XPointer:
    """用 ctypes + libX11 查询指针位置，避免任何 pip 依赖。"""

    def __init__(self):
        lib = ctypes.util.find_library("X11") or "libX11.so.6"
        self.x11 = ctypes.CDLL(lib)

        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.disp = self.x11.XOpenDisplay(None)
        if not self.disp:
            raise RuntimeError("无法连接 X server（DISPLAY 未设置？）")

        self.x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        self.x11.XDefaultRootWindow.restype = ctypes.c_ulong
        self.root = self.x11.XDefaultRootWindow(self.disp)

        self.x11.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.x11.XDisplayWidth.restype = ctypes.c_int
        self.x11.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.x11.XDisplayHeight.restype = ctypes.c_int
        self.w = self.x11.XDisplayWidth(self.disp, 0)
        self.h = self.x11.XDisplayHeight(self.disp, 0)

        self.x11.XQueryPointer.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint),
        ]
        self.x11.XQueryPointer.restype = ctypes.c_int

    def position(self):
        root_r = ctypes.c_ulong()
        child_r = ctypes.c_ulong()
        rx = ctypes.c_int()
        ry = ctypes.c_int()
        wx = ctypes.c_int()
        wy = ctypes.c_int()
        mask = ctypes.c_uint()
        self.x11.XQueryPointer(self.disp, self.root,
                               ctypes.byref(root_r), ctypes.byref(child_r),
                               ctypes.byref(rx), ctypes.byref(ry),
                               ctypes.byref(wx), ctypes.byref(wy),
                               ctypes.byref(mask))
        return rx.value, ry.value


def main():
    ap = argparse.ArgumentParser(description="Rapoo 屏幕边缘自动切换")
    ap.add_argument("--dry-run", action="store_true", help="只检测不切换")
    ap.add_argument("--debug", action="store_true", help="打印详细日志")
    args = ap.parse_args()

    xp = XPointer()
    W, H = xp.w, xp.h

    if args.debug:
        print(f"屏幕尺寸: {W}x{H}", flush=True)

    def edge_of(x, y):
        """返回指针所在的边缘列表(角落可能同时命中两个)，或空列表"""
        edges = []
        if x >= W - 1:
            edges.append("right")
        if x <= 0:
            edges.append("left")
        if y >= H - 1:
            edges.append("bottom")
        if y <= 0:
            edges.append("top")
        return edges

    # 每个边缘累计"顶住"的时间；触发过之后等指针离开该边缘才允许再次触发
    dwell_timer = {e: 0.0 for e in EDGE_ATTRS}
    fired_at_edge = {e: False for e in EDGE_ATTRS}
    last_fire = 0.0

    def fire(edge):
        chan = CONFIG[EDGE_ATTRS[edge]]
        if chan is None:
            return False
        if args.dry_run:
            print(f"[dry-run] 顶住 {edge} 边缘 -> 本应执行: switch.sh {chan}",
                  flush=True)
            return True
        print(f"[switch] 光标顶住 {edge} 边缘 {CONFIG['dwell_seconds']}s"
              f" -> 切换到信道 {chan}", flush=True)
        try:
            subprocess.run([CONFIG["switch_script"], str(chan)], check=False)
        except FileNotFoundError:
            print(f"找不到 {CONFIG['switch_script']}", flush=True)
        return True

    print("边缘监听已启动。顶住屏幕边缘即切换，Ctrl+C 退出。", flush=True)
    try:
        while True:
            time.sleep(CONFIG["poll_interval"])
            x, y = xp.position()
            now = time.time()
            edges = edge_of(x, y)

            if args.debug and edges:
                print(f"[debug] x={x} y={y} edges={edges} "
                      f"dwell={dwell_timer}", flush=True)

            for e in EDGE_ATTRS:
                if e in edges:
                    if fired_at_edge[e]:
                        # 已触发过，等指针离开该边缘再复位，避免重复/来回弹跳
                        continue
                    dwell_timer[e] += CONFIG["poll_interval"]
                    if (dwell_timer[e] >= CONFIG["dwell_seconds"]
                            and now - last_fire >= CONFIG["cooldown_seconds"]):
                        if fire(e):
                            # 防止出现在角落时两个边缘同时触发
                            for e2 in edges:
                                fired_at_edge[e2] = True
                            last_fire = now
                else:
                    dwell_timer[e] = 0.0
                    fired_at_edge[e] = False
    except KeyboardInterrupt:
        print("\n已退出。", flush=True)
    except Exception as exc:  # 例如 X 连接断开
        print(f"异常退出: {exc}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

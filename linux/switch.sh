#!/usr/bin/env bash
# Rapoo MT760 双 2.4G 接收器信道切换
# 用法: ./switch.sh <信道号>      信道号通常试 0 / 1 / 2
# 原理: 向接收器发送一条 32 字节的 HID output report，
#       第 8 字节(索引7)就是要切换到的信道 ID。
# 参考: https://phreer.github.io/2024/08/11/mouse-switcher-rapoo.html
set -euo pipefail

VIDPID="24ae:1870"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 优先用仓库内自带的二进制；没有则退回 ~/.local/bin（可用环境变量 HIDAPITESTER 覆盖）
HIDAPITESTER="${HIDAPITESTER:-$SCRIPT_DIR/hidapitester}"
if [ ! -x "$HIDAPITESTER" ]; then
    HIDAPITESTER="$HOME/.local/bin/hidapitester"
fi

if [ $# -ne 1 ]; then
    echo "用法: $0 <信道号>" >&2
    echo "信道号: 通常为 0、1 或 2，逐个试即可" >&2
    exit 1
fi

CHANNEL="$1"

# 32 字节 HID output report，第 8 字节为信道 ID
DATA="0xba,0xa5,0xae,0x00,0x00,0x00,0x00,${CHANNEL},0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00"

echo "切换到信道 ${CHANNEL} ..."
"$HIDAPITESTER" --vidpid "${VIDPID}" --usagePage 0xff00 --usage 0x0e \
    --open -l 32 --send-output "${DATA}"
echo "命令已发送。"
echo "若鼠标没有切到另一台电脑，请换一个信道号再试 (./switch.sh 0 / 1 / 2)。"
echo "切走后这台电脑会暂时失去鼠标控制，属正常现象。"

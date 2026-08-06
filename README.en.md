# Rapoo MT760 Dual 2.4G Receiver Switcher

> Freely switch a Rapoo MT760 mouse between Linux and Windows machines — with a single command, a hotkey, or a custom mouse button. No official Rapoo software required (there is no Linux version), no `sudo` needed for day-to-day use.

---

## How It Works

### Background

The Rapoo MT760 ships with **two 2.4G USB receivers** — the intended design is to plug one receiver into each computer and switch the mouse's channel to decide which one it connects to. Switching is normally controlled by Rapoo's Windows management software, and **Rapoo has no Linux version** — which is exactly why Linux users cannot switch devices.

### The Switching Principle

This project **reverses the official software's switch command**:

1. Capture the switching process with Wireshark and discover that the `URB_CONTROL out` message is a **32-byte HID output report**
2. Diff the packets and find that **byte 8 is the target channel ID**
3. Send the report directly with [hidapitester](https://github.com/todbot/hidapitester/) — no driver unbinding, no official software

### Key Parameters

| Parameter | Value |
|---|---|
| VID:PID | `24ae:1870` (Rapoo MT760) |
| Cross-platform usage | `usagePage 0xff00 / usage 0x0e` |
| Report length | 32 bytes |
| Channel location | byte 8 (index 7) |
| Tested channels | `1` = Linux receiver, `2` = Windows receiver |

### Cross-Platform Notes

`usagePage 0xff00` (the vendor-defined range) is **the key to cross-platform compatibility**:

- Linux's usbhid driver is lenient about usage and accepts almost any value
- On Windows, the output report must match the report descriptor; `--usage 1` fails with `wrote -1 bytes`. Only the vendor usage `0xff00/0x0e` works on both systems

### Hotkey Design Rationale

Switching itself is a single command, but daily use needs a **convenient trigger**. This project provides the `Ctrl+Pause` hotkey on both machines:

| Trigger | What is actually sent |
|---|---|
| Linux keyboard `Ctrl+Pause` | standard Pause (VK 13) |
| Windows keyboard `Ctrl+Pause` | standard Pause (VK 13) |
| Windows custom mouse button (Rapoo driver macro) | **Ctrl+Break** (down as VK 03 / scancode 146, released as Pause) |

**Why Windows binds three hotkeys (`^Pause` + `^sc146` + `^vk03`)**: the mouse macro actually sends `Ctrl+Break`, not `Ctrl+Pause` — a well-known Windows quirk of the Pause/Break key (keydown is VK_CANCEL, keyup becomes VK_PAUSE). `^Pause` catches the physical keyboard; `^sc146`/`^vk03` catch the mouse macro. All three are needed.

**Why not a `Super+` combo**: on Linux GNOME (X11), the bare `Super` key is grabbed by the Shell to open the Activities overview, so any `Super`-based combo is intercepted by the Shell and can't reach custom shortcuts. `Ctrl+Pause` has no default binding on either Linux GNOME X11 or Windows and triggers reliably.

### References

| Reference | Role in this project |
|---|---|
| [phreer: Linux 上雷柏 MT760 鼠标 2.4G 接收器切换](https://phreer.github.io/2024/08/11/mouse-switcher-rapoo.html) | **Source of the approach**: capture → identify the HID output report → send with hidapitester → udev rule, the full methodology |
| [todbot/hidapitester](https://github.com/todbot/hidapitester/) | **Sending tool**: the CLI used to write HID output reports to the receiver; this project depends on it |
| [marcelhoffs/input-switcher](https://github.com/marcelhoffs/input-switcher/) | **Cross-platform pattern**: .bat + .vbs hidden-window wrapper, udev rule, same-key-on-both-machines switching |
| [Who-T: Understanding HID report descriptors](https://who-t.blogspot.com/2018/12/understanding-hid-report-descriptors.html) | **Protocol background**: Usage / Usage Page, report descriptors, and why the vendor usage range works across OSes |

---

## Deployment

### System Requirements

| Item | Linux | Windows |
|---|---|---|
| OS | Tested on Ubuntu 22.04 + GNOME **X11** session | Windows 10 / 11 |
| Mouse | Rapoo MT760 (VID `24ae:1870`), **two 2.4G receivers, one per computer** | Same |
| Extra software | None (repo bundles `hidapitester`; optional `edge-switch.py` needs Python 3) | [AutoHotkey v2](https://www.autohotkey.com/) |
| Permissions | One-time `sudo` to install the udev rule | No administrator needed |

> ⚠️ Linux is best used on an **X11** session. The `Super`-combo conflict comes from GNOME's Shell grab on X11; this project works around it (by using `Ctrl+Pause`), and the whole setup was verified on X11.

### Directory Layout

```
rapoo-switch/
├── switch.sh             # Linux switch command (core)
├── hidapitester          # Linux binary (from todbot/hidapitester)
├── 42-rapoo.rules        # udev rule: non-root access to the receiver
├── edge-switch.py        # [optional] switch when the cursor hits the screen edge
├── windows/
│   ├── hidapitester.exe        # Windows binary
│   ├── switch_to_linux.bat     # switch back to Linux from Windows
│   ├── switch_to_linux.vbs     # hidden-window wrapper for the .bat
│   ├── switch_back_to_linux.ahk# AutoHotkey v2 hotkey script
│   └── README.txt              # Windows setup/debug notes
├── README.md
├── README.en.md
└── LICENSE
```

### Linux Setup

```bash
# 1. Install the udev rule (non-root access to the receiver)
sudo cp 42-rapoo.rules /usr/lib/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
# If permissions still don't apply, unplug and replug the receiver once

# 2. Verify a normal user can access it (list the device, no permission error)
./hidapitester --vidpid 24ae:1870 --list-detail

# 3. Test switching (channel 2 = Windows receiver; adjust to your own mapping)
./switch.sh 2
```

> `switch.sh` uses the repo-local `hidapitester` by default; you can also install it to `~/.local/bin` or point to it with the `HIDAPITESTER` environment variable.

### Windows Setup

1. Install [AutoHotkey v2](https://www.autohotkey.com/)
2. Copy the `windows/` folder to the Windows machine
3. Double-click `switch_to_linux.bat` to verify (the mouse should switch back to Linux)
4. Double-click `switch_back_to_linux.ahk` to enable the hotkey (a green H icon appears in the tray; you can add it to startup)

### Keyboard Hotkey Binding

| Side | Binding | Action |
|---|---|---|
| Linux | GNOME custom shortcut: `<Control>Pause` → `bash /home/<user>/rapoo-switch/switch.sh 2` | Switch to Windows |
| Windows | AutoHotkey (`switch_back_to_linux.ahk`): `^Pause` + `^sc146` + `^vk03` → `switch_to_linux.vbs` | Switch to Linux |

On Linux, configure it under Settings → Keyboard → Custom Shortcuts; on Windows, run the `.ahk` script and it takes effect.

### Mouse Custom Button Binding (Recommended)

Bind a custom mouse button (e.g. the DPI button or a side button) to the same trigger, so a single mouse click switches machines. **Rapoo has no Linux software — the binding is configured once in the Rapoo Windows software, stored in the mouse's onboard memory, and then works on Linux too.**

1. Open the Rapoo management software on Windows → button customization / macro settings
2. Select the custom button and set it to send **`Ctrl+Pause`**
3. Save and write to the mouse (onboard storage)
4. Behavior on both machines afterwards:
   - Mouse on the Linux receiver: press the button → switch to Windows
   - Mouse on the Windows receiver: press the button → switch to Linux

> Note: the Rapoo macro actually sends `Ctrl+Break` (not `Ctrl+Pause`) on Windows — which is exactly why `switch_back_to_linux.ahk` also binds `^sc146` / `^vk03`. The Windows side already handles this; no extra configuration needed.

### Usage

```bash
./switch.sh 1     # switch to channel 1 (Linux receiver)
./switch.sh 2     # switch to channel 2 (Windows receiver)
```

**You have to find the channel numbers yourself**: try `0 / 1 / 2 / 3` one by one; the one that makes the mouse appear on the other computer is correct. After switching away, the current computer briefly has no mouse — that's normal.

### Edge-Switching (Optional)

`edge-switch.py` mimics the official software's "switch when the cursor reaches the screen edge" behavior (not in the original blog; added by this project):

```bash
python3 edge-switch.py --dry-run   # detect only, don't switch (verify first)
python3 edge-switch.py             # run
```

Use `--debug` for detailed logging; configure per-edge channels in the `CONFIG` dict at the top of the script.

### FAQ

**Q: Does it work without the udev rule?**
No. `/dev/hidraw*` is `root:root 600` by default; the udev rule (`uaccess` + `plugdev` group) is required to grant normal users read/write access.

**Q: On Windows the keyboard `Ctrl+Pause` works but the mouse button doesn't?**
The mouse macro injects `Ctrl+Break`, not `Ctrl+Pause` (Windows quirk: keydown is VK_CANCEL / SC 146, keyup becomes VK_PAUSE). Use the `switch_back_to_linux.ahk` from this repo, which already includes `^sc146` / `^vk03`. If it still fails, rebind the button in the Rapoo driver to send `Ctrl+F12` and update the AHK and Linux gsettings bindings accordingly.

**Q: How do I find the channel numbers?**
Try `./switch.sh 0 / 1 / 2 / 3` one by one; the one that moves the mouse to the other computer is the target. Each machine has its own channel.

---

## License

[MIT](LICENSE)

> The bundled `hidapitester` / `hidapitester.exe` binaries are prebuilt artifacts of [todbot/hidapitester](https://github.com/todbot/hidapitester/), © their original authors.

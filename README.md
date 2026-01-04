# 🎮 Switch 2 Pro Controller - macOS Driver

**The first working Bluetooth driver for the Nintendo Switch 2 Pro Controller on macOS.**

<p align="center">
  <img src="assets/demo.gif" alt="Demo" width="600">
</p>

[![macOS](https://img.shields.io/badge/macOS-Ventura%2B-blue?logo=apple)](https://www.apple.com/macos)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🚀 Features

- ✅ **Full button mapping** - All buttons, triggers, D-pad working
- ✅ **Analog sticks** - Both sticks with 12-bit precision
- ✅ **Grip buttons** - Switch 2 exclusive GL/GR buttons supported
- ✅ **Ryujinx compatible** - Keyboard bridge for emulator support
- ✅ **Low latency** - Direct BLE connection (~60ms updates)
- ✅ **No pairing required** - Bypasses macOS Bluetooth limitations

## ⚠️ Why This Exists

The Nintendo Switch 2 Pro Controller (Product ID: `0x2069`) doesn't work with macOS natively:
- **USB**: Firmware blocks non-Switch connections
- **Bluetooth Classic**: macOS can't pair with it
- **BLE**: Works! But requires custom driver (this project)

This driver connects via Bluetooth Low Energy using the `bleak` library, bypassing Apple's Bluetooth stack limitations.

## 📋 Requirements

- macOS Ventura (13.0) or later
- Python 3.9+
- Nintendo Switch 2 Pro Controller

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/AurelienDesert/switch2-mac-driver.git
cd switch2-mac-driver

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Quick Start

### Option 1: Raw Driver (for testing/development)

```bash
python src/driver.py
```

This displays all controller inputs in real-time. Great for verifying your controller works.

### Option 2: Ryujinx Bridge (for gaming)

```bash
python src/ryujinx_bridge.py
```

This converts controller inputs to keyboard presses for use with Ryujinx emulator.

**Ryujinx Configuration:**
1. Open Ryujinx → Options → Settings → Input
2. Set Input Device: **Keyboard**
3. Set Controller Type: **Pro Controller**
4. Map each button according to the table below

## 🎮 Button Mapping

### Controller → Keyboard (Ryujinx Bridge)

| Button | Key | | Button | Key |
|--------|-----|-|--------|-----|
| A | Z | | L | Q |
| B | X | | R | E |
| X | C | | ZL | 1 |
| Y | V | | ZR | 3 |
| + | P | | LS (click) | F |
| - | M | | RS (click) | G |
| Home | H | | GL (grip) | 9 |
| Capture | O | | GR (grip) | 0 |

| D-Pad | Key | | Stick | Keys |
|-------|-----|-|-------|------|
| Up | ↑ | | Left Stick | WASD |
| Down | ↓ | | Right Stick | IJKL |
| Left | ← | | | |
| Right | → | | | |

### Raw Protocol (for developers)

```
Byte 2 (buttons 1):  B=0x01, A=0x02, Y=0x04, X=0x08, R=0x10, ZR=0x20, +=0x40, RS=0x80
Byte 3 (buttons 2):  ↓=0x01, →=0x02, ←=0x04, ↑=0x08, L=0x10, ZL=0x20, -=0x40, LS=0x80
Byte 4 (buttons 3):  HOME=0x01, ●=0x02, GR=0x04, GL=0x08, CAPT=0x10

Sticks (12-bit, center=2048):
  Left:  X = byte5 | (byte6 & 0x0F) << 8
         Y = (byte6 >> 4) | byte7 << 4
  Right: X = byte8 | (byte9 & 0x0F) << 8
         Y = (byte9 >> 4) | byte10 << 4
```

## 📁 Project Structure

```
switch2-mac-driver/
├── src/
│   ├── driver.py           # Core BLE driver (raw input display)
│   ├── ryujinx_bridge.py   # Keyboard bridge for Ryujinx
│   └── calibrate.py        # Calibration utility
├── docs/
│   ├── PROTOCOL.md         # BLE protocol documentation
│   └── REVERSE_ENGINEERING.md
├── requirements.txt
├── LICENSE
└── README.md
```

## 🔬 Technical Details

### BLE Characteristics

| UUID | Handle | Purpose |
|------|--------|---------|
| `7492866c-ec3e-4619-8258-32755ffcc0f9` | 45 | Input reports (notifications) |
| `7492866c-ec3e-4619-8258-32755ffcc0f8` | 13 | Output (LED, rumble - WIP) |

### Device Identification

- **Vendor ID**: `0x057E` (Nintendo)
- **Product ID**: `0x2069` (Switch 2 Pro Controller)
- **Manufacturer Data**: Contains `\x7e\x05` or `\x69\x20`

## 🚧 Known Limitations

- **LED control**: Not working yet (output characteristic doesn't respond)
- **Rumble/Haptics**: Not implemented
- **Motion controls**: Not implemented (gyro/accelerometer data not decoded)
- **Analog precision**: Keyboard bridge is digital (8 directions), not true analog

## 🤝 Contributing

Contributions are welcome! Areas that need work:

1. **LED control** - Figure out the correct subcommand format for BLE
2. **Rumble** - Implement HD Rumble support
3. **Motion** - Decode and expose gyro/accelerometer data
4. **Virtual HID** - Create a proper virtual gamepad (would require DriverKit)

## 📜 Credits

- **Aurélien Desert** - Reverse engineering & macOS implementation
- **Claude (Anthropic)** - Development assistance
- Inspired by [SPro2Win](https://github.com/SquareDonut1/SPro2Win) (Windows driver)
- Protocol reference from [Nintendo Switch Reverse Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>⭐ Star this repo if it helped you!</b><br>
  <i>First macOS driver for Switch 2 Pro Controller - January 2026</i>
</p>

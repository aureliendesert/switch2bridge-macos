# Switch2 Bridge - macOS App

Menubar app for connecting your Switch 2 Pro Controller on macOS.

## Quick Build

```bash
chmod +x build_dmg.sh
./build_dmg.sh
```

The DMG installer will be in `dist/Switch2Bridge-Installer.dmg`

## Manual Build

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup_app.py py2app
```

The app will be in `dist/Switch2 Bridge.app`

## Files

| File | Description |
|------|-------------|
| `Switch2Bridge.py` | Main application |
| `setup_app.py` | py2app configuration |
| `build_dmg.sh` | Automated build script |
| `requirements.txt` | Python dependencies |

## First Launch

On first launch, macOS will ask for:
1. **Bluetooth** - To connect to the controller
2. **Accessibility** - To simulate keyboard input

Grant both permissions in System Settings → Privacy & Security.

## Usage

1. Click 🎮 in the menu bar
2. Select "Connect Controller"
3. Wait for connection (icon turns 🟢)
4. Play!

## Ryujinx Setup

In Ryujinx: Settings → Input → Keyboard → Pro Controller

Map buttons according to:
```
A→Z  B→X  X→C  Y→V
L→Q  R→E  ZL→1  ZR→3
+→P  -→M  Home→H
Left Stick: WASD
Right Stick: IJKL
D-Pad: Arrow keys
```

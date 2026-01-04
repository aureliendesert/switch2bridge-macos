#!/usr/bin/env python3
"""
Switch2 Bridge - macOS Menubar App
==================================

A clean menubar app to connect your Switch 2 Pro Controller
and use it with Ryujinx.

Author: Aurélien Desert
Date: January 2026
License: MIT
"""

import asyncio
import threading
import sys

# ============================================================
# DEPENDENCY CHECK
# ============================================================

try:
    import rumps
except ImportError:
    print("❌ rumps not installed")
    print("   Run: pip install rumps")
    sys.exit(1)

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("❌ bleak not installed")
    print("   Run: pip install bleak")
    sys.exit(1)

try:
    from pynput.keyboard import Controller, Key
    keyboard = Controller()
except ImportError:
    print("❌ pynput not installed")
    print("   Run: pip install pynput")
    print("\n   ⚠️  Grant Accessibility access in:")
    print("   System Settings → Privacy & Security → Accessibility")
    sys.exit(1)


# ============================================================
# CONSTANTS
# ============================================================

APP_NAME = "Switch2 Bridge"
INPUT_CHAR_UUID = "7492866c-ec3e-4619-8258-32755ffcc0f9"

BUTTON_KEYS = {
    'A': 'z', 'B': 'x', 'X': 'c', 'Y': 'v',
    'L': 'q', 'R': 'e', 'ZL': '1', 'ZR': '3',
    '+': 'p', '-': 'm', 'HOME': 'h', 'CAPT': 'o',
    'LS': 'f', 'RS': 'g', 'GL': '9', 'GR': '0',
    'DUP': Key.up, 'DDOWN': Key.down,
    'DLEFT': Key.left, 'DRIGHT': Key.right,
}

STICK_THRESHOLD = 0.5


# ============================================================
# CONTROLLER BRIDGE (from working ryujinx_bridge.py)
# ============================================================

class ControllerBridge:
    """Handles BLE connection and keyboard input simulation."""

    def __init__(self):
        self.is_connected = False
        self.is_searching = False
        self.controller_name = None
        self.packet_count = 0
        self.pressed_keys = set()
        self._client = None
        self._stop_event = threading.Event()

    def _set_key(self, key, active):
        """Set key state (from working code)."""
        if active:
            if key not in self.pressed_keys:
                self.pressed_keys.add(key)
                keyboard.press(key)
        else:
            if key in self.pressed_keys:
                self.pressed_keys.discard(key)
                keyboard.release(key)

    def _on_data(self, sender, data: bytes):
        """Parse controller data - EXACT COPY from working ryujinx_bridge.py"""
        if len(data) < 11:
            return

        self.packet_count += 1

        # Button bytes
        b2, b3, b4 = data[2], data[3], data[4]

        # === FACE BUTTONS (byte 2) ===
        self._set_key(BUTTON_KEYS['B'], b2 & 0x01)
        self._set_key(BUTTON_KEYS['A'], b2 & 0x02)
        self._set_key(BUTTON_KEYS['Y'], b2 & 0x04)
        self._set_key(BUTTON_KEYS['X'], b2 & 0x08)
        self._set_key(BUTTON_KEYS['R'], b2 & 0x10)
        self._set_key(BUTTON_KEYS['ZR'], b2 & 0x20)
        self._set_key(BUTTON_KEYS['+'], b2 & 0x40)
        self._set_key(BUTTON_KEYS['RS'], b2 & 0x80)

        # === D-PAD + LEFT TRIGGERS (byte 3) ===
        self._set_key(BUTTON_KEYS['DDOWN'], b3 & 0x01)
        self._set_key(BUTTON_KEYS['DRIGHT'], b3 & 0x02)
        self._set_key(BUTTON_KEYS['DLEFT'], b3 & 0x04)
        self._set_key(BUTTON_KEYS['DUP'], b3 & 0x08)
        self._set_key(BUTTON_KEYS['L'], b3 & 0x10)
        self._set_key(BUTTON_KEYS['ZL'], b3 & 0x20)
        self._set_key(BUTTON_KEYS['-'], b3 & 0x40)
        self._set_key(BUTTON_KEYS['LS'], b3 & 0x80)

        # === SPECIAL BUTTONS (byte 4) ===
        self._set_key(BUTTON_KEYS['HOME'], b4 & 0x01)
        self._set_key(BUTTON_KEYS['GR'], b4 & 0x04)
        self._set_key(BUTTON_KEYS['GL'], b4 & 0x08)
        self._set_key(BUTTON_KEYS['CAPT'], b4 & 0x10)

        # === ANALOG STICKS ===
        lx_raw = data[5] | ((data[6] & 0x0F) << 8)
        ly_raw = ((data[6] & 0xF0) >> 4) | (data[7] << 4)
        rx_raw = data[8] | ((data[9] & 0x0F) << 8)
        ry_raw = ((data[9] & 0xF0) >> 4) | (data[10] << 4)

        lx = (lx_raw - 2048) / 2048.0
        ly = (ly_raw - 2048) / 2048.0
        rx = (rx_raw - 2048) / 2048.0
        ry = (ry_raw - 2048) / 2048.0

        # Left stick → WASD
        self._set_key('w', ly > STICK_THRESHOLD)
        self._set_key('s', ly < -STICK_THRESHOLD)
        self._set_key('a', lx < -STICK_THRESHOLD)
        self._set_key('d', lx > STICK_THRESHOLD)

        # Right stick → IJKL
        self._set_key('i', ry > STICK_THRESHOLD)
        self._set_key('k', ry < -STICK_THRESHOLD)
        self._set_key('j', rx < -STICK_THRESHOLD)
        self._set_key('l', rx > STICK_THRESHOLD)

    def _release_all_keys(self):
        """Release all pressed keys."""
        for key in list(self.pressed_keys):
            try:
                keyboard.release(key)
            except:
                pass
        self.pressed_keys.clear()

    async def _find_controller(self, timeout=5.0):
        """Scan for Switch 2 Pro Controller."""
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

        for address, (device, adv) in devices.items():
            if adv.manufacturer_data:
                for company_id, data in adv.manufacturer_data.items():
                    if b'\x7e\x05' in data or b'\x69\x20' in data:
                        return address, device.name or "Switch 2 Pro Controller"
        return None, None

    async def _connect_async(self):
        """Async connection routine."""
        self.is_searching = True

        # Find controller
        address, name = await self._find_controller()

        if not address:
            self.is_searching = False
            return False

        self.is_searching = False

        # Connect
        try:
            self._client = BleakClient(address, timeout=30.0)
            await self._client.connect()

            if not self._client.is_connected:
                return False

            self.controller_name = name
            self.is_connected = True

            # Start notifications
            await self._client.start_notify(INPUT_CHAR_UUID, self._on_data)

            # Keep alive until stop requested or disconnected
            while not self._stop_event.is_set() and self._client.is_connected:
                await asyncio.sleep(0.1)

            # Cleanup
            if self._client.is_connected:
                await self._client.stop_notify(INPUT_CHAR_UUID)
                await self._client.disconnect()

        except Exception as e:
            print(f"Connection error: {e}")

        self._release_all_keys()
        self.is_connected = False
        self.controller_name = None
        return False

    def connect(self, callback=None):
        """Start connection in background thread."""
        self._stop_event.clear()

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._connect_async())
            loop.close()
            if callback:
                callback()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def disconnect(self):
        """Request disconnection."""
        self._stop_event.set()


# ============================================================
# MENUBAR APP
# ============================================================

class Switch2BridgeApp(rumps.App):
    """Menubar application."""

    def __init__(self):
        super().__init__(APP_NAME, title="🎮", quit_button=None)
        self.bridge = ControllerBridge()
        self._build_menu()

        # Status check timer
        self._timer = rumps.Timer(self._check_status, 1)
        self._timer.start()

    def _build_menu(self):
        """Build menu based on current state."""
        self.menu.clear()

        if self.bridge.is_searching:
            self.title = "🔍"
            self.menu = [
                rumps.MenuItem("Searching...", callback=None),
                None,
                rumps.MenuItem("Quit", callback=self._quit),
            ]

        elif self.bridge.is_connected:
            self.title = "🟢"
            self.menu = [
                rumps.MenuItem(f"✓ {self.bridge.controller_name}", callback=None),
                rumps.MenuItem(f"   {self.bridge.packet_count} packets", callback=None),
                None,
                rumps.MenuItem("Disconnect", callback=self._disconnect),
                None,
                rumps.MenuItem("Button Mapping...", callback=self._show_mapping),
                rumps.MenuItem("Quit", callback=self._quit),
            ]

        else:
            self.title = "🎮"
            self.menu = [
                rumps.MenuItem("Connect Controller", callback=self._connect),
                None,
                rumps.MenuItem("○ Not connected", callback=None),
                None,
                rumps.MenuItem("Button Mapping...", callback=self._show_mapping),
                rumps.MenuItem("Quit", callback=self._quit),
            ]

    def _check_status(self, _):
        """Periodic status check to update menu."""
        self._build_menu()

    def _connect(self, _):
        """Start connection."""
        self.bridge.connect(callback=self._build_menu)
        self._build_menu()

    def _disconnect(self, _):
        """Disconnect."""
        self.bridge.disconnect()

    def _show_mapping(self, _):
        """Show mapping info."""
        rumps.alert(
            title="Ryujinx Button Mapping",
            message="""In Ryujinx: Settings → Input → Keyboard

BUTTONS:
  A→Z  B→X  X→C  Y→V
  L→Q  R→E  ZL→1  ZR→3
  +→P  -→M  Home→H  Capture→O

STICKS:
  Left: WASD
  Right: IJKL

D-PAD: Arrow keys""",
            ok="OK"
        )

    def _quit(self, _):
        """Quit app."""
        self.bridge.disconnect()
        rumps.quit_application()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print(f"\n🎮 {APP_NAME}")
    print("   App is running in the menu bar.\n")
    print("   ⚠️  Grant Accessibility access if prompted:")
    print("   System Settings → Privacy & Security → Accessibility\n")

    app = Switch2BridgeApp()
    app.run()

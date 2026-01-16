[中文版](./README_CN.md)

# HypeRate Desktop Overlay (EXE Ver.)

A minimalist desktop widget for HypeRate.io that displays your real-time heart rate. Designed for streamers and gamers, it supports overlaying on top of full-screen games (e.g., Delta Force).
**Attention**：This widget requires a HypeRate-enabled wearable device; the device collects and supplies real-time heart rate data through HypeRate.

## ✨ Key Features
* **Fully Automated**: Auto-fetches the secure token. Just enter your Short ID (e.g., `1F01`).
* **Game Overlay**: Stays on top of games using "Fullscreen Optimizations". 
* **Click-Through Mode**: Lock the widget to let mouse clicks pass through to your game.
* **System Tray Control**: Runs quietly in the background with no taskbar icon.

## 🚀 How to Use
1. **Start the device and note the ID**: Open the HypeRate app on your wearable and record the device HypeRate ID (e.g., `1F01`).
2. **Run**: Double-click `HypeRateOverlay.exe`.
3. **Set ID**: Enter your HypeRate ID on first launch.
4. **Move**: Press and hold the heart-rate number to drag it (position is saved automatically).
5. **Lock**: In the system tray (bottom-right), right-click the red heart (❤) icon and choose **"Lock Click-through"**.

## ⚙️ System Tray Menu (Right-click ❤)
* **🔒 Lock Click-through**:
    * [Check]: Widget becomes semi-transparent; mouse clicks pass through to the game.
    * [Uncheck]: Widget becomes solid; allows dragging and moving.
* **🚀 Start at Login**: Automatically launch when Windows starts.
* **🔄 Reset ID**: Change your HypeRate ID.
* **❌ Exit**: Close the application.

## ⚠️ Notes
* **Config File**: Located at `C:\Users\YourUser\HypeRateOverlay\config.json`.
* **Troubleshooting**: If the overlay does not appear in-game, please set your game display mode to **"Borderless Window"** or **"Windowed Fullscreen"**. (e.g. League of Legends, CS2)
# HypeRate Desktop Overlay (EXE Ver.)

A minimalist desktop widget for HypeRate.io that displays your real-time heart rate. Designed for streamers and gamers, it supports overlaying on top of full-screen games (e.g., Delta Force, LoL).

## ✨ Key Features
* **Fully Automated**: Auto-fetches the secure token. Just enter your Short ID (e.g., `2A01`).
* **Game Overlay**: Stays on top of games using "Fullscreen Optimizations".
* **Click-Through Mode**: Lock the widget to let mouse clicks pass through to your game.
* **System Tray Control**: Runs quietly in the background with no taskbar icon.

## 🚀 How to Use
1.  **Run**: Launch `HypeRateOverlay.exe`.
2.  **Setup**: Enter your HypeRate ID on the first launch (e.g., `2A01`, found at the end of your OBS URL).
3.  **Move**: Drag the number to your desired position (location is auto-saved).
4.  **Lock**: Right-click the **Red Heart (❤)** icon in your system tray and select **"Lock Click-through"**.

## ⚙️ System Tray Menu (Right-click ❤)
* **🔒 Lock Click-through**:
    * [Check]: Widget becomes semi-transparent; mouse clicks pass through to the game.
    * [Uncheck]: Widget becomes solid; allows dragging and moving.
* **🚀 Start at Login**: Automatically launch when Windows starts.
* **🔄 Reset ID**: Change your HypeRate ID.
* **❌ Exit**: Close the application.

## ⚠️ Notes
* **Config File**: Located at `C:\Users\YourUser\HypeRateOverlay\config.json`.
* **Troubleshooting**: If the overlay does not appear in-game, please set your game display mode to **"Borderless Window"** or **"Windowed Fullscreen"**.
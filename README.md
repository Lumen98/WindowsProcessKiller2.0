⚠️ This project is licensed under Creative Commons BY-NC 4.0. Commercial use, resale, or redistribution without permission is strictly prohibited.

FPS Booster

A powerful and user-friendly Windows application to optimize system performance by managing and terminating unnecessary processes. It provides both basic and advanced controls for users to boost FPS and overall system efficiency.

📊 Features

One-Click Boost: Automatically detects and terminates high CPU-consuming or blacklisted processes.

Advanced Process Management: Allows manual control to filter, sort, and manage processes.

Whitelist/Blacklist Management: Protect important processes or target unnecessary ones for termination.

System Process Protection: Warns users before terminating critical system processes.

Rolling Average CPU/Memory Monitoring: Smooth, real-time monitoring of system resource usage.

Customizable UI: Enhanced user experience with modern UI and smooth controls.

💻 Installation & Setup

Install Python 3.x:

Download Python and ensure it's added to your PATH.

Install Required Packages:

pip install -r requirements.txt

Required Packages:

PyQt5

psutil

GPUtil (optional, for GPU monitoring)

Run the Application:

python main.py

The application automatically requests admin rights for process management.

The console window is hidden for a seamless GUI experience.

🛠️ Usage Guide

1. Basic Mode

Click One-Click Boost to automatically terminate top CPU hogging and blacklisted processes.

View the top 10 processes consuming the most CPU and memory.

2. Advanced Mode

Search & Filter: Locate specific processes.

Sort: Arrange by CPU, Memory, Alphabetical, or GPU usage.

Select Processes: Kill, whitelist, or blacklist processes.

Warning for System Processes: Prevents accidental termination of critical processes.

3. Manage Lists Tab

View and remove processes from the Whitelist and Blacklist.

Changes are updated live without restarting the app.

🔑 Whitelist & Blacklist

Whitelist: Processes here are protected from termination.

Blacklist: Processes here are targeted for termination during One-Click Boost or manual actions.

Files:

user_whitelist.json: Stores user-defined whitelisted processes.

user_blacklist.json: Stores user-defined blacklisted processes.

💡 Key Files & Structure

FPS-Booster/
├── gui.py                # Main GUI logic
├── main.py               # Entry point, handles admin check
├── process_manager.py    # Process listing and termination logic
├── utils.py              # Helper functions for file management & logging
├── user_whitelist.json   # User-defined whitelist
├── user_blacklist.json   # User-defined blacklist
├── cache.json            # Cached selected processes
├── style.qss             # UI styling for the application
└── README.md             # This file

📉 Future Improvements

Detailed Process Info: Add process descriptions and parent-child hierarchy.

Custom Alerts: Notify users when blacklisted processes start.

Resource Usage Graphs: Visual CPU/GPU/Memory monitoring.

Auto Blacklist Suggestions: Recommend processes to blacklist.

🛡️ Safety Notes

System Process Protection: The app prevents the termination of critical processes like MpDefenderCoreService.exe.

Admin Rights: The app requires admin permissions to manage system processes effectively.

👨‍💻 Author

Developed by Lumen98. For inquiries or support, please contact: Lumenngoods@gmail.com.

🔒 License

This project is licensed under the MIT License. See the LICENSE file for more details.

🚀 Start Boosting!

Run the app and enjoy a faster, optimized system for gaming and productivity! 🚀

Happy Boosting! 💪


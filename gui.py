# gui.py

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

# We'll assume you have these functions in process_manager.py
from process_manager import list_processes, safe_kill

# We'll assume you have these in utils.py
from utils import (
    load_cached_processes,
    save_cached_processes,
    load_json_file,
    save_json_file,
    USER_WHITELIST_FILE,
    USER_BLACKLIST_FILE
)

def is_process_blacklisted(proc_name_lower):
    """
    You can implement your own logic or import from process_manager.py if desired.
    We'll just do a quick example here, or leave it as a placeholder.
    """
    blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")
    return proc_name_lower in [b.lower() for b in blacklist]

class FPSBoosterApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPS Booster")
        self.resize(1200, 800)

        self.cached_processes = load_cached_processes()
        self.timer = None

        # For the Advanced tab
        self.filter_text = ""
        self.filter_blacklisted_only = False
        self.sort_option = "CPU Usage"

        self.init_ui()
        self.start_auto_refresh()

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.tabs = QtWidgets.QTabWidget()

        self.basic_tab = QtWidgets.QWidget()
        self.advanced_tab = QtWidgets.QWidget()

        self.init_basic_tab()
        self.init_advanced_tab()

        self.tabs.addTab(self.basic_tab, "Basic Mode")
        self.tabs.addTab(self.advanced_tab, "Advanced Mode")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ---------------------------------------------------------------------
    # Basic Mode
    # ---------------------------------------------------------------------
    def init_basic_tab(self):
        layout = QtWidgets.QVBoxLayout()

        self.logo_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("logo.png")
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaledToWidth(400))
        else:
            self.logo_label.setText("Logo not found")
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        self.one_click_boost_btn = QtWidgets.QPushButton("One-Click Boost")
        self.one_click_boost_btn.setStyleSheet("font-size: 24px; padding: 10px;")
        self.one_click_boost_btn.clicked.connect(self.handle_one_click_boost)
        layout.addWidget(self.one_click_boost_btn, alignment=Qt.AlignCenter)

        self.basic_table = QtWidgets.QTableWidget()
        self.basic_table.setColumnCount(4)
        self.basic_table.setHorizontalHeaderLabels(["PID", "Process Name", "CPU %", "Memory %"])
        self.basic_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.basic_table)

        self.basic_tab.setLayout(layout)

    def load_basic_table(self):
        """Show top CPU hogging processes."""
        processes = list_processes()
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:10]

        self.basic_table.setUpdatesEnabled(False)
        self.basic_table.setRowCount(0)

        for row, proc in enumerate(top_processes):
            self.basic_table.insertRow(row)
            self.basic_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(proc['pid'])))
            self.basic_table.setItem(row, 1, QtWidgets.QTableWidgetItem(proc['name']))
            self.basic_table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{proc['cpu_percent']:.2f}"))
            self.basic_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{proc['memory_percent']:.2f}"))

        self.basic_table.setUpdatesEnabled(True)

    def handle_one_click_boost(self):
        """
        Kill the top 10 CPU hogs that are blacklisted or exceed 10% CPU usage,
        with a warning prompt for system processes.
        """
        processes = list_processes()
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)

        kill_count = 0
        for proc in processes[:10]:  # 🔍 Target top 10 CPU hogs
            pid = proc['pid']
            real_name = proc['name'].split()[0]
            lower_name = real_name.lower()

            # 🛑 Special case for MpDefenderCoreService.exe
            if lower_name == "mpdefendercoreservice.exe":
                QtWidgets.QMessageBox.information(
                    self,
                    "Warning",
                    "You tried terminating the MpDefenderCoreService.exe process, which is a vital anti-virus process built into Windows.\n"
                    "To stop this process, disable Windows Defender via settings. (NOT RECOMMENDED)",
                    QtWidgets.QMessageBox.Ok
                )
                continue  # Skip this process

            # 🔥 Attempt to kill the process (with system process warning)
            if is_process_blacklisted(lower_name) or proc['cpu_percent'] > 10.0:
                if safe_kill(pid, parent_window=self):  # ✅ Now includes system process warning
                    kill_count += 1

        # ✅ Show result summary
        QtWidgets.QMessageBox.information(
            self,
            "One-Click Boost",
            f"Killed {kill_count} processes hogging CPU!"
        )

    # ---------------------------------------------------------------------
    # Advanced Mode
    # ---------------------------------------------------------------------
    def init_advanced_tab(self):
        layout = QtWidgets.QVBoxLayout()

        # Filter row
        filter_layout = QtWidgets.QHBoxLayout()
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search by process name...")
        self.search_box.textChanged.connect(self.update_filter_text)
        filter_layout.addWidget(self.search_box)

        self.sort_dropdown = QtWidgets.QComboBox()
        self.sort_dropdown.addItems(["CPU Usage", "Memory Usage", "Alphabetical", "GPU Usage"])
        self.sort_dropdown.currentIndexChanged.connect(self.load_processes)
        filter_layout.addWidget(self.sort_dropdown)

        self.blacklist_checkbox = QtWidgets.QCheckBox("Show only blacklisted processes")
        self.blacklist_checkbox.stateChanged.connect(self.toggle_blacklist_filter)
        filter_layout.addWidget(self.blacklist_checkbox)

        layout.addLayout(filter_layout)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Select", "PID", "Process Name", "CPU %", "Memory %", "GPU %"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Action buttons
        btn_layout = QtWidgets.QHBoxLayout()

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_processes)
        btn_layout.addWidget(self.refresh_btn)

        self.remove_btn = QtWidgets.QPushButton("Remove Unnecessary Windows Processes")
        self.remove_btn.clicked.connect(self.remove_unnecessary_processes)
        btn_layout.addWidget(self.remove_btn)

        self.kill_btn = QtWidgets.QPushButton("Kill Selected")
        self.kill_btn.clicked.connect(self.kill_selected)
        btn_layout.addWidget(self.kill_btn)

        layout.addLayout(btn_layout)

        # Whitelist/Blacklist management
        list_mgmt_layout = QtWidgets.QHBoxLayout()

        self.add_whitelist_btn = QtWidgets.QPushButton("Add to Whitelist")
        self.add_whitelist_btn.clicked.connect(self.add_selected_to_whitelist)
        list_mgmt_layout.addWidget(self.add_whitelist_btn)

        self.add_blacklist_btn = QtWidgets.QPushButton("Add to Blacklist")
        self.add_blacklist_btn.clicked.connect(self.add_selected_to_blacklist)
        list_mgmt_layout.addWidget(self.add_blacklist_btn)

        layout.addLayout(list_mgmt_layout)

        self.advanced_tab.setLayout(layout)

    def load_processes(self):
        """Load processes into the advanced table, keeping checked processes synced."""
        self.table.setUpdatesEnabled(False)

        # 🔴 Disconnect itemChanged signal to prevent recursive calls
        try:
            self.table.itemChanged.disconnect(self.sync_checkbox_states)
        except TypeError:
            pass  # Ignore if not connected

        # 🔴 Step 1: Remember currently checked process names
        self.selected_process_names = set()
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                name_item = self.table.item(row, 2)
                if name_item:
                    self.selected_process_names.add(name_item.text().lower())

        self.table.setRowCount(0)

        # 🔴 Step 2: Load the latest process list
        processes = list_processes()

        # Apply filters if needed
        if self.filter_text:
            processes = [p for p in processes if self.filter_text in p['name'].lower()]

        if self.filter_blacklisted_only:
            processes = [p for p in processes if is_process_blacklisted(p['name'].split()[0].lower())]

        # 🔴 Step 3: Sort with checked processes at the top
        sort_option = self.sort_dropdown.currentText()
        if sort_option == "CPU Usage":
            processes.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, -x['cpu_percent']))
        elif sort_option == "Memory Usage":
            processes.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, -x['memory_percent']))
        elif sort_option == "Alphabetical":
            processes.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, x['name'].lower()))
        elif sort_option == "GPU Usage":
            processes.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, -x['gpu_percent']))

        # 🔴 Step 4: Rebuild the table and restore checked selections by name
        for row, proc in enumerate(processes):
            self.table.insertRow(row)

            # Checkbox
            checkbox = QtWidgets.QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Checked if proc['name'].lower() in self.selected_process_names else Qt.Unchecked)
            self.table.setItem(row, 0, checkbox)

            # PID
            pid_item = QtWidgets.QTableWidgetItem(str(proc['pid']))
            self.table.setItem(row, 1, pid_item)

            # Process Name
            name_item = QtWidgets.QTableWidgetItem(proc['name'])
            self.table.setItem(row, 2, name_item)

            # CPU %
            cpu_item = QtWidgets.QTableWidgetItem(f"{proc['cpu_percent']:.2f}")
            self.table.setItem(row, 3, cpu_item)

            # Memory %
            mem_item = QtWidgets.QTableWidgetItem(f"{proc['memory_percent']:.2f}")
            self.table.setItem(row, 4, mem_item)

            # GPU %
            gpu_val = f"{proc['gpu_percent']:.2f}" if proc['gpu_percent'] > 0 else "N/A"
            gpu_item = QtWidgets.QTableWidgetItem(gpu_val)
            self.table.setItem(row, 5, gpu_item)

        # 🔴 Reconnect the signal after the table is updated
        self.table.itemChanged.connect(self.sync_checkbox_states)

        self.table.setUpdatesEnabled(True)

    def sync_checkbox_states(self, item):
        """Ensure that selecting/deselecting one instance affects all instances of the same process."""
        if item.column() == 0:  # Only respond to checkbox changes
            row = item.row()
            process_name = self.table.item(row, 2).text().lower()
            new_state = item.checkState()

            # 🔴 Disconnect to avoid recursive triggering
            try:
                self.table.itemChanged.disconnect(self.sync_checkbox_states)
            except TypeError:
                pass

            # Apply the same check state to all matching processes
            for r in range(self.table.rowCount()):
                if self.table.item(r, 2).text().lower() == process_name:
                    self.table.item(r, 0).setCheckState(new_state)

            # Update the selection state
            if new_state == Qt.Checked:
                self.selected_process_names.add(process_name)
            else:
                self.selected_process_names.discard(process_name)

            # 🔴 Reconnect after processing
            self.table.itemChanged.connect(self.sync_checkbox_states)

    def remove_unnecessary_processes(self):
        """
        Example: kill known trivial processes, ignoring MpDefenderCoreService.exe
        if found in that list.
        """
        targets = ["GamingServices.exe", "YourPhone.exe", "OneDrive.exe", "SearchUI.exe"]
        kill_count = 0

        all_procs = list_processes()
        for proc in all_procs:
            real_name = proc['name'].split()[0]
            if real_name.lower() in [t.lower() for t in targets]:
                if real_name.lower() == "mpdefendercoreservice.exe":
                    QtWidgets.QMessageBox.information(
                        self,
                        "Warning",
                        "You tried terminating the MpDefenderCoreService.exe process which is a vital anti-virus process built into Windows. "
                        "If you would like to stop this process, you must disable Windows Defender completely via settings. (NOT RECOMMENDED)",
                        QtWidgets.QMessageBox.Ok
                    )
                else:
                    if safe_kill(proc['pid'], parent_window=self):
                        kill_count += 1

        QtWidgets.QMessageBox.information(
            self,
            "Remove Unnecessary Processes",
            f"Killed {kill_count} unnecessary processes."
        )
        self.load_processes()

    def kill_selected(self):
        """
        Kill selected processes, prompt to force kill if needed.
        """
        killed_count = 0

        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                pid = int(self.table.item(row, 1).text())
                process_name = self.table.item(row, 2).text().split()[0].lower()

                # Block killing Windows Defender
                if process_name == "mpdefendercoreservice.exe":
                    QtWidgets.QMessageBox.information(
                        self,
                        "Warning",
                        "You tried terminating the MpDefenderCoreService.exe process which is a vital anti-virus process built into Windows.\n"
                        "If you would like to stop this process, you must disable Windows Defender completely via settings. (NOT RECOMMENDED)",
                        QtWidgets.QMessageBox.Ok
                    )
                    continue

                # Attempt to kill the process
                if safe_kill(pid, parent_window=self):
                    killed_count += 1

        self.load_processes()

        # Show how many were killed
        QtWidgets.QMessageBox.information(
            self,
            "Kill Selected",
            f"Killed {killed_count} processes."
        )

    def add_selected_to_whitelist(self):
        row_count = self.table.rowCount()
        whitelist = load_json_file(USER_WHITELIST_FILE, "user_defined_whitelist")

        for row in range(row_count):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                displayed_name = self.table.item(row, 2).text()
                real_name = displayed_name.split()[0]
                if real_name not in whitelist:
                    whitelist.append(real_name)

        save_json_file(USER_WHITELIST_FILE, "user_defined_whitelist", whitelist)
        QtWidgets.QMessageBox.information(
            self,
            "Whitelist",
            "Selected processes have been added to your Whitelist.\n"
            "They will be protected from termination in the future."
        )
        self.load_processes()

    def add_selected_to_blacklist(self):
        row_count = self.table.rowCount()
        blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")

        for row in range(row_count):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                displayed_name = self.table.item(row, 2).text()
                real_name = displayed_name.split()[0]
                if real_name not in blacklist:
                    blacklist.append(real_name)

        save_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist", blacklist)
        QtWidgets.QMessageBox.information(
            self,
            "Blacklist",
            "Selected processes have been added to your Blacklist.\n"
            "They will be targeted for termination if found running."
        )
        self.load_processes()

    def update_filter_text(self, text):
        self.filter_text = text.lower()
        self.load_processes()

    def toggle_blacklist_filter(self, state):
        self.filter_blacklisted_only = (state == Qt.Checked)
        self.load_processes()

    def start_auto_refresh(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_all_tables)
        self.timer.start(2000)

    def refresh_all_tables(self):
        self.load_basic_table()
        self.load_processes()


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    window = FPSBoosterApp()
    window.show()
    sys.exit(app.exec_())

# gui.py

import sys
import psutil
from collections import deque
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

# from process_manager import safe_kill, is_process_blacklisted
# We'll assume you have safe_kill in a separate module. If not, define your safe_kill here.
from src.process_manager import safe_kill
from src.utils import (
    load_cached_processes,
    save_cached_processes,
    load_json_file,
    save_json_file,
    USER_WHITELIST_FILE,
    USER_BLACKLIST_FILE
)

############################################################
# PLACEHOLDER if you need is_process_blacklisted from process_manager
############################################################
def is_process_blacklisted(proc_name_lower):
    blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")
    return proc_name_lower in [b.lower() for b in blacklist]

############################################################
# MAIN CLASS
############################################################
class FPSBoosterApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPS Booster")
        self.resize(1200, 800)

        # Give our main window an object name so we can style it via QSS
        self.setObjectName("MainWindowBase")

        # Dictionary: pid -> psutil.Process
        self.process_map = {}

        # Rolling usage history (for CPU/mem usage)
        self.rolling_usage = {}

        # How many samples we keep per PID
        self.history_size = 3

        self.cached_processes = load_cached_processes()
        self.timer = None

        # For the Advanced tab
        self.filter_text = ""
        self.filter_blacklisted_only = False

        # Number of logical cores for CPU usage scaling
        self.num_cores = psutil.cpu_count(logical=True)

        self.init_ui()
        self.start_auto_refresh()

    ############################################################
    # 1) GUI Initialization
    ############################################################
    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout()
        # A little more breathing room
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.tabs = QtWidgets.QTabWidget()
        self.basic_tab = QtWidgets.QWidget()
        self.advanced_tab = QtWidgets.QWidget()
        self.manage_lists_tab = QtWidgets.QWidget()

        self.init_basic_tab()
        self.init_advanced_tab()
        self.init_manage_lists_tab()

        self.tabs.addTab(self.basic_tab, "Basic Mode")
        self.tabs.addTab(self.advanced_tab, "Advanced Mode")
        self.tabs.addTab(self.manage_lists_tab, "Manage Lists")

        self.tabs.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def on_tab_changed(self, index):
        if self.tabs.tabText(index) == "Manage Lists":
            self.load_manage_lists()

    ############################################################
    # 2) Manage Lists Tab
    ############################################################
    def init_manage_lists_tab(self):
        layout = QtWidgets.QVBoxLayout()

        # Whitelist Section
        whitelist_group = QtWidgets.QGroupBox("Whitelist")
        whitelist_layout = QtWidgets.QVBoxLayout()

        self.whitelist_table = QtWidgets.QTableWidget()
        self.whitelist_table.setColumnCount(1)
        self.whitelist_table.setHorizontalHeaderLabels(["Process Name"])
        self.whitelist_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        whitelist_layout.addWidget(self.whitelist_table)

        self.remove_whitelist_btn = QtWidgets.QPushButton("Remove from Whitelist")
        self.remove_whitelist_btn.clicked.connect(self.remove_from_whitelist)
        whitelist_layout.addWidget(self.remove_whitelist_btn)

        whitelist_group.setLayout(whitelist_layout)
        layout.addWidget(whitelist_group)

        # Blacklist Section
        blacklist_group = QtWidgets.QGroupBox("Blacklist")
        blacklist_layout = QtWidgets.QVBoxLayout()

        self.blacklist_table = QtWidgets.QTableWidget()
        self.blacklist_table.setColumnCount(1)
        self.blacklist_table.setHorizontalHeaderLabels(["Process Name"])
        self.blacklist_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        blacklist_layout.addWidget(self.blacklist_table)

        self.remove_blacklist_btn = QtWidgets.QPushButton("Remove from Blacklist")
        self.remove_blacklist_btn.clicked.connect(self.remove_from_blacklist)
        blacklist_layout.addWidget(self.remove_blacklist_btn)

        blacklist_group.setLayout(blacklist_layout)
        layout.addWidget(blacklist_group)

        self.manage_lists_tab.setLayout(layout)
        self.load_manage_lists()

    def load_manage_lists(self):
        # Whitelist
        whitelist = load_json_file(USER_WHITELIST_FILE, "user_defined_whitelist")
        self.whitelist_table.setRowCount(0)
        for row, process in enumerate(whitelist):
            self.whitelist_table.insertRow(row)
            self.whitelist_table.setItem(row, 0, QtWidgets.QTableWidgetItem(process))

        # Blacklist
        blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")
        self.blacklist_table.setRowCount(0)
        for row, process in enumerate(blacklist):
            self.blacklist_table.insertRow(row)
            self.blacklist_table.setItem(row, 0, QtWidgets.QTableWidgetItem(process))

    ############################################################
    # 3) Basic Mode Tab
    ############################################################
    def init_basic_tab(self):
        layout = QtWidgets.QVBoxLayout()

        # (Optional) Create a frame around the logo for a "card" style
        logo_frame = QtWidgets.QFrame()
        logo_frame.setObjectName("LogoFrame")  # Style in QSS if desired
        logo_layout = QtWidgets.QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_frame.setLayout(logo_layout)

        self.logo_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("../assets/logo.png")
        if not pixmap.isNull():
            # Keep aspect ratio & use smooth transformation
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.setText("Logo not found")
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        logo_layout.addWidget(self.logo_label)

        layout.addWidget(logo_frame, alignment=Qt.AlignCenter)

        self.one_click_boost_btn = QtWidgets.QPushButton("One-Click Boost")
        # Assign a special object name so we can style it differently in QSS
        self.one_click_boost_btn.setObjectName("OneClickBoostBtn")
        self.one_click_boost_btn.clicked.connect(self.handle_one_click_boost)
        layout.addWidget(self.one_click_boost_btn, alignment=Qt.AlignCenter)

        self.basic_table = QtWidgets.QTableWidget()
        self.basic_table.setColumnCount(4)
        self.basic_table.setHorizontalHeaderLabels(["PID", "Process Name", "CPU %", "Memory %"])
        self.basic_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.basic_table.setAlternatingRowColors(True)

        # Enable hover tracking to see :hover in QSS
        self.basic_table.setMouseTracking(True)
        self.basic_table.viewport().setAttribute(QtCore.Qt.WA_Hover, True)

        layout.addWidget(self.basic_table)
        self.basic_tab.setLayout(layout)

    def load_basic_table(self):
        process_list = []
        for pid, proc in self.process_map.items():
            try:
                name = proc.name()
                if pid not in self.rolling_usage:
                    continue

                cpu_deque = self.rolling_usage[pid]["cpu_history"]
                if len(cpu_deque) == 0:
                    continue

                avg_cpu = sum(cpu_deque) / len(cpu_deque)
                mem_deque = self.rolling_usage[pid]["mem_history"]
                avg_mem = sum(mem_deque) / len(mem_deque) if len(mem_deque) > 0 else 0

                process_list.append({
                    'pid': pid,
                    'name': name,
                    'cpu_percent': avg_cpu,
                    'memory_percent': avg_mem
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort descending by CPU
        process_list.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = process_list[:10]

        self.basic_table.setUpdatesEnabled(False)
        self.basic_table.setRowCount(0)

        for row, proc_data in enumerate(top_processes):
            self.basic_table.insertRow(row)
            self.basic_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(proc_data['pid'])))
            self.basic_table.setItem(row, 1, QtWidgets.QTableWidgetItem(proc_data['name']))
            self.basic_table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{proc_data['cpu_percent']:.2f}"))
            self.basic_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{proc_data['memory_percent']:.2f}"))

        self.basic_table.setUpdatesEnabled(True)

    def handle_one_click_boost(self):
        process_list = []
        for pid, proc in self.process_map.items():
            if pid not in self.rolling_usage:
                continue

            # Get the process name
            name = proc.name()
            process_list.append({
                'pid': pid,
                'name': name,
            })

        # Sort processes alphabetically for consistent behavior (optional)
        process_list.sort(key=lambda x: x['name'].lower())

        kill_count = 0
        for item in process_list:
            pid = item['pid']
            real_name = item['name'].split()[0]
            lower_name = real_name.lower()

            # Only kill processes that are explicitly blacklisted
            if is_process_blacklisted(lower_name):
                if safe_kill(pid, parent_window=self):
                    kill_count += 1

        # Show a message box with the number of killed processes
        QtWidgets.QMessageBox.information(
            self,
            "One-Click Boost",
            f"Killed {kill_count} blacklisted processes!"
        )

    ############################################################
    # 4) Advanced Mode Tab
    ############################################################
    def init_advanced_tab(self):
        layout = QtWidgets.QVBoxLayout()

        # Filter + Sort row
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

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Select", "PID", "Process Name", "CPU %", "Memory %", "GPU %"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        # Enable hover tracking
        self.table.setMouseTracking(True)
        self.table.viewport().setAttribute(QtCore.Qt.WA_Hover, True)

        layout.addWidget(self.table)

        btn_layout = QtWidgets.QHBoxLayout()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_processes)
        btn_layout.addWidget(self.refresh_btn)

        self.kill_btn = QtWidgets.QPushButton("Kill Selected")
        self.kill_btn.clicked.connect(self.kill_selected)
        btn_layout.addWidget(self.kill_btn)
        layout.addLayout(btn_layout)

        # List Management Buttons
        list_mgmt_layout = QtWidgets.QHBoxLayout()

        self.add_whitelist_btn = QtWidgets.QPushButton("Add to Whitelist")
        self.add_whitelist_btn.clicked.connect(self.add_selected_to_whitelist)
        list_mgmt_layout.addWidget(self.add_whitelist_btn)

        self.remove_whitelist_btn2 = QtWidgets.QPushButton("Remove from Whitelist")
        self.remove_whitelist_btn2.clicked.connect(self.remove_from_whitelist)
        list_mgmt_layout.addWidget(self.remove_whitelist_btn2)

        self.add_blacklist_btn = QtWidgets.QPushButton("Add to Blacklist")
        self.add_blacklist_btn.clicked.connect(self.add_selected_to_blacklist)
        list_mgmt_layout.addWidget(self.add_blacklist_btn)

        self.remove_blacklist_btn2 = QtWidgets.QPushButton("Remove from Blacklist")
        self.remove_blacklist_btn2.clicked.connect(self.remove_from_blacklist)
        list_mgmt_layout.addWidget(self.remove_blacklist_btn2)

        layout.addLayout(list_mgmt_layout)

        self.advanced_tab.setLayout(layout)

    def load_processes(self):
        self.table.setUpdatesEnabled(False)
        try:
            self.table.itemChanged.disconnect(self.sync_checkbox_states)
        except TypeError:
            pass

        # Remember checked processes
        self.selected_process_names = set()
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                name_item = self.table.item(row, 2)
                if name_item:
                    self.selected_process_names.add(name_item.text().lower())

        self.table.setRowCount(0)

        # Build list from rolling averages
        full_list = []
        for pid, proc in self.process_map.items():
            if pid not in self.rolling_usage:
                continue

            cpu_deque = self.rolling_usage[pid]["cpu_history"]
            mem_deque = self.rolling_usage[pid]["mem_history"]
            if len(cpu_deque) == 0:
                continue

            avg_cpu = sum(cpu_deque) / len(cpu_deque)
            avg_mem = sum(mem_deque) / len(mem_deque) if len(mem_deque) > 0 else 0
            name = proc.name()

            # GPU usage placeholder
            gpu_usage = 0.0

            full_list.append({
                'pid': pid,
                'name': name,
                'cpu_percent': avg_cpu,
                'memory_percent': avg_mem,
                'gpu_percent': gpu_usage
            })

        # Filter
        if self.filter_text:
            full_list = [p for p in full_list if self.filter_text in p['name'].lower()]

        # Show only blacklisted?
        if self.filter_blacklisted_only:
            full_list = [p for p in full_list if is_process_blacklisted(p['name'].split()[0].lower())]

        # Sort with checked processes at the top
        sort_option = self.sort_dropdown.currentText()
        if sort_option == "CPU Usage":
            full_list.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, -x['cpu_percent']))
        elif sort_option == "Memory Usage":
            full_list.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, -x['memory_percent']))
        elif sort_option == "Alphabetical":
            full_list.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, x['name'].lower()))
        elif sort_option == "GPU Usage":
            full_list.sort(key=lambda x: (x['name'].lower() not in self.selected_process_names, -x['gpu_percent']))

        # Populate table
        for row, proc in enumerate(full_list):
            self.table.insertRow(row)

            # Checkbox
            checkbox = QtWidgets.QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            if proc['name'].lower() in self.selected_process_names:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, checkbox)

            pid_item = QtWidgets.QTableWidgetItem(str(proc['pid']))
            self.table.setItem(row, 1, pid_item)

            name_item = QtWidgets.QTableWidgetItem(proc['name'])
            self.table.setItem(row, 2, name_item)

            cpu_item = QtWidgets.QTableWidgetItem(f"{proc['cpu_percent']:.2f}")
            self.table.setItem(row, 3, cpu_item)

            mem_item = QtWidgets.QTableWidgetItem(f"{proc['memory_percent']:.2f}")
            self.table.setItem(row, 4, mem_item)

            gpu_val = f"{proc['gpu_percent']:.2f}" if proc['gpu_percent'] > 0 else "N/A"
            gpu_item = QtWidgets.QTableWidgetItem(gpu_val)
            self.table.setItem(row, 5, gpu_item)

        self.table.itemChanged.connect(self.sync_checkbox_states)
        self.table.setUpdatesEnabled(True)

    def sync_checkbox_states(self, item):
        if item.column() == 0:
            row = item.row()
            process_name = self.table.item(row, 2).text().lower()
            new_state = item.checkState()
            try:
                self.table.itemChanged.disconnect(self.sync_checkbox_states)
            except TypeError:
                pass

            # Ensure all rows with the same process_name match the new state
            for r in range(self.table.rowCount()):
                if self.table.item(r, 2).text().lower() == process_name:
                    self.table.item(r, 0).setCheckState(new_state)

            if new_state == Qt.Checked:
                self.selected_process_names.add(process_name)
            else:
                self.selected_process_names.discard(process_name)

            self.table.itemChanged.connect(self.sync_checkbox_states)

    def kill_selected(self):
        killed_count = 0
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                pid = int(self.table.item(row, 1).text())
                if safe_kill(pid, parent_window=self):
                    killed_count += 1

        self.load_processes()
        QtWidgets.QMessageBox.information(
            self,
            "Kill Selected",
            f"Killed {killed_count} processes."
        )

    ############################################################
    # 5) Whitelist/Blacklist Management
    ############################################################
    def add_selected_to_whitelist(self):
        whitelist = load_json_file(USER_WHITELIST_FILE, "user_defined_whitelist")

        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                process_name = self.table.item(row, 2).text().split()[0]
                if process_name not in whitelist:
                    whitelist.append(process_name)

        save_json_file(USER_WHITELIST_FILE, "user_defined_whitelist", whitelist)
        QtWidgets.QMessageBox.information(self, "Whitelist", "Selected processes have been added to the Whitelist.")
        self.load_processes()

    def remove_from_whitelist(self):
        # If triggered from the advanced tab
        if self.sender() == self.remove_whitelist_btn2:
            selected_rows = self.table.selectionModel().selectedRows()
            if not selected_rows:
                QtWidgets.QMessageBox.information(self, "No Selection",
                                                  "Please select a process to remove from the Whitelist.")
                return

            whitelist = load_json_file(USER_WHITELIST_FILE, "user_defined_whitelist")
            for row in selected_rows:
                process_name = self.table.item(row.row(), 2).text().split()[0]
                if process_name in whitelist:
                    whitelist.remove(process_name)

            save_json_file(USER_WHITELIST_FILE, "user_defined_whitelist", whitelist)
            QtWidgets.QMessageBox.information(self, "Removed", "Selected process(es) removed from the Whitelist.")
            self.load_processes()
        else:
            # If triggered from the Manage Lists tab
            selected_rows = self.whitelist_table.selectionModel().selectedRows()
            if not selected_rows:
                QtWidgets.QMessageBox.information(self, "No Selection",
                                                  "Please select a process to remove from the Whitelist.")
                return

            whitelist = load_json_file(USER_WHITELIST_FILE, "user_defined_whitelist")
            for row in selected_rows:
                process_name = self.whitelist_table.item(row.row(), 0).text()
                if process_name in whitelist:
                    whitelist.remove(process_name)

            save_json_file(USER_WHITELIST_FILE, "user_defined_whitelist", whitelist)
            QtWidgets.QMessageBox.information(self, "Removed", "Selected process(es) removed from the Whitelist.")
            self.load_manage_lists()

    def add_selected_to_blacklist(self):
        blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")

        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                process_name = self.table.item(row, 2).text().split()[0]
                if process_name not in blacklist:
                    blacklist.append(process_name)

        save_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist", blacklist)
        QtWidgets.QMessageBox.information(self, "Blacklist", "Selected processes have been added to the Blacklist.")
        self.load_processes()

    def remove_from_blacklist(self):
        # If triggered from the advanced tab
        if self.sender() == self.remove_blacklist_btn2:
            selected_rows = self.table.selectionModel().selectedRows()
            if not selected_rows:
                QtWidgets.QMessageBox.information(self, "No Selection",
                                                  "Please select a process to remove from the Blacklist.")
                return

            blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")
            for row in selected_rows:
                process_name = self.table.item(row.row(), 2).text().split()[0]
                if process_name in blacklist:
                    blacklist.remove(process_name)

            save_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist", blacklist)
            QtWidgets.QMessageBox.information(self, "Removed", "Selected process(es) removed from the Blacklist.")
            self.load_processes()
        else:
            # If triggered from the Manage Lists tab
            selected_rows = self.blacklist_table.selectionModel().selectedRows()
            if not selected_rows:
                QtWidgets.QMessageBox.information(self, "No Selection",
                                                  "Please select a process to remove from the Blacklist.")
                return

            blacklist = load_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist")
            for row in selected_rows:
                process_name = self.blacklist_table.item(row.row(), 0).text()
                if process_name in blacklist:
                    blacklist.remove(process_name)

            save_json_file(USER_BLACKLIST_FILE, "user_defined_blacklist", blacklist)
            QtWidgets.QMessageBox.information(self, "Removed", "Selected process(es) removed from the Blacklist.")
            self.load_manage_lists()

    def update_filter_text(self, text):
        self.filter_text = text.lower()
        self.load_processes()

    def toggle_blacklist_filter(self, state):
        self.filter_blacklisted_only = (state == Qt.Checked)
        self.load_processes()

    ############################################################
    # 6) Periodic Refresh
    ############################################################
    def start_auto_refresh(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_all_tables)
        self.timer.start(3000)  # 3 seconds

    def refresh_all_tables(self):
        self.update_process_map()
        self.load_basic_table()
        self.load_processes()

    ############################################################
    # 7) Maintaining psutil.Process Objects + Rolling Averages
    ############################################################
    def update_process_map(self):
        # 1) Remove ended processes
        dead_pids = []
        for pid, proc in self.process_map.items():
            try:
                proc.status()
            except psutil.NoSuchProcess:
                dead_pids.append(pid)

        for pid in dead_pids:
            if pid in self.rolling_usage:
                del self.rolling_usage[pid]
            del self.process_map[pid]

        # 2) Add new processes
        for pinfo in psutil.process_iter(['pid', 'name']):
            pid = pinfo.info['pid']
            name = pinfo.info['name'].lower()
            if pid == 0 or name == "system idle process":
                # skip idle
                continue

            if pid not in self.process_map:
                try:
                    self.process_map[pid] = psutil.Process(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        # 3) Update rolling averages
        for pid, proc in self.process_map.items():
            try:
                raw_cpu = proc.cpu_percent(interval=None)
                scaled_cpu = raw_cpu / self.num_cores
                mem_usage = proc.memory_percent()

                if pid not in self.rolling_usage:
                    self.rolling_usage[pid] = {
                        "cpu_history": deque(maxlen=self.history_size),
                        "mem_history": deque(maxlen=self.history_size)
                    }

                self.rolling_usage[pid]["cpu_history"].append(scaled_cpu)
                self.rolling_usage[pid]["mem_history"].append(mem_usage)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

############################################################
# 8) LOAD STYLE SHEET & ENTRY POINT
############################################################
def load_stylesheet(app, stylesheet_path="style.qss"):
    with open(stylesheet_path, "r", encoding="utf-8") as f:
        style = f.read()
    app.setStyleSheet(style)

def run_app():
    app = QtWidgets.QApplication(sys.argv)

    # Optional: Use a built-in style first, then apply QSS
    app.setStyle("Fusion")

    load_stylesheet(app, "../assets/style.qss")  # Update path if needed

    window = FPSBoosterApp()
    window.show()
    sys.exit(app.exec_())

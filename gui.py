from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from process_manager import list_processes, safe_kill
from utils import load_cached_processes, save_cached_processes

class FPSBoosterApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPS Booster")
        self.resize(1200, 800)
        self.cached_processes = load_cached_processes()
        self.sort_option = "CPU Usage"
        self.init_ui()
        self.start_auto_refresh()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        self.logo_label = QtWidgets.QLabel()
        self.logo_pixmap = QtGui.QPixmap("logo.png")
        if not self.logo_pixmap.isNull():
            self.logo_label.setPixmap(self.logo_pixmap.scaledToWidth(400))
        else:
            self.logo_label.setText("Logo not found")
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        self.sort_dropdown = QtWidgets.QComboBox()
        self.sort_dropdown.addItems(["CPU Usage", "Alphabetical"])
        self.sort_dropdown.currentIndexChanged.connect(self.load_processes)
        layout.addWidget(self.sort_dropdown)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Select", "PID", "Process Name", "CPU %"])
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.remove_btn = QtWidgets.QPushButton("Remove Unnecessary Windows Processes")
        self.kill_btn = QtWidgets.QPushButton("Kill Selected")

        self.refresh_btn.clicked.connect(self.load_processes)
        self.remove_btn.clicked.connect(self.remove_unecessary_processes)
        self.kill_btn.clicked.connect(self.kill_selected)

        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.remove_btn)
        layout.addWidget(self.kill_btn)

        self.setLayout(layout)
        self.load_processes()

    def start_auto_refresh(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.load_processes)
        self.timer.start(1000)

    def remove_unecessary_processes(self):
        selected_processes = ["GamingServices.exe",
        "YourPhone.exe",
        "OneDrive.exe",
        "SearchUI.exe",
        "RuntimeBroker.exe",
        "wsappx",
        "Microsoft.Photos.exe",
        "SkypeApp.exe",
        "AdobeARM.exe",
        "MicrosoftEdgeUpdate.exe",
        "Teams.exe",
        "backgroundTaskHost.exe",
        "smartscreen.exe",
        "OfficeClickToRun.exe",
        "XboxAppServices.exe",
        "GameBarPresenceWriter.exe",
        "OneApp.IGCC.WinService.exe",
        "GetSkype.exe",
        "SearchIndexer.exe"]
        save_cached_processes(selected_processes)
        self.load_processes()

    def load_processes(self):
        self.table.setUpdatesEnabled(False)
        current_selection = {self.table.item(row, 2).text(): self.table.item(row, 0).checkState() for row in range(self.table.rowCount())}

        self.table.setRowCount(0)
        processes = list_processes()

        if self.sort_dropdown.currentText() == "CPU Usage":
            processes.sort(key=lambda x: (x['name'] not in self.cached_processes, -x['cpu_percent']))
        else:
            processes.sort(key=lambda x: (x['name'] not in self.cached_processes, x['name'].lower()))

        for row, proc in enumerate(processes):
            self.table.insertRow(row)
            checkbox = QtWidgets.QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(current_selection.get(proc['name'], Qt.Unchecked))
            self.table.setItem(row, 0, checkbox)
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(proc['pid'])))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(proc['name']))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{proc['cpu_percent']:.2f}"))

        self.table.setUpdatesEnabled(True)

    def kill_selected(self):
        selected_processes = []
        for row in range(self.table.rowCount()):
            success = False
            if self.table.item(row, 0) is not None and self.table.item(row, 0).checkState() == Qt.Checked:
                pid = int(self.table.item(row, 1).text())
                process_name = self.table.item(row, 2).text()
                print(process_name)
                if process_name.lower() == "mpdefendercoreservice.exe":
                    QtWidgets.QMessageBox.information(self, "Warning", "You tried terminating the MpDefenderCoreService.exe process which is a vital anti-virus process built into Windows. "
                                                                       "If you would like to stop this process you must disable Windows Defender completely via settings. (NOT RECOMMENDED)", QtWidgets.QMessageBox.Ok)
                    success = True
                if not success:
                    success = safe_kill(pid)
                if not success:
                    response = QtWidgets.QMessageBox.question(self, "Force Kill?", f"Failed to kill {process_name}. Force kill?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if response == QtWidgets.QMessageBox.Yes:
                        success = safe_kill(pid, force=True)
                if success:
                    selected_processes.append(process_name)
        save_cached_processes(selected_processes)
        self.load_processes()


def run_app():
    app = QtWidgets.QApplication([])
    window = FPSBoosterApp()
    window.show()
    app.exec_()
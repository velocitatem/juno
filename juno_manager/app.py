import sys
import os
import subprocess
import shutil
import threading
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
                           QListWidget, QListWidgetItem, QMessageBox, QComboBox,
                             QFileDialog, QGroupBox, QFormLayout, QCheckBox, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor


class WorkerThread(QThread):
    """Worker thread for running operations that might take time"""
    finished = pyqtSignal(bool, str)  # Success flag, Message

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        try:
            self.result = self.function(*self.args, **self.kwargs)
            self.finished.emit(True, "Operation completed successfully")
        except Exception as e:
            self.finished.emit(False, str(e))


class JunoApp(QMainWindow):
    # Button style constants
    PRIMARY_BUTTON_STYLE = """
        QPushButton {
            background-color: #1976D2;
            color: white;
            border-radius: 4px;
            padding: 8px 15px;
            font-weight: bold;
            min-height: 30px;
        }
        QPushButton:hover {
            background-color: #1565C0;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        QPushButton:disabled {
            background-color: #BBDEFB;
            color: #78909C;
        }
    """
    
    DANGER_BUTTON_STYLE = """
        QPushButton {
            background-color: #E53935;
            color: white;
            border-radius: 4px;
            padding: 8px 15px;
            font-weight: bold;
            min-height: 30px;
        }
        QPushButton:hover {
            background-color: #D32F2F;
        }
        QPushButton:pressed {
            background-color: #B71C1C;
        }
        QPushButton:disabled {
            background-color: #FFCDD2;
            color: #78909C;
        }
    """
    
    SECONDARY_BUTTON_STYLE = """
        QPushButton {
            background-color: #78909C;
            color: white;
            border-radius: 4px;
            padding: 8px 15px;
            min-height: 30px;
        }
        QPushButton:hover {
            background-color: #607D8B;
        }
        QPushButton:pressed {
            background-color: #455A64;
        }
        QPushButton:disabled {
            background-color: #CFD8DC;
            color: #90A4AE;
        }
    """
    
    def __init__(self):
        super().__init__()

        # Default base directory for virtual environments
        self.base_dir = os.environ.get("JUNO_VENV_DIR",
                                    os.path.join(os.path.expanduser("~"), ".jupyter_venvs"))

        # Create the base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)

        # Initialize thread attributes
        self.create_thread = None
        self.remove_thread = None
        self.install_thread = None
        self.worker_thread = None

        self.setWindowTitle("Juno - JupyterLab Virtual Environment Manager")
        self.setMinimumSize(800, 600)

        # Set application icon
        # self.setWindowIcon(QIcon("path/to/icon.png"))

        # Create the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Add title and description
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(15, 20, 15, 10)

        title_label = QLabel("♃ Juno: JupyterLab Virtual Environment Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_font.setFamily("Arial")
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1565C0;")
        title_label.setAlignment(Qt.AlignCenter)

        desc_label = QLabel("Manage Python virtual environments for JupyterLab.")
        desc_font = QFont()
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #546E7A; margin-bottom: 10px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)

        # Add a subtle separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #BBDEFB; border: none; height: 2px; margin: 0 15px;")

        self.main_layout.addWidget(header_container)
        self.main_layout.addWidget(separator)

        # Display storage location
        storage_container = QWidget()
        storage_layout = QHBoxLayout(storage_container)
        storage_layout.setContentsMargins(15, 10, 15, 10)

        storage_label = QLabel(f"Virtual environments stored at: {self.base_dir}")
        storage_label.setStyleSheet("background-color: #E3F2FD; color: #0D47A1; padding: 10px; border-radius: 5px; border: 1px solid #BBDEFB;")
        storage_layout.addWidget(storage_label)

        self.main_layout.addWidget(storage_container)

        # Status message area
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(15, 5, 15, 5)

        self.status_area = QLabel()
        self.status_area.setStyleSheet("padding: 12px; margin: 5px 0; border-radius: 5px; font-weight: bold;")
        self.status_area.setVisible(False)
        status_layout.addWidget(self.status_area)

        self.main_layout.addWidget(status_container)

        # Create the main content splitter (left/right panels)
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.content_splitter)

        # Left panel - Create environment
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # Create environment group
        self.create_env_group = QGroupBox("Create Environment")
        create_env_layout = QFormLayout()

        self.env_name_input = QLineEdit()
        self.env_name_input.setPlaceholderText("Enter environment name (alphanumeric and underscores)")

        self.packages_input = QLineEdit()
        self.packages_input.setPlaceholderText("Optional: numpy,pandas,matplotlib")

        self.create_btn = QPushButton("Create Environment")
        self.create_btn.clicked.connect(self.create_environment)

        create_env_layout.addRow("Environment Name:", self.env_name_input)
        create_env_layout.addRow("Additional Packages:", self.packages_input)
        create_env_layout.addRow(self.create_btn)

        self.create_env_group.setLayout(create_env_layout)
        self.left_layout.addWidget(self.create_env_group)

        # Help section
        help_group = QGroupBox("Help")
        help_layout = QVBoxLayout()

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>About Juno</h3>
        <p>Juno is an application designed to simplify the management of
        Python virtual environments for JupyterLab.</p>

        <h3>How to Use</h3>
        <ul>
            <li><b>Create Environment:</b> Enter a name and optional packages</li>
            <li><b>View Environments:</b> All environments are listed in the manage tab</li>
            <li><b>Remove Environment:</b> Select an environment and click 'Remove'</li>
            <li><b>Install Packages:</b> Add packages to an existing environment</li>
            <li><b>Export Requirements:</b> Export requirements.txt from any environment</li>
        </ul>

        <h3>Troubleshooting</h3>
        <ul>
            <li><b>Missing Jupyter:</b> Make sure Jupyter is installed</li>
            <li><b>Permission Issues:</b> Ensure you have write permissions</li>
            <li><b>Kernel Not Showing:</b> Restart JupyterLab after creating a new environment</li>
        </ul>
        """)

        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        self.left_layout.addWidget(help_group)

        # Right panel - Manage environments
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Add refresh button
        refresh_layout = QHBoxLayout()
        refresh_label = QLabel("Manage Environments")
        refresh_label.setFont(QFont("", 12, QFont.Bold))
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_environments)
        refresh_layout.addWidget(refresh_label)
        refresh_layout.addStretch()
        refresh_layout.addWidget(refresh_btn)
        self.right_layout.addLayout(refresh_layout)

        # Tabs for different management operations
        self.tabs = QTabWidget()

        # Tab 1: View and Remove
        self.view_tab = QWidget()
        view_layout = QVBoxLayout(self.view_tab)

        self.env_list = QListWidget()
        self.env_list.setSelectionMode(QListWidget.SingleSelection)
        self.env_list.itemClicked.connect(self.on_env_selected)

        view_layout.addWidget(QLabel("Select an environment:"))
        view_layout.addWidget(self.env_list)

        # Environment details
        self.env_details = QTextEdit()
        self.env_details.setReadOnly(True)
        self.env_details.setMaximumHeight(100)
        view_layout.addWidget(QLabel("Environment details:"))
        view_layout.addWidget(self.env_details)

        # Action buttons
        actions_layout = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected Environment")
        self.remove_btn.clicked.connect(self.confirm_remove_environment)
        self.remove_btn.setEnabled(False)
        actions_layout.addWidget(self.remove_btn)

        view_layout.addLayout(actions_layout)

        # Tab 2: Install Packages
        self.install_tab = QWidget()
        install_layout = QVBoxLayout(self.install_tab)

        self.install_env_combo = QComboBox()
        self.install_packages_input = QLineEdit()
        self.install_packages_input.setPlaceholderText("numpy,pandas,matplotlib")
        self.install_btn = QPushButton("Install Packages")
        self.install_btn.clicked.connect(self.install_packages)

        # Show installed packages
        self.show_packages_check = QCheckBox("Show Installed Packages")
        self.show_packages_check.stateChanged.connect(self.toggle_show_packages)
        self.packages_display = QTextEdit()
        self.packages_display.setReadOnly(True)
        self.packages_display.setVisible(False)

        install_layout.addWidget(QLabel("Select Environment:"))
        install_layout.addWidget(self.install_env_combo)
        install_layout.addWidget(QLabel("Packages to install (comma-separated):"))
        install_layout.addWidget(self.install_packages_input)
        install_layout.addWidget(self.install_btn)
        install_layout.addWidget(self.show_packages_check)
        install_layout.addWidget(self.packages_display)

        # Tab 3: Export Requirements
        self.export_tab = QWidget()
        export_layout = QVBoxLayout(self.export_tab)

        self.export_env_combo = QComboBox()
        self.export_btn = QPushButton("Export requirements.txt")
        self.export_btn.clicked.connect(self.export_requirements)
        self.export_display = QTextEdit()
        self.export_display.setReadOnly(True)
        self.export_save_btn = QPushButton("Save to File")
        self.export_save_btn.clicked.connect(self.save_requirements)
        self.export_save_btn.setEnabled(False)

        export_layout.addWidget(QLabel("Select Environment:"))
        export_layout.addWidget(self.export_env_combo)
        export_layout.addWidget(self.export_btn)
        export_layout.addWidget(QLabel("Requirements:"))
        export_layout.addWidget(self.export_display)
        export_layout.addWidget(self.export_save_btn)

        # Tab 4: Settings
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)

        self.base_dir_input = QLineEdit(self.base_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.base_dir_input)
        dir_layout.addWidget(browse_btn)

        update_dir_btn = QPushButton("Update Base Directory")
        update_dir_btn.clicked.connect(self.update_base_directory)

        settings_layout.addWidget(QLabel("Virtual Environments Directory:"))
        settings_layout.addLayout(dir_layout)
        settings_layout.addWidget(update_dir_btn)
        settings_layout.addStretch()

        # Add all tabs
        self.tabs.addTab(self.view_tab, "View & Remove")
        self.tabs.addTab(self.install_tab, "Install Packages")
        self.tabs.addTab(self.export_tab, "Export Requirements")
        self.tabs.addTab(self.settings_tab, "Settings")

        self.right_layout.addWidget(self.tabs)

        # Add panels to splitter
        self.content_splitter.addWidget(self.left_panel)
        self.content_splitter.addWidget(self.right_panel)
        self.content_splitter.setSizes([300, 500])

        # Add footer
        footer_label = QLabel("Juno: JupyterLab Virtual Environment Manager | MIT License")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #777; margin-top: 10px;")
        self.main_layout.addWidget(footer_label)

        # Initialize
        self.refresh_environments()

    def refresh_environments(self):
        """Refresh the list of environments"""
        self.env_list.clear()
        self.install_env_combo.clear()
        self.export_env_combo.clear()
        self.env_details.clear()
        self.remove_btn.setEnabled(False)

        # Get list of environments
        envs = self.list_envs()

        if not envs:
            item = QListWidgetItem("No environments found")
            item.setForeground(QColor("#999"))
            self.env_list.addItem(item)
            return

        # Add to list widget
        for env in envs:
            self.env_list.addItem(env)
            self.install_env_combo.addItem(env)
            self.export_env_combo.addItem(env)

    def on_env_selected(self, item):
        """Handle environment selection"""
        env_name = item.text()
        self.remove_btn.setEnabled(True)

        # Display environment details
        env_path = os.path.join(self.base_dir, env_name)
        python_version = self.get_python_version(env_name)

        details = f"Name: {env_name}\n"
        details += f"Path: {env_path}\n"
        details += f"Python: {python_version}\n"

        self.env_details.setText(details)

    def create_environment(self):
        """Create a new virtual environment"""
        env_name = self.env_name_input.text().strip()
        packages = self.packages_input.text().strip()

        if not env_name:
            self.show_status("Please provide a valid environment name", "error")
            return

        if not env_name.isalnum() and not all(c.isalnum() or c == '_' for c in env_name):
            self.show_status("Environment name should only contain alphanumeric characters and underscores", "error")
            return

        # Disable the create button to prevent multiple clicks
        self.create_btn.setEnabled(False)
        self.show_status("Creating environment... Please wait", "info")

        # Run the creation in a thread
        self.create_thread = WorkerThread(self.create_and_register_kernel, env_name, packages if packages else None)
        self.create_thread.finished.connect(self.on_create_finished)
        self.create_thread.start()

    def on_create_finished(self, success, message):
        """Handle completion of environment creation"""
        self.create_btn.setEnabled(True)
        if success:
            self.show_status(f"Virtual environment created successfully", "success")
            self.env_name_input.clear()
            self.packages_input.clear()
            self.refresh_environments()
        else:
            self.show_status(f"Error creating environment: {message}", "error")

    def confirm_remove_environment(self):
        """Confirm before removing an environment"""
        if not self.env_list.currentItem():
            return

        env_name = self.env_list.currentItem().text()

        reply = QMessageBox.question(
            self,
            'Confirm Removal',
            f"Are you sure you want to remove the environment '{env_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.remove_environment(env_name)

    def remove_environment(self, env_name):
        """Remove a virtual environment"""
        self.show_status(f"Removing environment '{env_name}'... Please wait", "info")

        # Disable buttons during removal
        self.remove_btn.setEnabled(False)

        # Run the removal in a thread
        self.remove_thread = WorkerThread(self.remove_kernel_and_env, env_name)
        self.remove_thread.finished.connect(lambda success, msg: self.on_remove_finished(success, msg, env_name))
        self.remove_thread.start()

    def on_remove_finished(self, success, message, env_name):
        """Handle completion of environment removal"""
        if success:
            self.show_status(f"Environment '{env_name}' removed successfully", "success")
        else:
            self.show_status(f"Error removing environment: {message}", "error")

        self.refresh_environments()

    def install_packages(self):
        """Install packages in the selected environment"""
        env_name = self.install_env_combo.currentText()
        packages = self.install_packages_input.text().strip()

        if not packages:
            self.show_status("Please specify at least one package to install", "error")
            return

        self.install_btn.setEnabled(False)
        self.show_status(f"Installing packages in '{env_name}'... Please wait", "info")

        # Run the installation in a thread
        self.install_thread = WorkerThread(self.install_packages_in_env, env_name, packages)
        self.install_thread.finished.connect(self.on_install_finished)
        self.install_thread.start()

    def on_install_finished(self, success, message):
        """Handle completion of package installation"""
        self.install_btn.setEnabled(True)
        if success:
            self.show_status("Packages installed successfully", "success")
            self.install_packages_input.clear()

            # Refresh package list if shown
            if self.show_packages_check.isChecked():
                self.show_packages()
        else:
            self.show_status(f"Error installing packages: {message}", "error")

    def toggle_show_packages(self, state):
        """Toggle display of installed packages"""
        self.packages_display.setVisible(state == Qt.Checked)
        if state == Qt.Checked:
            self.show_packages()

    def show_packages(self):
        """Show installed packages for the selected environment"""
        env_name = self.install_env_combo.currentText()
        if not env_name:
            return

        packages = self.get_installed_packages(env_name)
        if packages:
            self.packages_display.setText("\n".join(packages))
        else:
            self.packages_display.setText("Unable to retrieve package list.")

    def export_requirements(self):
        """Export requirements.txt from selected environment"""
        env_name = self.export_env_combo.currentText()
        if not env_name:
            return

        self.export_btn.setEnabled(False)
        self.show_status("Exporting requirements... Please wait", "info")

        # Run the export in a thread
        self.worker_thread = WorkerThread(self.export_requirements_from_env, env_name)
        self.worker_thread.finished.connect(self.on_export_finished)
        self.worker_thread.start()

    def on_export_finished(self, success, message):
        """Handle completion of requirements export"""
        self.export_btn.setEnabled(True)

        if success and isinstance(self.worker_thread.result, str):
            self.export_display.setText(self.worker_thread.result)
            self.export_save_btn.setEnabled(True)
            self.show_status("Requirements exported successfully", "success")
        else:
            self.export_display.setText("")
            self.export_save_btn.setEnabled(False)
            self.show_status(f"Error exporting requirements: {message}", "error")

    def save_requirements(self):
        """Save requirements.txt to a file"""
        env_name = self.export_env_combo.currentText()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Requirements",
            f"{env_name}_requirements.txt",
            "Text Files (*.txt)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.export_display.toPlainText())
                self.show_status(f"Requirements saved to {filename}", "success")
            except Exception as e:
                self.show_status(f"Error saving file: {str(e)}", "error")

    def browse_directory(self):
        """Browse for a directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Base Directory",
            self.base_dir_input.text()
        )

        if directory:
            self.base_dir_input.setText(directory)

    def update_base_directory(self):
        """Update the base directory for virtual environments"""
        new_dir = self.base_dir_input.text().strip()

        if not new_dir:
            self.show_status("Please provide a valid directory", "error")
            return

        if not os.path.exists(new_dir):
            reply = QMessageBox.question(
                self,
                'Create Directory',
                f"Directory does not exist. Create it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(new_dir, exist_ok=True)
                except Exception as e:
                    self.show_status(f"Error creating directory: {str(e)}", "error")
                    return
            else:
                return

        self.base_dir = new_dir
        self.show_status(f"Base directory updated to: {new_dir}", "success")

        # Update UI
        storage_label = self.findChild(QLabel, "storage_label")
        if storage_label:
            storage_label.setText(f"Virtual environments stored at: {self.base_dir}")

        self.refresh_environments()

    def show_status(self, message, status_type="info"):
        """Show a status message"""
        if status_type == "error":
            icon = "❌ "
            style = "background-color: #FFEBEE; color: #C62828; padding: 12px; border-radius: 5px; border: 1px solid #FFCDD2; font-weight: bold;"
        elif status_type == "success":
            icon = "✅ "
            style = "background-color: #E8F5E9; color: #2E7D32; padding: 12px; border-radius: 5px; border: 1px solid #C8E6C9; font-weight: bold;"
        else:  # info
            icon = "ℹ️ "
            style = "background-color: #E3F2FD; color: #1565C0; padding: 12px; border-radius: 5px; border: 1px solid #BBDEFB; font-weight: bold;"

        self.status_area.setText(f"{icon} {message}")
        self.status_area.setStyleSheet(style)
        self.status_area.setVisible(True)

        # Auto-hide after 5 seconds for success messages
        if status_type == "success":
            QTimer.singleShot(5000, lambda: self.status_area.setVisible(False))

    # Core functionality methods (adapted from Streamlit version)

    def list_envs(self, base_dir=None):
        """List all virtual environments in the base directory"""
        if base_dir is None:
            base_dir = self.base_dir

        if not os.path.exists(base_dir):
            return []

        return sorted([name for name in os.listdir(base_dir)
                      if os.path.isdir(os.path.join(base_dir, name))])

    def get_python_version(self, env_name):
        """Get Python version for a virtual environment"""
        env_path = os.path.join(self.base_dir, env_name)

        if os.name == "nt":
            python_executable = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(env_path, "bin", "python")

        try:
            result = subprocess.run(
                [python_executable, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown"

    def create_and_register_kernel(self, env_name, additional_packages=None):
        """Create a virtual environment and register it as a Jupyter kernel"""
        env_path = os.path.join(self.base_dir, env_name)

        if os.path.exists(env_path):
            raise Exception(f"Virtual environment '{env_name}' already exists")

        # Create the virtual environment
        subprocess.check_call([sys.executable, "-m", "venv", env_path])

        # Determine the python executable path for the new environment
        if os.name == "nt":
            python_executable = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(env_path, "bin", "python")

        # Upgrade pip and install ipykernel
        subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([python_executable, "-m", "pip", "install", "ipykernel"])

        # Install additional packages if specified
        if additional_packages:
            packages = [pkg.strip() for pkg in additional_packages.split(',') if pkg.strip()]
            if packages:
                subprocess.check_call([python_executable, "-m", "pip", "install"] + packages)

        # Register the kernel with Jupyter
        subprocess.check_call([
            python_executable, "-m", "ipykernel", "install",
            "--user",
            "--name", env_name,
            "--display-name", f"Python ({env_name})"
        ])

        return True

    def remove_kernel_and_env(self, env_name):
        """Unregister a Jupyter kernel and remove the associated virtual environment"""
        env_path = os.path.join(self.base_dir, env_name)

        if not os.path.exists(env_path):
            raise Exception(f"Environment '{env_name}' does not exist")

        # First try to uninstall the Jupyter kernel
        cmd = f"{sys.executable} -m jupyter kernelspec uninstall {env_name} -y"
        try:
            subprocess.run(
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                check=False  # Don't raise exception if this fails
            )
        except Exception:
            # Continue even if kernel uninstallation fails
            pass

        # Now remove the virtual environment directory
        if os.path.exists(env_path):
            shutil.rmtree(env_path)

        return True

    def install_packages_in_env(self, env_name, packages):
        """Install packages in a virtual environment"""
        env_path = os.path.join(self.base_dir, env_name)

        if not os.path.exists(env_path):
            raise Exception(f"Virtual environment '{env_name}' does not exist")

        if os.name == "nt":
            python_executable = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(env_path, "bin", "python")

        packages_list = [pkg.strip() for pkg in packages.split(',') if pkg.strip()]
        if not packages_list:
            raise Exception("No valid packages specified")

        subprocess.check_call([
            python_executable, "-m", "pip", "install"] + packages_list
        )

        return True

    def get_installed_packages(self, env_name):
        """Get list of installed packages in a virtual environment"""
        env_path = os.path.join(self.base_dir, env_name)

        if os.name == "nt":
            python_executable = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(env_path, "bin", "python")

        try:
            result = subprocess.run(
                [python_executable, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.splitlines()
        except subprocess.CalledProcessError:
            return []

    def export_requirements_from_env(self, env_name):
        """Export requirements.txt from a virtual environment"""
        env_path = os.path.join(self.base_dir, env_name)

        if not os.path.exists(env_path):
            raise Exception(f"Virtual environment '{env_name}' does not exist")

        if os.name == "nt":
            python_executable = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(env_path, "bin", "python")

        result = subprocess.run(
            [python_executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Set a modern color palette
    palette = app.palette()
    palette.setColor(palette.Window, QColor(240, 244, 249))
    palette.setColor(palette.WindowText, QColor(35, 35, 35))
    palette.setColor(palette.Base, QColor(255, 255, 255))
    palette.setColor(palette.AlternateBase, QColor(230, 235, 245))
    palette.setColor(palette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(palette.ToolTipText, QColor(35, 35, 35))
    palette.setColor(palette.Text, QColor(35, 35, 35))
    palette.setColor(palette.Button, QColor(240, 244, 249))
    palette.setColor(palette.ButtonText, QColor(35, 35, 35))
    palette.setColor(palette.BrightText, QColor(240, 60, 60))
    palette.setColor(palette.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = JunoApp()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

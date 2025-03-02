import streamlit as st
import os
import sys
import subprocess
import threading
import shutil
from pathlib import Path
import time

# App configuration and styling
st.set_page_config(
    page_title="Juno - Jupyter Environment Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve appearance
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .env-card {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .info-message {
        color: #17a2b8;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Default base directory for virtual environments
BASE_DIR = os.environ.get("JUNO_VENV_DIR", os.path.join(os.path.expanduser("~"), ".jupyter_venvs"))

# Create the base directory if it doesn't exist
os.makedirs(BASE_DIR, exist_ok=True)

# Session state to track operations
if 'operation_status' not in st.session_state:
    st.session_state.operation_status = None
if 'operation_message' not in st.session_state:
    st.session_state.operation_message = ""
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

def get_installed_packages(env_name):
    """Get list of installed packages in a virtual environment"""
    env_path = os.path.join(BASE_DIR, env_name)

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

def get_python_version(env_name):
    """Get Python version for a virtual environment"""
    env_path = os.path.join(BASE_DIR, env_name)

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
    except subprocess.CalledProcessError:
        return "Unknown"

def create_and_register_kernel(env_name, base_dir=BASE_DIR, additional_packages=None):
    """Create a virtual environment and register it as a Jupyter kernel"""
    # Validating the environment name
    if not env_name.isalnum() and not all(c.isalnum() or c == '_' for c in env_name):
        st.session_state.operation_status = "error"
        st.session_state.operation_message = "Environment name should only contain alphanumeric characters and underscores."
        return

    env_path = os.path.join(base_dir, env_name)
    if os.path.exists(env_path):
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Virtual environment '{env_name}' already exists at {env_path}."
        return

    try:
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)

        # Create the virtual environment
        subprocess.check_call([sys.executable, "-m", "venv", env_path])

        # Determine the python executable path for the new environment
        if os.name == "nt":
            python_executable = os.path.join(env_path, "Scripts", "python.exe")
            pip_executable = os.path.join(env_path, "Scripts", "pip.exe")
        else:
            python_executable = os.path.join(env_path, "bin", "python")
            pip_executable = os.path.join(env_path, "bin", "pip")

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

        st.session_state.operation_status = "success"
        st.session_state.operation_message = f"Virtual environment '{env_name}' created and registered as a Jupyter kernel successfully."

    except subprocess.CalledProcessError as e:
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Error occurred: {str(e)}"

        # Cleanup if environment was partially created
        if os.path.exists(env_path):
            try:
                shutil.rmtree(env_path)
            except:
                pass
    except Exception as e:
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Unexpected error: {str(e)}"

def install_packages(env_name, packages):
    """Install packages in a virtual environment"""
    env_path = os.path.join(BASE_DIR, env_name)

    if not os.path.exists(env_path):
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Virtual environment '{env_name}' does not exist."
        return

    if os.name == "nt":
        python_executable = os.path.join(env_path, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(env_path, "bin", "python")

    try:
        packages_list = [pkg.strip() for pkg in packages.split(',') if pkg.strip()]
        if not packages_list:
            st.session_state.operation_status = "error"
            st.session_state.operation_message = "No valid packages specified."
            return

        subprocess.check_call([
            python_executable, "-m", "pip", "install"] + packages_list
        )

        st.session_state.operation_status = "success"
        st.session_state.operation_message = f"Packages {', '.join(packages_list)} installed successfully in '{env_name}'."
    except subprocess.CalledProcessError as e:
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Error installing packages: {str(e)}"

def remove_kernel_and_env(env_name, base_dir=BASE_DIR):
    """Unregister a Jupyter kernel and remove the associated virtual environment"""
    env_path = os.path.join(base_dir, env_name)
    if not os.path.exists(env_path):
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Environment '{env_name}' does not exist at {env_path}."
        return

    try:
        # First try to uninstall the Jupyter kernel
        cmd = f"{sys.executable} -m jupyter kernelspec uninstall {env_name} -y"
        process = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True
        )

        # Even if kernel uninstallation fails, we'll still try to remove the environment
        kernel_removed = process.returncode == 0

        # Now remove the virtual environment directory
        if os.path.exists(env_path):
            shutil.rmtree(env_path)

        if kernel_removed:
            st.session_state.operation_status = "success"
            st.session_state.operation_message = f"Environment '{env_name}' and its kernel have been removed successfully."
        else:
            st.session_state.operation_status = "warning"
            st.session_state.operation_message = f"Environment '{env_name}' has been removed, but there may have been issues removing the kernel: {process.stderr}"

    except Exception as e:
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Error removing environment: {str(e)}"

def export_requirements(env_name):
    """Export requirements.txt from a virtual environment"""
    env_path = os.path.join(BASE_DIR, env_name)

    if not os.path.exists(env_path):
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Virtual environment '{env_name}' does not exist."
        return None

    if os.name == "nt":
        python_executable = os.path.join(env_path, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(env_path, "bin", "python")

    try:
        result = subprocess.run(
            [python_executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        st.session_state.operation_status = "error"
        st.session_state.operation_message = f"Error exporting requirements: {str(e)}"
        return None

def list_envs(base_dir=BASE_DIR):
    """List all virtual environments in the base directory"""
    if not os.path.exists(base_dir):
        return []
    return sorted([name for name in os.listdir(base_dir)
                  if os.path.isdir(os.path.join(base_dir, name))])

def run_creation(env_name, additional_packages=None):
    """Run environment creation in a separate thread"""
    thread = threading.Thread(
        target=create_and_register_kernel,
        args=(env_name,),
        kwargs={"additional_packages": additional_packages}
    )
    thread.start()
    # Wait a bit for the thread to complete
    time.sleep(0.5)

def run_removal(env_name):
    """Run environment removal in a separate thread"""
    thread = threading.Thread(target=remove_kernel_and_env, args=(env_name,))
    thread.start()
    # Wait a bit for the thread to complete
    time.sleep(0.5)

def run_install_packages(env_name, packages):
    """Run package installation in a separate thread"""
    thread = threading.Thread(target=install_packages, args=(env_name, packages))
    thread.start()
    # Wait a bit for the thread to complete
    time.sleep(0.5)

def refresh_envs():
    """Force refresh of environments list"""
    st.session_state.refresh_counter += 1

# Display banner/logo
st.title("🚀 Juno: JupyterLab Virtual Environment Manager")
st.write("""
Juno simplifies the management of Python virtual environments for JupyterLab.
Create, manage, and remove virtual environments that are registered as Jupyter kernels.
""")

# Show storage location
st.info(f"Virtual environments are stored at: **{BASE_DIR}**")

# Display status messages if any
if st.session_state.operation_status == "success":
    st.success(st.session_state.operation_message)
    st.session_state.operation_status = None
elif st.session_state.operation_status == "error":
    st.error(st.session_state.operation_message)
    st.session_state.operation_status = None
elif st.session_state.operation_status == "warning":
    st.warning(st.session_state.operation_message)
    st.session_state.operation_status = None

# Create two columns for layout
col1, col2 = st.columns([1, 2])

# Left column: Create new environment
with col1:
    st.header("Create Environment")

    with st.form(key="create_env_form"):
        env_name = st.text_input("Environment Name:",
                               help="Enter a name for your virtual environment. Use only alphanumeric characters and underscores.")

        additional_packages = st.text_input("Additional Packages (comma-separated):",
                                        help="List any additional packages to install, separated by commas (e.g., numpy,pandas,matplotlib).")

        submit_button = st.form_submit_button(label="Create Environment")

        if submit_button:
            if not env_name or not env_name.strip():
                st.error("Please provide a valid environment name.")
            else:
                run_creation(env_name.strip(), additional_packages)
                refresh_envs()

# Right column: List environments
with col2:
    st.header("Manage Environments")

    if st.button("Refresh Environment List"):
        refresh_envs()

    # Get the list of environments
    envs = list_envs()

    if not envs:
        st.write("No virtual environments found.")
    else:
        # Create tabs for different management operations
        tabs = st.tabs(["View & Remove", "Install Packages", "Export Requirements", "Advanced Options"])

        # Tab 1: View and Remove environments
        with tabs[0]:
            for env in envs:
                with st.container():
                    # Create a card-like appearance for each environment
                    st.markdown(f"<div class='env-card'>", unsafe_allow_html=True)

                    env_path = os.path.join(BASE_DIR, env)
                    python_version = get_python_version(env)

                    # Display environment details
                    col_info, col_actions = st.columns([3, 1])

                    with col_info:
                        st.markdown(f"#### {env}")
                        st.text(f"Path: {env_path}")
                        st.text(f"Python: {python_version}")

                    with col_actions:
                        # Remove button
                        if st.button("Remove", key=f"remove_{env}"):
                            if st.session_state.get(f"confirm_remove_{env}", False):
                                run_removal(env)
                                refresh_envs()
                                st.session_state[f"confirm_remove_{env}"] = False
                            else:
                                st.session_state[f"confirm_remove_{env}"] = True

                        # Show confirmation if needed
                        if st.session_state.get(f"confirm_remove_{env}", False):
                            st.warning(f"Are you sure you want to remove '{env}'?")
                            # Use buttons side by side without nested columns
                            if st.button("Yes", key=f"yes_remove_{env}"):
                                run_removal(env)
                                refresh_envs()
                                st.session_state[f"confirm_remove_{env}"] = False
                            if st.button("No", key=f"no_remove_{env}"):
                                st.session_state[f"confirm_remove_{env}"] = False

                    st.markdown("</div>", unsafe_allow_html=True)
                    st.write("")  # Add some spacing

        # Tab 2: Install Packages
        with tabs[1]:
            selected_env = st.selectbox("Select Environment:", envs, key="install_env_select")

            with st.form(key="install_packages_form"):
                packages = st.text_input("Packages to Install (comma-separated):",
                                      help="List packages to install, separated by commas (e.g., numpy,pandas,matplotlib).")

                submit_install = st.form_submit_button(label="Install Packages")

                if submit_install:
                    if not packages or not packages.strip():
                        st.error("Please specify at least one package to install.")
                    else:
                        run_install_packages(selected_env, packages)
                        refresh_envs()

            # Show currently installed packages
            if st.checkbox("Show Installed Packages", key="show_packages"):
                packages = get_installed_packages(selected_env)
                if packages:
                    st.code("\n".join(packages), language="text")
                else:
                    st.warning("Unable to retrieve package list.")

        # Tab 3: Export Requirements
        with tabs[2]:
            export_env = st.selectbox("Select Environment:", envs, key="export_env_select")

            if st.button("Export requirements.txt"):
                requirements = export_requirements(export_env)
                if requirements is not None:
                    # Create a download button for the requirements file
                    st.download_button(
                        label="Download requirements.txt",
                        data=requirements,
                        file_name="requirements.txt",
                        mime="text/plain"
                    )

                    # Also display the requirements
                    st.code(requirements, language="text")
                    
        # Tab 4: Advanced Options
        with tabs[3]:
            st.subheader("Environment Settings")
            
            st.write("Configure advanced settings for your Jupyter environments.")
            
            custom_base_dir = st.text_input(
                "Custom Base Directory:", 
                value=BASE_DIR,
                help="Change the base directory where virtual environments are stored."
            )
            
            if st.button("Update Base Directory"):
                if os.path.exists(custom_base_dir):
                    st.session_state.operation_status = "success"
                    st.session_state.operation_message = f"Base directory updated to: {custom_base_dir}"
                    # This would require restarting the app to take effect
                    st.info("Please restart the application for changes to take effect.")
                else:
                    st.session_state.operation_status = "error"
                    st.session_state.operation_message = f"Directory does not exist: {custom_base_dir}"

# Footer
st.markdown("---")
st.markdown("""
Juno: JupyterLab Virtual Environment Manager |
[GitHub](https://github.com/velocitatem/juno) |
MIT License
""")

# Help section in sidebar
with st.sidebar:
    st.header("Help")

    with st.expander("About Juno"):
        st.write("""
        Juno is a lightweight Streamlit-based application designed to simplify the management of
        Python virtual environments for JupyterLab. Inspired by NASA's Juno mission, this tool helps
        you create, list, and remove virtual environments that are registered as Jupyter kernels.
        """)

    with st.expander("How to Use"):
        st.write("""
        1. **Create Environment:** Enter a name and optional packages, then click 'Create Environment'.
        2. **View Environments:** All environments are listed in the 'Manage Environments' section.
        3. **Remove Environment:** Click the 'Remove' button next to an environment to delete it.
        4. **Install Packages:** Use the 'Install Packages' tab to add packages to an existing environment.
        5. **Export Requirements:** Export requirements.txt from any environment.
        """)

    with st.expander("Troubleshooting"):
        st.write("""
        - **Missing Jupyter:** Make sure Jupyter is installed on your system.
        - **Permission Issues:** Ensure you have write permissions to the environment directory.
        - **Kernel Not Showing:** Restart JupyterLab after creating a new environment.
        - **Remove Failures:** If an environment fails to remove, try restarting the application.
        """)

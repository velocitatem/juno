import streamlit as st
import os
import sys
import subprocess
import threading
import shutil

# Default base directory for virtual environments
BASE_DIR = os.environ.get("JUNO_VENV_DIR", os.path.join(os.path.expanduser("~"), ".jupyter_venvs"))

def create_and_register_kernel(env_name, base_dir=BASE_DIR):
    env_path = os.path.join(base_dir, env_name)
    if os.path.exists(env_path):
        st.error(f"Virtual environment '{env_name}' already exists at {env_path}.")
        return

    os.makedirs(base_dir, exist_ok=True)
    st.info(f"Creating virtual environment '{env_name}' at {env_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", env_path])
    except subprocess.CalledProcessError as e:
        st.error(f"Error creating virtual environment: {e}")
        return

    # Determine the correct python executable for the new virtual environment
    if os.name == "nt":
        python_executable = os.path.join(env_path, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(env_path, "bin", "python")

    st.info("Upgrading pip and installing ipykernel...")
    try:
        subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip", "ipykernel"])
    except subprocess.CalledProcessError as e:
        st.error(f"Error installing ipykernel: {e}")
        return

    st.info("Registering the new kernel with Jupyter...")
    try:
        subprocess.check_call([
            python_executable, "-m", "ipykernel", "install",
            "--user",
            "--name", env_name,
            "--display-name", f"Python ({env_name})"
        ])
    except subprocess.CalledProcessError as e:
        st.error(f"Error registering the kernel: {e}")
        return

    st.success(f"Kernel for virtual environment '{env_name}' registered successfully.")

def remove_kernel_and_env(env_name, base_dir=BASE_DIR):
    env_path = os.path.join(base_dir, env_name)
    if not os.path.exists(env_path):
        st.error(f"Environment '{env_name}' does not exist at {env_path}.")
        return

    st.info(f"Uninstalling Jupyter kernel '{env_name}'...")
    try:
        # Note the changed order: --user and --force come before the kernel n00ame.
        print(f"{sys.executable} -m jupyter kernelspec uninstall {env_name} -y")
        cmd = f"{sys.executable} -m jupyter kernelspec uninstall {env_name} -y"
        # send y to confirm in the shell
        subprocess.check_call(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    except subprocess.CalledProcessError as e:
        st.error(f"Error uninstalling kernel: {e}")
        return

    st.info(f"Removing virtual environment directory for '{env_name}'...")
    try:
        shutil.rmtree(env_path)
    except Exception as e:
        st.error(f"Error removing virtual environment directory: {e}")
        return

    st.success(f"Environment '{env_name}' and its kernel have been removed.")

def list_envs(base_dir=BASE_DIR):
    if not os.path.exists(base_dir):
        return []
    return sorted([name for name in os.listdir(base_dir)
                   if os.path.isdir(os.path.join(base_dir, name))])

def run_creation(env_name):
    thread = threading.Thread(target=create_and_register_kernel, args=(env_name,))
    thread.start()

def run_removal(env_name):
    thread = threading.Thread(target=remove_kernel_and_env, args=(env_name,))
    thread.start()

st.title("JupyterLab Virtual Environment Manager")

st.header("Create a New Virtual Environment")
env_name = st.text_input("Enter the name for the new virtual environment (and kernel):")

if st.button("Create Virtual Environment"):
    if env_name.strip() == "":
        st.error("Please provide a valid environment name.")
    else:
        run_creation(env_name)
        st.info("Creation process started. Refresh the list below in a few seconds.")

st.header("Existing Virtual Environments")
refresh = st.button("Refresh List")
envs = list_envs()
if envs:
    for env in envs:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(env)
        with col2:
            if st.button("Remove", key=f"remove_{env}"):
                run_removal(env)
                st.info(f"Removal process for '{env}' started. Refresh the list in a few seconds.")
else:
    st.write("No virtual environments found.")


# interactive shell for a selected env:
selected_env = st.selectbox("Select an environment to launch an interactive shell:", envs)
if selected_env:
    if st.button("Launch Shell"):
        st.info(f"Launching an interactive shell for environment '{selected_env}'...")
        if os.name == "nt":
            cmd = f"{os.path.join(BASE_DIR, selected_env, 'Scripts', 'activate')}"
        else:
            cmd = f"source {os.path.join(BASE_DIR, selected_env, 'bin', 'activate')}"
        st.code(cmd)

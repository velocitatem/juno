# Juno: Jupyter Virtual Environment Manager

Juno is a lightweight Streamlit-based application designed to simplify the management of Python virtual environments for JupyterLab. Inspired by NASA’s Juno mission, this tool helps you create, list, and remove virtual environments that are registered as Jupyter kernels, making it easier to work with multiple Python environments within JupyterLab.

## Features

- **Create Virtual Environments:**
  Easily create new Python virtual environments and automatically register them as Jupyter kernels.

- **List Existing Environments:**
  View all virtual environments that have been created using the app.

- **Remove Environments:**
  Unregister the corresponding Jupyter kernel and remove the virtual environment when it’s no longer needed.

- **Customizable Storage:**
  Configure the directory where virtual environments are stored via an environment variable.

## Prerequisites

- Python 3.7 or later
- [Streamlit](https://streamlit.io/)
- [Jupyter](https://jupyter.org/) (for registering kernels)
- [ipykernel](https://pypi.org/project/ipykernel/)

## Installation

1. **Clone the repository (if applicable) or download `main.py`:**

   ```bash
   git clone https://github.com/yourusername/juno-venv-manager.git
   cd juno-venv-manager
   ```

2. **Install dependencies:**

   Create a virtual environment (if desired) and install the required packages:

   ```bash
   pip install streamlit jupyter ipykernel
   ```

3. **(Optional) Set the Virtual Environments Directory:**
   By default, Juno stores virtual environments in `~/.jupyter_venvs`. To change this, set the `JUNO_VENV_DIR` environment variable. For example:

   ```bash
   export JUNO_VENV_DIR=/path/to/your/venv_directory
   ```

## Usage

1. **Run the App:**

   From the command line, run:

   ```bash
   streamlit run main.py
   ```

2. **Using the Interface:**

   - **Create a New Virtual Environment:**
     Enter the desired name for your new environment and click the "Create Virtual Environment" button. The app will create the environment, install/upgrades `pip` and `ipykernel`, and register it as a Jupyter kernel (displayed as `Python (env_name)` in JupyterLab).

   - **View Existing Virtual Environments:**
     The app displays a list of currently managed virtual environments.

   - **Remove an Environment:**
     To remove an environment, click the "Remove" button next to its name. This will uninstall the associated Jupyter kernel and delete the virtual environment directory.

3. **Launch a Kernel in JupyterLab:**
   Once an environment is created and registered, you can select it in JupyterLab when starting a new notebook or changing the kernel for an existing notebook.

## Important Notes

- **Kernel Registration:**
  Activating a virtual environment (e.g., using `source /path/to/venv/bin/activate`) does not automatically register it with JupyterLab. Juno takes care of registration by running the `ipykernel install` command after creating the environment.

- **Persistence:**
  Make sure that the virtual environments directory (default or set via `JUNO_VENV_DIR`) is persistent across sessions if you plan to use these environments over time.

- **Permissions:**
  Ensure that your user has the necessary permissions to create directories, execute Python commands, and write to the kernelspec directory used by Jupyter.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have ideas or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

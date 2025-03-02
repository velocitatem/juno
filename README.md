![banner](./banner.svg)

# Juno: JupyterLab Virtual Environment Manager

Juno is a desktop application designed to simplify the management of Python virtual environments for JupyterLab. This tool helps you create, manage, and remove virtual environments that are registered as Jupyter kernels, making it easier to work with multiple Python environments within JupyterLab.

## Features

- **Create Virtual Environments:**
  Easily create new Python virtual environments and automatically register them as Jupyter kernels.

- **Manage Existing Environments:**
  View details about all environments created with Juno.

- **Install Packages:**
  Add new packages to existing environments directly from the interface.

- **Export Requirements:**
  Generate and save requirements.txt files from your environments.

- **Remove Environments:**
  Unregister Jupyter kernels and remove virtual environments when no longer needed.

- **Customizable Storage:**
  Configure the directory where virtual environments are stored.

## Prerequisites

- Python 3.7 or later
- PyQt5
- Jupyter (for registering kernels)
- ipykernel

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/juno.git
   cd juno
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Set the Virtual Environments Directory:**
   By default, Juno stores virtual environments in `~/.jupyter_venvs`. To change this, set the `JUNO_VENV_DIR` environment variable:

   ```bash
   export JUNO_VENV_DIR=/path/to/your/venv_directory
   ```

## Usage

1. **Run the Application:**

   From the command line, run:

   ```bash
   python main.py
   ```

2. **Using the Interface:**

   - **Create a New Environment:**
     Enter a name for your environment, optionally specify additional packages, and click "Create Environment".

   - **View & Remove Environments:**
     Select an environment from the list to view its details, then use the "Remove" button to delete it if needed.

   - **Install Packages:**
     Choose an environment, enter package names separated by commas, and click "Install Packages".

   - **Export Requirements:**
     Generate a requirements.txt file from any environment, which can be saved to your filesystem.

   - **Settings:**
     Change the base directory where environments are stored.

3. **Use in JupyterLab:**
   After creating environments with Juno, they will appear in JupyterLab's kernel selection menu when starting a new notebook or changing kernels.

## Important Notes

- **Kernel Registration:**
  Juno handles the registration of environments with JupyterLab by running the `ipykernel install` command automatically.

- **Permissions:**
  Ensure your user has the necessary permissions to create directories, execute Python commands, and write to the kernelspec directory used by Jupyter.

- **Python Version:**
  Environments are created using the Python version that is running Juno.

## Troubleshooting

- **Missing Jupyter:** Make sure Jupyter is installed in your system Python environment.
- **Permission Issues:** Ensure you have write permissions to the environments directory.
- **Kernel Not Showing:** Restart JupyterLab after creating a new environment if it doesn't appear immediately.

## License

This project is licensed under the MIT License.
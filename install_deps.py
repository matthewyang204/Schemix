import os

# Get variables
pyqtdarktheme_wheel = os.path.join("wheels", "pyqtdarktheme-2.1.0-py3-none-any.whl")

# Install dependencies
os.system("pip install -r requirements.txt")
os.system(f"pip install {pyqtdarktheme_wheel}")
import subprocess
import sys
import os
import platform

def run_pyinstaller():
    try:
        main_script = os.path.join('schemix', 'main.py')

        # PyInstaller command to build the executable
        if platform.system() == 'Darwin':
            cmd = [
                'pyinstaller',
                main_script,
                '-w',  # Makes it windowed
                '--name', '"Schemix"',
                '--icon=icon.ico'
            ]
        else:
            cmd = [
                'pyinstaller',
                main_script,
                '--onedir',  # Create a single folder
                '-w',  # Makes it windowed
                '--icon=icon.ico'
            ]

        # Run PyInstaller
        subprocess.check_call(cmd)

        print("Build successful.")
    except Exception as e:
        print(f"Build failed: {e}")


if __name__ == '__main__':
    run_pyinstaller()

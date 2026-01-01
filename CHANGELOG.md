# Changelog

## 2026 New Year Release v1.1.1
- Fix newer versions of `numpy` breaking launch due to dependency problems
- Replace `tk`-based open/select/create board dialog with native Qt-based dialog to avoid mixing widget kits
    - This also fixes macOS support
- Fix Finder not being able to find the directory due to an unescaped space
- Create an `About` dialog to show settings info
- Add `About` and `Settings` to `Help` menu
    - On macOS, it shows up under the application name due to macOS conventions about rearranging menu items

## v1.1.0
- Use a custom pyqtgraph 2.x wheel to avoid problems with missing setup theme functions
- New build system complete with Windows installers and Linux `.desktop` files
- Now displays icon correctly
- Remove some binaries from the source tree that were accidentally committed
- Adds in a few dialogues created by tk
- New board selection dialogue that shows existing boards
- Improve the calculator by handling invalid characters
- Calculator also now shows the full error and not just `Error:`
- Refactor the calculator code
- Allow the user to enter `pi` and other character sequences that are automatically expanded
- Add a `pi` button that does the same

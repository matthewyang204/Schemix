# Changelog

## v1.1.0
- Use custom pyqtgraph 2.x wheel to avoid problems with missing setup theme functions
- New build system complete with Windows installers and Linux `.desktop` files
- Now displays icon correctly
- Remove some binaries from the source tree that were accidentally committed
- Adds in a few dialogs created by tk
- New board selection dialog that shows existing boards
- Improve the calculator by handling invalid characters
- Calculator also now shows the full error and not just `Error:`
- Refactor the calculator code
- Allow user to enter `pi` and other character sequences that are automatically expanded
- Add `pi` button that does same
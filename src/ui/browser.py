'''
File Browser Component
======================
This module provides the ``FileBrowser`` class, which utilizes the `questionary`
library to render an interactive, terminal-based file navigation interface. It
allows users to traverse the local filesystem and select specific files filtered
by extension.
'''
import os
import questionary
from typing import cast

class FileBrowser:
    '''
    Provide interactive file browser using questionary.

    :cvar icons: Dictionary mapping item types to their corresponding terminal icon strings.
    :vartype icons: dict[str, str]
    :ivar _extensions: Tuple of allowed file extensions.
    :vartype _extensions: tuple[str, ...]
    :ivar _items: Cached list of all directory items.
    :vartype _items: list[str] | None
    :ivar _folders: Cached list of folder names.
    :vartype _folders: list[str] | None
    :ivar _files: Cached list of file names filtered by allowed extensions.
    :vartype _files: list[str] | None
    :ivar _choices: Cached list of questionary Choice strings.
    :vartype _choices: list[str] | None
    :ivar _cd: Absolute path to the currently active directory.
    :vartype _cd: str
    '''
    icons: dict[str, str] = {
        'file': '🖹',
        'exit': '⪩',
        'folder': '🖿'
    }

    def __init__(self, path: str, extensions: tuple[str, ...]) -> None:
        '''
        Initialize file browser instance.

        :param path: Initial directory path.
        :param extensions: Tuple of allowed file extensions.
        '''
        self._extensions: tuple[str, ...] = extensions
        self._items: list[str] | None = None
        self._folders: list[str] | None = None
        self._files: list[str] | None = None
        self._choices: list[str] | None = None
        self._cd: str = os.path.abspath(path)

    @property
    def cd(self) -> str:
        '''
        Get current directory path.

        :return: Current directory path string.
        '''
        return self._cd

    @cd.setter
    def cd(self, path: str) -> None:
        '''
        Set current directory path and clear cached items.

        :param path: New directory path.
        '''
        self._items = None
        self._folders = None
        self._files = None
        self._choices = None
        self._cd = os.path.abspath(path)

    @property
    def extensions(self) -> tuple[str, ...]:
        '''
        Get allowed file extensions.

        :return: Tuple of extension strings.
        '''
        return self._extensions

    @property
    def items(self) -> list[str]:
        '''
        Get all items in current directory.

        :return: List of item names.
        '''
        if self._items is None:
            try:
                self._items = os.listdir(self.cd)
            except PermissionError:
                self._items = []
        return self._items

    @property
    def files(self) -> list[str]:
        '''
        Get filtered files in current directory.

        :return: List of file names.
        '''
        if self._files is None:
            self._categorize_items()
        return cast(list[str], self._files)

    @property
    def folders(self) -> list[str]:
        '''
        Get folders in current directory.

        :return: List of folder names.
        '''
        if self._folders is None:
            self._categorize_items()
        return cast(list[str], self._folders)

    @property
    def choices(self) -> list[str]:
        '''
        Get menu choices for questionary.

        :return: List of choice strings.
        '''
        if self._choices is None:
            self._choices = [f'{type(self).icons['folder']} ..']
            self._choices.extend((f'{type(self).icons['folder']} {f}' for f in self.folders))
            self._choices.extend((f'{type(self).icons['file']} {f}' for f in self.files))
            self._choices.append(f'{type(self).icons['exit']} Cancel')
        return self._choices

    def _categorize_items(self) -> None:
        '''
        Categorize items into folders and filtered files.
        '''
        self._files = []
        self._folders = []
        # Loop through items
        for item in self.items:
            path = os.path.join(self.cd, item)
            # Check whether its a dir
            if os.path.isdir(path):
                self._folders.append(item)
            # Check whether its a file
            elif os.path.isfile(path):
                _, ext = os.path.splitext(item)
                # Filter by extensions
                if ext in self.extensions:
                    self._files.append(item)
        self._files.sort()
        self._folders.sort()

    def up(self) -> None:
        '''
        Navigate to parent directory.
        '''
        self.cd = os.path.dirname(self.cd)

    def into(self, directory: str) -> None:
        '''
        Navigate into child directory.

        :param directory: Target directory name.
        '''
        self.cd = os.path.join(self.cd, directory)

    def run(self) -> str | None:
        '''
        Execute interactive file browser loop.

        .. note::
           This method takes control of the terminal until the user makes a
           valid selection or chooses to cancel the prompt.

        :return: Selected file path or None if cancelled.
        :rtype: str | None
        '''
        while True:
            opt = cast(
                str,
                questionary.select(
                    (
                        f'╭─Current: {self.cd}\n'
                        f' ╰─λ Select file:'
                    ), qmark='', instruction=' ',
                    choices=self.choices
                ).ask()
            )

            match opt[2:]:
                case '..': self.up()
                case 'Cancel': return None
                case folder if folder in self.folders: self.into( folder)
                case file if file in self.files: return os.path.join(self.cd, file)
                case _: pass

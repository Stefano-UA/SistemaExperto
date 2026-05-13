'''
Interactive checkbox chooser module.
'''
import questionary
from typing import Any, cast
from questionary import Choice
from rich.console import Console

class Chooser:
    '''
    Interactive checkbox chooser for selecting items from a list.
    '''
    def __init__(self, min_n: int, max_n: int, choices: tuple[dict[str, Any], ...], console: Console) -> None:
        '''
        Initialize the Chooser.

        :param min_n: Minimum number of items that must be selected.
        :param max_n: Maximum number of items that can be selected.
        :param choices: Tuple of dictionaries containing choice parameters (e.g., title, value).
        :param console: Rich console instance for rendering.
        '''
        self._min_n: int = min_n
        self._max_n: int = max_n
        self._choices: tuple[dict[str, Any], ...] = choices
        self._console: Console = console

    def run(self) -> list[str] | None:
        '''
        Execute the interactive chooser.

        :return: List of selected values, or None if no valid selection was made.
        '''
        msg: str = f'Select at least {self._min_n} and up to {self._max_n} options:'
        if (self._min_n == self._max_n): msg = f'Select {self._min_n} options:'
        # Ask the user to choose
        results: list[str] = cast(
            list[str],
            questionary.checkbox(
                msg,
                choices=[Choice(**kwargs) for kwargs in self._choices], qmark='', instruction=' ',
                validate=lambda x: True if (self._min_n <= len(x) <= self._max_n) else f'You must select between {self._min_n} and {self._max_n} options.'
            ).ask()
        )
        return results if results else None
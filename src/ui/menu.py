'''
Interactive terminal menu.
'''
import questionary
from typing import cast
from questionary import Choice
from rich.console import Console, ConsoleRenderable

from data import Data
from inference.engines import BaseEngine
from .controller import Controller
from .display import Display

class Menu:
    '''
    Interactive menu for the application.

    :cvar options: Dictionary mapping display names of menu options to their corresponding Controller methods.
    :vartype options: dict[str, str]
    :cvar status_items: Dictionary mapping state keys to a tuple of display title and default value for the status bar.
    :vartype status_items: dict[str, tuple[str, str]]
    :ivar _console: Active Rich console instance.
    :vartype _console: Console
    :ivar _status: Dedicated Display instance for rendering the static status bar.
    :vartype _status: Display
    :ivar _rules: Dedicated Display instance for rendering loaded rules summary.
    :vartype _rules: Display
    :ivar _vars: Dedicated Display instance for rendering loaded variables summary.
    :vartype _vars: Display
    :ivar _output: Dedicated Display instance for ad-hoc command responses and warnings.
    :vartype _output: Display
    :ivar _controller: Central application Controller managing state logic.
    :vartype _controller: Controller
    '''
    options: dict[str, str] = {
        'Load Data': 'load_data',
        'Load Rules': 'load_rules',
        'Switch Engine': 'switch_engine',
        'Load Mappings': 'load_mappings',
        'Load Variables': 'load_variables',
        'Execute Inference': 'execute_inference',
        'Generate Visualizations': 'generate_visualizations',
        'Save Results': 'save_results'
    }

    status_items: dict[str, tuple[str, str]] = {
        'data': ('Data', 'No'),
        'rules': ('Rules', 'No'),
        'mappings': ('Mappings', 'No'),
        'variables': ('Variables', 'No'),
        'engine': ('Engine', 'None')
    }

    def __init__(self) -> None:
        '''
        Initialize the Menu.
        '''
        self._console: Console = Console()
        self._status: Display = Display('System Status', self._console)
        self._rules: Display = Display('Loaded Rules', self._console)
        self._vars: Display = Display('Loaded Variables', self._console)
        self._output: Display = Display('Command Output', self._console)
        self._controller: Controller = Controller(self._console, self._output)

    @property
    def state(self) -> dict[str, str | type[BaseEngine] | None]:
        '''
        Get the current application state.

        :return: State dictionary.
        '''
        return self._controller.state

    @property
    def data(self) -> Data:
        '''
        Get the underlying data container.

        :return: Data container instance.
        '''
        return self._controller.data

    def _display_status(self) -> None:
        '''
        Display status bar with current system state.
        '''
        status: list[str] = []
        # Loop through status items
        for key, values in type(self).status_items.items():
            # Get title and default value
            title, default = values
            # Get value, falling back to default
            value: str | type[BaseEngine] | None = self.state.get(key, default)
            # Engine key is a special case
            if (key == 'engine') and not isinstance(value, str | None):
                value = value.__name__
            status.append(f'[bold magenta]{title}:[/bold magenta] {value}')
        # Set and show, to always show
        self._status.set('\n'.join(status))
        self._status.show()
        # Show rules, if any
        if self.state.get('rules'):
            rules: list[str] = []
            for rule in self.data.rules:
                rules.append(f'[bold yellow]{rule}[/bold yellow]')
            if (len(rules) > 0):
                # Set and show, to always show, if we get here
                self._rules.set('\n'.join(rules))
                self._rules.show()
        # Show variables, if any
        if self.state.get('variables'):
            vars: list[str] = []
            for var in self.data.variables.values():
                vars.append(f'[bold green]{var}[/bold green]')
            if (len(vars) > 0):
                # Set and show, to always show, if we get here
                self._vars.set('\n'.join(vars))
                self._vars.show()

    def _check_availability(self, opt: str) -> str | None:
        '''
        Check if an option is available.

        :param opt: Option name.
        :return: Motive for unavailability if unavailable else None.
        '''
        match opt:
            case 'Execute Inference':
                # If no data we cannot do inference
                if (self.state.get('data') is None):
                    return 'Needs data loaded'
                # If FuzzyEngine we need both rules and variables loaded
                if (getattr(self.state.get('engine'), '__name__', '') == 'FuzzyEngine'):
                    if not (self.state.get('rules') and self.state.get('variables')):
                        return 'Needs engines and rules loaded'
            case 'Generate Visualizations':
                # We need some results to make visualizations
                if (len(self.data.results) == 0):
                    return 'No results in memory'
            case 'Save Results':
                # We need some results to make visualizations
                if (len(self.data.results) == 0):
                    return 'No results in memory'
            case _: return None
        return None

    def cls(self) -> None:
        '''
        Clear the console screen.
        '''
        self._console.clear()

    def echo(self, string: str | ConsoleRenderable='') -> None:
        '''
        Print to the console.

        :param string: String to print.
        '''
        self._console.print(string)

    def read(self, prompt: str='') -> str:
        '''
        Read input from the console.

        :param prompt: Input prompt.
        :return: User input.
        '''
        return self._console.input(prompt)

    def run(self) -> int:
        '''
        Execute interactive main menu loop.

        :return: Exit status code.
        '''
        while True:
            self.cls()
            # Display status and show output, if any
            self._display_status()
            self._output.show()
            self.echo()
            # Create the list of choices
            choices: list[Choice] = []
            # Loop through options
            for opt in type(self).options.keys():
                # Append choices, disabling if necessary
                choices.append(Choice(title=opt, value=opt, disabled=self._check_availability(opt)))
            choices.append(Choice(title='Exit', value='Exit'))
            # Ask for an option
            opt = cast(
                str,
                questionary.select(
                'Fuzzy Expert System - Main Menu:',
                    qmark='', instruction=' ',
                    choices=choices
                ).ask()
            )
            self.echo()
            # Exit action
            if (opt == 'Exit'):
                self.echo('[bold green]Exiting...[/bold green]')
                return 0
            # Call related action on controller
            getattr(self._controller, type(self).options[opt])()
            # New line and pause
            self.echo()
            _ = self.read('[dim]Press ENTER to continue...[/dim]')
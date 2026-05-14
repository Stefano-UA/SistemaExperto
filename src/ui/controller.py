'''
Application Controller
======================
This module defines the central ``Controller`` responsible for orchestrating the
application's primary workflow. It acts as the mediator between the interactive
terminal views (Menu, Browser, Display) and the backend logic (Data, Inference
Engines), ensuring state consistency and managing the execution lifecycle.
'''
import os
from typing import cast
from pathlib import Path
from rich.console import Console
from collections.abc import Callable

from data import Data
from visualization.plotters import Plotter
from inference.engines import BaseEngine, MBIEngine, FuzzyEngine
from .chooser import Chooser
from .display import Display
from .browser import FileBrowser
from .progress import ProgressBar

class Controller:
    '''
    Controller orchestrating the application flow.

    :cvar engines: Tuple of available BaseEngine subclasses that can be dynamically swapped.
    :vartype engines: tuple[type[BaseEngine], ...]
    :ivar _data: The central Data container tracking all parsed values.
    :vartype _data: Data
    :ivar _display: System-wide display controller for rendering outputs.
    :vartype _display: Display
    :ivar _progressbar: System-wide progress bar utility for long-running inferences.
    :vartype _progressbar: ProgressBar
    :ivar _engine: Index representing the currently active evaluation engine.
    :vartype _engine: int
    :ivar _browsers: Dictionary mapping domain file types to their FileBrowser prompts.
    :vartype _browsers: dict[str, FileBrowser]
    :ivar _state: Application state dictionary accessible across the UI layer.
    :vartype _state: dict[str, str | type[BaseEngine] | None]
    '''
    engines: tuple[type[BaseEngine], ...] = (MBIEngine, FuzzyEngine)

    def __init__(self, console: Console, display: Display) -> None:
        '''
        Initialize the Controller.

        :param display: Display instance for showing output messages.
        '''
        self._data: Data = Data()
        # Output console
        self._console: Console = console
        # Output display
        self._display: Display = display
        # Output progress bar
        self._progressbar: ProgressBar = ProgressBar()
        # Engine index
        self._engine: int = 0
        # File browsers for each kind of loading
        self._browsers: dict[str, FileBrowser] = {
            'data': FileBrowser(os.getenv('DATAPATH', '.'), ('.csv',)),
            'rules': FileBrowser(os.getenv('DATAPATH', '.'), ('.rules',)),
            'mappings': FileBrowser(os.getenv('DATAPATH', '.'), ('.map',)),
            'variables': FileBrowser(os.getenv('DATAPATH', '.'), ('.vars',))
        }
        # State of the controller, accessed by menu
        self._state: dict[str, str | type[BaseEngine] | None] = {
            'data': None,
            'rules': None,
            'mappings': None,
            'variables': None,
            'engine': self.engines[self._engine]
        }

    @property
    def state(self) -> dict[str, str | type[BaseEngine] | None]:
        '''
        Get current application state.

        :return: State dictionary.
        '''
        return self._state

    @property
    def data(self) -> Data:
        '''
        Get the data container.

        :return: Data container instance.
        '''
        return self._data

    def _load(self, type_name: str, func: str) -> bool:
        '''
        Generic file loading handler.

        :param type_name: Key type of the file being loaded.
        :param func: Function name in the Data container to execute.
        :return: True if successfully loaded or cancelled, False if failed.
        '''
        # Run interactive file browser
        path = self._browsers[type_name].run()
        if not path: return True # User cancelled
        # Load chosen path as func
        state: bool = cast(
            Callable[[str], bool],
            getattr(self._data, func)
        )(path)
        # Set state and output according to load result
        if state:
            self._display.set('Loaded successfully', 'success')
            self.state[type_name] = os.path.basename(path)
        else:
            self._display.set('Failed to load', 'error')
            self.state[type_name] = None
        return state

    def load_data(self) -> bool:
        '''
        Load data into the container.

        :return: True if successful, False otherwise.
        '''
        return self._load('data', 'load_csv')

    def load_mappings(self) -> bool:
        '''
        Load mapping into the container.

        :return: True if successful, False otherwise.
        '''
        return self._load('mappings', 'load_map')

    def load_rules(self) -> bool:
        '''
        Load fuzzy rules from a .rules file.

        :return: True if successful, False otherwise.
        '''
        return self._load('rules', 'load_rules')

    def load_variables(self) -> bool:
        '''
        Load fuzzy variables from a .vars file.

        :return: True if successful, False otherwise.
        '''
        return self._load('variables', 'load_vars')

    def switch_engine(self) -> None:
        '''
        Switch between available inference engines.
        '''
        self._engine = (self._engine + 1) % len(self.engines)
        self._state['engine'] = self.engines[self._engine]
        self._display.set(f'Switched engine to {self._state['engine'].__name__}', 'success')

    def execute_inference(self) -> None:
        '''
        Execute inference on loaded data.
        '''
        # Get engine instance to use
        engine: BaseEngine = cast(type[BaseEngine], self.state['engine'])()
        # Get progress bar context
        with self._progressbar as pg:
            # Set task in the progress bar
            taskid = pg.add_task("[cyan]Processing rows...", total=len(self._data.data))
            # Function to update task progress and total
            def progress_fn(current: int, total: int) -> None:
                if (pg.tasks[taskid].total != total):
                    pg.update(taskid, total=total)
                pg.update(taskid, completed=current)
            # Evaluate results
            engine.evaluate(self._data, progress_fn=progress_fn)

    def generate_visualizations(self) -> None:
        '''
        Generate and save configured visualizations.
        '''
        # Get results choices available
        choices: tuple[dict[str, str], ...] = tuple([{'title': id, 'value': id} for id in self._data.results.keys()])
        # Ask user to select one or two results from the list
        selected: list[str] | None = Chooser(1, 2, choices, self._console).run()
        self._console.print('') # Add newline after choosing options
        if (selected is None): return
        # Initialize plotter to plot data
        plotter: Plotter = Plotter(self._data)
        out: str = os.getenv('VISOUT', './visuals')
        # Get progress bar context
        with self._progressbar as pg:
            # Plot depending on selected results
            if (len(selected) == 1):
                key: str = selected[0]
                # Set task in the progress bar
                taskid = pg.add_task("[cyan]Generating variable visualizations...", total=len(self._data.variables))
                # Function to update task progress and total
                def progress_fn_var(current: int, total: int) -> None:
                    if (pg.tasks[taskid].total != total):
                        pg.update(taskid, total=total)
                    pg.update(taskid, completed=current)
                # Plot variables
                plotter.plot_variables(out, progress_fn=progress_fn_var)
                # Set task in the progress bar
                taskid = pg.add_task("[cyan]Generating results visualizations...", total=len(self._data.results[key]))
                # Function to update task progress and total
                def progress_fn_results(current: int, total: int) -> None:
                    if (pg.tasks[taskid].total != total):
                        pg.update(taskid, total=total)
                    pg.update(taskid, completed=current)
                # Plot results
                plotter.plot_results(key, out, progress_fn=progress_fn_results)
                self._display.set(f'Visualizations generated in {out}/ for {key}.', 'success')
            elif (len(selected) == 2):
                key1, key2 = selected
                # Plot comparison
                plotter.plot_comparison(key1, key2, out)
                self._display.set(f'Comparative visualization generated in {out}/ for {key1} and {key2}.', 'success')

    def save_results(self) -> None:
        '''
        Save current runs from memory to disk.
        '''
        # Get output directory and ensure it exists
        out_dir: Path = Path(os.getenv('DATAPATH', '.')) / 'results'
        out_dir.mkdir(parents=True, exist_ok=True)
        # Get progress bar context
        with self._progressbar as pg:
            # Set task in the progress bar
            taskid = pg.add_task("[cyan]Saving results to csv...", total=len(self._data.results))
            # Init counter
            current = 0
            # Loop through results
            for key, result in self._data.results.items():
                # Store result as csv in output directory
                safe_key: str = key.replace('<', '').replace('>', '_')
                result.to_csv(out_dir / f'{safe_key}.csv')
                # Update progress bar
                pg.update(taskid, completed=current)
                current += 1
            # Update progress bar
            pg.update(taskid, completed=len(self._data.results))
            # Show message so the user know where the results where saved
            self._display.set(f'Results saved to {out_dir}/.', 'success')

'''
Progress Bar Utility
====================
This module provides a context manager for rendering an interactive progress bar
in the terminal. It leverages the rich library to display real-time progress
updates, spinners, and task completion metrics during long-running operations.
'''
from types import TracebackType
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, MofNCompleteColumn

class ProgressBar:
    '''
    Context manager for a Rich progress bar.
    '''
    def __init__(self) -> None:
        '''
        Initialize the ProgressBar instance.
        '''
        self._progress: Progress | None = None

    def __enter__(self) -> Progress:
        '''
        Enter the runtime context and start the progress bar.

        :return: Underlying Rich Progress instance.
        '''
        # Initialize progress bar
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn()
        ).__enter__()
        return self._progress

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool:
        '''
        Exit the runtime context and stop the progress bar.

        :param exc_type: Exception type if an exception was raised.
        :param exc_val: Exception value if an exception was raised.
        :param exc_tb: Traceback if an exception was raised.
        :return: False to propagate any exceptions.
        '''
        # Call progress bar exit
        assert(self._progress is not None)
        self._progress.__exit__(exc_type, exc_val, exc_tb)
        return False
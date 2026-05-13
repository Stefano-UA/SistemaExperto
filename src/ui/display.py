'''
Console display utility module.
'''
from rich.panel import Panel
from rich.console import Console, ConsoleRenderable

class Display:
    '''
    Console display manager for rendering messages, warnings, and panels.

    :cvar styles: Global dictionary mapping semantic types to rich styling parameters.
    :vartype styles: dict[str, dict[str, str]]
    :ivar _console: Active Rich console for rendering text.
    :vartype _console: Console
    :ivar _title: Optional title string for rendered panels.
    :vartype _title: str | None
    :ivar _type: Semantic type defining the current rendering style (e.g., 'error', 'success').
    :vartype _type: str
    :ivar _message: Content body to be displayed upon invocation.
    :vartype _message: str | None
    '''
    # Styles for the display
    styles: dict[str, dict[str, str]] = {
        'error': {'text': 'red', 'title': 'bold red', 'border': 'bold red'},
        'normal': {'text': 'blue', 'title': 'bold blue', 'border': 'bold blue'},
        'warning': {'text': 'orange', 'title': 'bold orange', 'border': 'bold orange'},
        'success': {'text': 'green', 'title': 'bold green', 'border': 'bold green'}
    }

    def __init__(self, title: str, console: Console):
        '''
        Initialize the Display instance.

        :param title: Title text for the display panels.
        :param console: Rich console instance used for rendering.
        '''
        self._type: str = 'normal'
        self._title: str | None = title
        self._message: str | None = None
        self._console: Console = console

    @property
    def style(self) -> dict[str, str]:
        '''
        Get the current style configuration.

        :return: Dictionary containing color specifications.
        '''
        return type(self).styles[self.type]

    @property
    def type(self) -> str:
        '''
        Get the active message type (e.g., error, normal).

        :return: String representing the message type.
        '''
        return self._type

    @type.setter
    def type(self, value: str) -> None:
        '''
        Set the active message type.

        :param value: Message type string. Must be a valid key in styles.
        '''
        if value in type(self).styles.keys():
            self._type = value

    def echo(self, string: str | ConsoleRenderable='') -> None:
        '''
        Print a raw string to the console.

        :param string: String to print.
        '''
        self._console.print(string)

    def set(self, message: str, type: str | None=None) -> None:
        '''
        Set a formatted message to be displayed later.

        Only the last set message will be displayed and
        messages will be displayed only once.

        :param message: Content of the message.
        :param type: Optional type for styling the message.
        '''
        self._message = message
        if not (type is None): self.type = type

    def show(self) -> None:
        '''
        Render the configured message, if any, inside a styled panel, then reset state.
        '''
        # Ignore show if nothing to show
        if (self._message is None): return
        # Show and clear data
        self.echo(
            Panel(
                f"[{self.style['text']}]{self._message}[/{self.style['text']}]",
                title=f"[{self.style['title']}]{self._title}[/{self.style['title']}]",
                border_style=self.style['border']
            )
        )
        self._message = None
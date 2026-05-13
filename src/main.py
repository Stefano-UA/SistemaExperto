'''
Application Entry Point
=======================
This module serves as the primary entry point for the Fuzzy Expert System.
It encapsulates the bootstrap logic required to instantiate the interactive
terminal Menu and delegates execution control to the UI package.
'''
from sys import exit

from ui import Menu

def main() -> None: # pragma: no cover
    '''
    Bootstrap and start the interactive terminal application.

    This function instantiates the root Menu component and hands over the
    main execution thread to its event loop, returning the final status code
    upon exit.
    '''
    exit(
        Menu().run()
    )

if (__name__ == '__main__'): main() # pragma: no cover
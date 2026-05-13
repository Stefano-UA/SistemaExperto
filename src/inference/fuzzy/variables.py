'''
Fuzzy Linguistic Variables
==========================
This module encapsulates the representation of fuzzy linguistic variables,
including their mathematically defined universe of discourse and associated
membership functions (e.g., 'low', 'high') used during fuzzification.
'''
import numpy as np
import skfuzzy as fuzz
from typing import cast, override

class Variable:
    '''
    Represent a linguistic fuzzy variable with membership functions.
    '''
    def __init__(self, name: str, universe: np.ndarray) -> None:
        '''
        Initialize the linguistic variable.

        :param name: Name of the variable.
        :param universe: Array representing the universe of discourse.
        '''
        self._name: str = name
        self._universe: np.ndarray = universe
        self._terms: dict[str, np.ndarray] = {}

    @property
    def name(self) -> str:
        '''
        Get variable name.
        '''
        return self._name

    @property
    def universe(self) -> np.ndarray:
        '''
        Get variable universe.
        '''
        return self._universe

    @property
    def terms(self) -> dict[str, np.ndarray]:
        '''
        Get variable terms.
        '''
        return self._terms

    @override
    def __str__(self) -> str:
        return f'{self.name}<{self.universe.min()}, {self.universe.max()}>: {tuple((term for term in self.terms.keys()))}'

    def add_term(self, term: str, membership_fn: np.ndarray) -> None:
        '''
        Add a linguistic term and its membership function.

        :param term: Name of the term (e.g., 'low', 'high').
        :param membership_fn: Array of membership values corresponding to the universe.
        '''
        self._terms[term] = membership_fn

    def fuzzify(self, values: float | np.ndarray) -> dict[str, np.ndarray]:
        '''
        Calculate membership degrees for input value.

        :param value: Input value or values to fuzzify.
        :return: Dictionary of term names to membership arrays.
        '''
        return {
            term: cast(np.ndarray, fuzz.interp_membership(self.universe, mf, values))
            for term, mf in self.terms.items()
        }

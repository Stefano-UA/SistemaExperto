'''
Fuzzy Logic Rules
=================
This module defines the ``Rule`` and ``ThenNode`` objects, which tie together
an antecedent (an AST of conditions) and a consequent (the resulting output term)
to compute final activation strengths using numpy array operations.
'''
import numpy as np
from typing import override

from .ast import BinaryOp, Node, BranchNode, LeafNode

OPERATORS: dict[str, BinaryOp] = {
    'THEN': np.fmin
}
'''Dictionary mapping consequent string operators to their underlying numpy aggregation functions.'''

class Rule:
    '''
    Represent a fuzzy IF-THEN rule.
    '''
    def __init__(self, antecedent: Node, consequent: LeafNode) -> None:
        '''
        Initialize the rule.

        :param antecedent: AST Node representing the IF part.
        :param consequent: AST Node representing the THEN part.
        '''
        self._antecedent: Node = antecedent
        self._consequent: LeafNode = consequent

    @property
    def antecedent(self) -> Node:
        '''
        Get the antecedent term.

        :return: Antecedent term Node.
        '''
        return self._antecedent

    @property
    def consequent(self) -> LeafNode:
        '''
        Get the consequent term.

        :return: Consequent term Node.
        '''
        return self._consequent

    @override
    def __str__(self) -> str:
        return f'IF {self.antecedent} THEN {self.consequent}'

    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate rule.

        :param context: Fuzzified input data.
        :return: Activation strength of the rule.
        '''
        return ThenNode(
            self._antecedent,
            self._consequent
        ).evaluate(context)

class ThenNode(BranchNode):
    '''
    Represent a fuzzy THEN operation.
    '''
    @override
    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate the fuzzy THEN operation using np.fmin.

        :param context: Dictionary containing data/context for evaluation.
        :return: Activation strength as a membership function.
        '''
        assert(self._right is not None)
        return OPERATORS['THEN'](
            self._left.evaluate(context),
            self._right.evaluate(context)
        )
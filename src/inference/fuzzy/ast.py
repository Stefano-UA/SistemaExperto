'''
AST for fuzzy rule evaluation.
'''
import numpy as np
from abc import ABC, abstractmethod
from typing import cast, override, Callable

type UnaryOp = Callable[[np.ndarray], np.ndarray]
'''Type alias for a unary operation over numpy arrays.'''

type BinaryOp = Callable[[np.ndarray, np.ndarray], np.ndarray]
'''Type alias for a binary operation over numpy arrays.'''

OPERATORS: dict[str, UnaryOp | BinaryOp] = {
    'OR': np.fmax, 'AND': np.fmin,
    'NOT': lambda vs: (1.0 - vs)
}
'''Dictionary mapping string identifiers to their corresponding logical numpy operations.'''

class Node(ABC):
    '''
    Abstract base class for all nodes in the evaluation tree.
    '''
    @abstractmethod
    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate the node given a context.

        :param context: Dictionary containing fuzzified data for evaluation.
        :type context: dict[str, dict[str, np.ndarray]]
        :return: Evaluation results.
        :rtype: np.ndarray
        '''
        pass

    def __and__(self, other: 'Node') -> 'Node':
        '''
        Overload the & operator to perform fuzzy AND.

        :param other: Node to perform AND with.
        :type other: Node
        :return: BranchNode representing the AND operation.
        :rtype: Node
        '''
        return AndNode(self, other)

    def __or__(self, other: 'Node') -> 'Node':
        '''
        Overload the | operator to perform fuzzy OR.

        :param other: Node to perform OR with.
        :type other: Node
        :return: BranchNode representing the OR operation.
        :rtype: Node
        '''
        return OrNode(self, other)

    def __invert__(self) -> 'Node':
        '''
        Overload the ~ operator to perform fuzzy NOT.

        :return: BranchNode representing the NOT operation.
        :rtype: Node
        '''
        return NotNode(self)

class LeafNode(Node):
    '''
    A leaf node representing a single fuzzy variable evaluation.

    :ivar _variable: Name of the variable in the context.
    :vartype _variable: str
    :ivar _term: Name of the membership function to evaluate.
    :vartype _term: str
    '''
    def __init__(self, variable: str, term: str) -> None:
        '''
        Initialize the LeafNode.

        :param variable: Name of the variable in the context.
        :type variable: str
        :param term: Name of the membership function to evaluate.
        :type term: str
        '''
        self._variable: str = variable
        self._term: str = term

    @override
    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate the leaf node by fetching membership from context.

        :param context: Dictionary containing evaluated memberships.
        :type context: dict[str, dict[str, np.ndarray]]
        :return: Membership value.
        :rtype: np.ndarray
        :raises KeyError: If the variable or term is not found in the context.
        '''
        return context[self._variable][self._term]

    @override
    def __str__(self) -> str:
        return f'{self._variable} IS {self._term}'

class BranchNode(Node, ABC):
    '''
    Branch node representing a logical operation between nodes.

    :ivar _left: Left child node.
    :vartype _left: Node
    :ivar _right: Optional right child node.
    :vartype _right: Node | None
    '''
    def __init__(self, left: Node, right: Node | None=None) -> None:
        '''
        Initialize BranchNode.

        :param left: Left child node.
        :type left: Node
        :param right: Optional right child node.
        :type right: Node | None
        '''
        self._left: Node = left
        self._right: Node | None = right

class AndNode(BranchNode):
    '''
    Represent a fuzzy AND operation.
    '''
    @override
    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate the fuzzy AND using np.fmin.

        :param context: Dictionary containing data/context for evaluation.
        :type context: dict[str, dict[str, np.ndarray]]
        :return: Minimum membership value.
        :rtype: np.ndarray
        :raises AssertionError: If the right child node is missing.
        '''
        assert(self._right is not None)
        return cast(BinaryOp, OPERATORS['AND'])(
            self._left.evaluate(context),
            self._right.evaluate(context)
        )

    @override
    def __str__(self) -> str:
        return f'({self._left} AND {self._right})'

class OrNode(BranchNode):
    '''
    Represent a fuzzy OR operation.
    '''
    @override
    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate the fuzzy OR using np.fmax.

        :param context: Dictionary containing data/context for evaluation.
        :type context: dict[str, dict[str, np.ndarray]]
        :return: Maximum membership value.
        :rtype: np.ndarray
        :raises AssertionError: If the right child node is missing.
        '''
        assert(self._right is not None)
        return cast(BinaryOp, OPERATORS['OR'])(
            self._left.evaluate(context),
            self._right.evaluate(context)
        )

    @override
    def __str__(self) -> str:
        return f'({self._left} OR {self._right})'

class NotNode(BranchNode):
    '''
    Represent a fuzzy NOT operation.
    '''
    def __init__(self, child: Node) -> None:
        '''
        Initializes the NotNode.

        :param child: Child node to invert.
        :type child: Node
        '''
        super().__init__(left=child, right=None)

    @override
    def evaluate(self, context: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
        '''
        Evaluate fuzzy NOT using 1.0 - val.

        :param context: Dictionary containing data/context for evaluation.
        :type context: dict[str, dict[str, np.ndarray]]
        :return: Inverted membership value.
        :rtype: np.ndarray
        '''
        return cast(UnaryOp, OPERATORS['NOT'])(self._left.evaluate(context))

    @override
    def __str__(self) -> str:
        return f'NOT {self._left}'
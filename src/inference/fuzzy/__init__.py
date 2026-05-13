'''
Fuzzy Logic Subsystem
=====================
This package constructs a domain-specific language (DSL) and Abstract Syntax Tree (AST)
for defining and evaluating fuzzy logic constraints, operators, rules, and linguistic
variables across mathematical universes.
'''
from .ast import Node, BranchNode, LeafNode, UnaryOp, BinaryOp
from .variables import Variable
from .rules import Rule

__all__ = [
    'Node', 'BranchNode', 'LeafNode',
    'UnaryOp', 'BinaryOp',
    'Variable', 'Rule'
]
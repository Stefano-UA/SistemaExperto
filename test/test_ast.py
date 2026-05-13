'''
Tests for the fuzzy AST and operators.
'''
import pytest
import numpy as np

from inference.fuzzy import Node, LeafNode

def test_ast_evaluation_scalar() -> None:
    '''
    Test AST operations with scalar values.
    '''
    # Set scalar context
    context: dict[str, dict[str, np.ndarray]] = {
        'exhaustion': {'high': np.array([0.8]), 'low': np.array([0.2])},
        'cynicism': {'high': np.array([0.9]), 'low': np.array([0.1])}
    }
    # Get leaf nodes
    node_a: LeafNode = LeafNode('exhaustion', 'high')
    node_b: LeafNode = LeafNode('cynicism', 'low')
    # Test AND
    and_node: Node = node_a & node_b
    assert(and_node.evaluate(context) == 0.1)
    # Test OR
    or_node: Node = node_a | node_b
    assert(or_node.evaluate(context) == 0.8)
    # Test NOT
    not_node: Node = ~node_a
    assert(not_node.evaluate(context) == pytest.approx(0.2))

def test_ast_evaluation_array() -> None:
    '''
    Test AST operations with vector values.
    '''
    # Set vectorized context
    context: dict[str, dict[str, np.ndarray]] = {
        'exhaustion': {'high': np.array([0.8, 0.5, 0.2])},
        'cynicism': {'high': np.array([0.9, 0.4, 0.1])}
    }
    # Get leaf nodes
    node_a: LeafNode = LeafNode('exhaustion', 'high')
    node_b: LeafNode = LeafNode('cynicism', 'high')
    # Test AND
    and_result: np.ndarray = (node_a & node_b).evaluate(context)
    np.testing.assert_array_equal(and_result, np.array([0.8, 0.4, 0.1]))
    # Test OR
    or_result: np.ndarray = (node_a | node_b).evaluate(context)
    np.testing.assert_array_equal(or_result, np.array([0.9, 0.5, 0.2]))
    # Test NOT
    not_result: np.ndarray = (~node_a).evaluate(context)
    np.testing.assert_allclose(not_result, np.array([0.2, 0.5, 0.8]))

def test_ast_complex_structure() -> None:
    '''
    Test AST oeprations in a complex tree structure.
    '''
    # Set vectorized context
    context: dict[str, dict[str, np.ndarray]] = {
        'exhaustion': {'high': np.array([0.8]), 'low': np.array([0.2])},
        'cynicism': {'high': np.array([0.9]), 'low': np.array([0.1])},
        'personalization': {'high': np.array([0.4]), 'low': np.array([0.6])}
    }
    # Get leaf nodes
    node_a: LeafNode = LeafNode('exhaustion', 'high')
    node_b: LeafNode = LeafNode('cynicism', 'high')
    node_c: LeafNode = LeafNode('personalization', 'high')
    node_d: LeafNode = LeafNode('cynicism', 'low')
    # Create complex tree
    node: Node = node_a & node_b & ~node_c | node_d
    # Test tree
    assert(node.evaluate(context) == pytest.approx(0.6))
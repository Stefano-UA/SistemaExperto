'''
Tests for the parser module.
'''
import pytest
import skfuzzy as fuzz

from inference.fuzzy import Variable
from data.parsers import RuleParser, VariableParser

def test_variable_parser() -> None:
    '''
    Test Variable DSL syntax resolution.

    Supply a raw multiline string of custom DSL Variable syntax and verify that
    the parser constructs valid Variables with correctly scoped numpy
    universes and correctly bound scikit-fuzzy membership functions.
    '''
    # Initialize parser
    parser: VariableParser = VariableParser()
    # Prepare multiline DSL string with comments and various formats
    text: str = '''
    # Mixed MF types test
    Exhaustion <0, 10>: (Low <trimf, 0, 2, 4>; High <gaussmf, 10, 2>)
    Cynicism <0, 5>: (Low <trapmf, 0, 0, 1, 2>; High <gbellmf, 2, 4, 5>)
    # Testing different range and parameters
    # This is a comment
    invalid line without colon
    Personalization <5, 10>: (Medium <trimf, 5, 6, 7>; High <trapmf, 5, 5, 7, 10>)
    '''
    # Execute parsing
    vars_list: list[Variable] = parser.parse(text)
    # Verify that variables were extracted
    assert(len(vars_list) == 3)
    # Validate specific attributes for the variables
    assert(vars_list[0].name == 'Exhaustion')
    assert(vars_list[1].name == 'Cynicism')
    assert(vars_list[2].name == 'Personalization')
    assert('Low' in vars_list[0].terms)
    assert('High' in vars_list[0].terms)
    assert('Low' in vars_list[1].terms)
    assert('High' in vars_list[1].terms)
    assert('Medium' in vars_list[2].terms)
    assert('High' in vars_list[2].terms)
    assert(vars_list[0].universe.min() == 0)
    assert(vars_list[0].universe.max() == 10)
    assert(vars_list[1].universe.min() == 0)
    assert(vars_list[1].universe.max() == 5)
    assert(vars_list[2].universe.min() == 5)
    assert(vars_list[2].universe.max() == 10)
    # Check terms were got correctly
    for var, term, fn, params in [
        (0, 'Low',    'trimf',   [0, 2, 4]),      # Triangle: abc
        (0, 'High',   'gaussmf', [10, 2]),        # Gaussian: mean, sigma
        (1, 'Low',    'trapmf',  [0, 0, 1, 2]),   # Trapezoid: abcd
        (1, 'High',   'gbellmf', [2, 4, 5]),      # Gen. Bell: width, slope, center
        (2, 'Medium', 'trimf',   [5, 6, 7]),      # Triangle: abc
        (2, 'High',   'trapmf',  [5, 5, 7, 10]),  # Trapezoid: abcd
    ]:
        assert (vars_list[var].terms[term] == getattr(fuzz, fn)(vars_list[var].universe, params)).all() # pyright: ignore[reportAny]

def test_variable_parser_errors() -> None:
    '''
    Test graceful degradation of Variable parsing.

    Feed syntactically invalid strings into the Variable parser and ensure it
    swallows the errors gracefully, skipping malformed variables without crashing
    the system.
    '''
    # Initialize parser
    parser: VariableParser = VariableParser()
    # Prepare multiline DSL string with comments and various formats
    text: str = '''
    # Mixed MF types test
    Exhaustion <0, 10: (Low <trimf, 0, 2, 4>; High <gaussmf, 10, 2>)
    Exhaustion <0 10>: (Low <trimf, 0, 2, 4>; High <gaussmf, 10, 2>)
    Exhaustion <0, 10>: .(Low <trimf, 0, 2, 4>; High <gaussmf, 10, 2>)
    Cynicism <0, 5> (Low <trapmf, 0, 0, 1, 2>; High <gbellmf, 2, 4, 5>)
    Cynicism <0, 5>: (Low <trapmf, 0, 0, 1, 2>; High <gbellmf, 2, 4, 5)
    Cynicism <0, 5>: (Low <trapmf, 10, 0, 1, 2>; High <gbellmf, 2, 4, 5>)
    # Testing different range and parameters
    # This is a comment
    invalid line without colon
    Personalization <5, 10>: Medium <trimf, 5, 6, 7>; High <trapmf, 5, 5, 7, 10>)
    Personalization <5, 10>: (Medium <trimff, 5, 6, 7>; High <trapmf, 5, 5, 7, 10>)
    Personalization <5, 10>: (Medium <trimf, 5, 6, 7> High <trapmf, 5, 5, 7, 10>)
    '''
    # Test lots of variables with small syntax errors
    vars_list: list[Variable] = parser.parse(text)
    assert(len(vars_list) == 0)

def test_rule_parser() -> None:
    '''
    Test Rule DSL syntax resolution.

    Provide complex logical conditions and verify the parser generates the
    correct abstract syntax tree consisting of OrNodes, AndNodes, NotNodes,
    and LeafNodes bound to the correct Rule consequent object.
    '''
    # Initialize parser
    parser: RuleParser = RuleParser()
    # Prepare rules with logic and groupings
    text: str = """
    IF Exhaustion IS High AND Cynicism IS High OR Personalization IS Low THEN Burnout IS High
    IF Exhaustion IS High AND (Cynicism IS High OR NOT Personalization IS High) THEN Burnout IS High
    IF NOT Exhaustion IS High THEN Burnout IS Low
    """
    # Execute parsing
    rules_list: list = parser.parse(text)
    # Verify rules were parsed correctly
    assert(len(rules_list) == 3)
    assert(str(rules_list[0]) == 'IF ((Exhaustion IS High AND Cynicism IS High) OR Personalization IS Low) THEN Burnout IS High')
    assert(str(rules_list[1]) == 'IF (Exhaustion IS High AND (Cynicism IS High OR NOT Personalization IS High)) THEN Burnout IS High')
    assert(str(rules_list[2]) == 'IF NOT Exhaustion IS High THEN Burnout IS Low')

def test_rule_parser_errors() -> None:
    '''
    Test graceful degradation of Rule parsing.

    Feed syntactically invalid strings into the Rule parser and ensure it
    swallows the errors gracefully, skipping malformed rules without crashing
    the system.
    '''
    # Initialize parser
    parser: RuleParser = RuleParser()
    # Prepare multiline DSL string with comments and various formats
    text: str = '''
    # This is a comment
    (Exhaustion IS High) THEN Burnout IS High
    IF (Exhaustion IS High) Burnout IS High
    # This is a comment
    # This is a comment
    IF (Exhaustion IS High THEN Burnout IS High
    IF (Exhaustion IS High THEN Burnout IS High)
    IF Exhaustion IS High ( AND Cynicism IS High ) THEN Burnout IS High
    '''
    # Test lots of rules with small syntax errors
    rules_list: list[Rule] = parser.parse(text)
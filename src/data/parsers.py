'''
Domain Parsers
==============
This module provides concrete parser implementations for transforming raw
text file payloads (.rules, .vars) into structured, operable domain objects
such as LinguisticVariables and Abstract Syntax Trees for fuzzy logic rules.
'''
import numpy as np
import skfuzzy as fuzz
from abc import ABC, abstractmethod
from typing import Callable, cast, override

from inference.fuzzy import Variable, Rule, Node, LeafNode

PRECISION: int = 1000
'''Integer defining the resolution (number of discrete steps) used when generating numpy arrays for fuzzy universes.'''

class Parser(ABC):
    '''
    Abstract base class for parsers.
    '''
    @abstractmethod
    def parse(self, text: str) -> object:
        '''
        Parse text and return corresponding object.

        :param text: Text to parse.
        :return: Parsed object.
        '''
        pass

class VariableParser(Parser):
    '''
    Parser for linguistic variables definitions.

    Format: VariableName<DomainStart, DomainEnd>: (FirstSet<func, val1, ..., valn>; ...; NSet<func, val2, ..., valn>)
    '''
    def _parse_line(self, line: str) -> Variable | None:
        '''
        Parse single line into variable.

        :param line: Text line.
        :return: Parsed Variable or None if invalid.
        '''
        try:
            # Separate by :
            parts: list[str] = line.split(':')
            # Must have two parts divided by a :
            if (len(parts) != 2): return None
            # Separate into variable and set parts
            varpart, setpart = parts
            # Clean parts of trailing spaces
            varpart: str = varpart.strip()
            setpart: str = setpart.strip()
            # Separate by <
            parts = varpart.split('<')
            # Must have two parts divided by a <
            if (len(parts) != 2): return None
            # Separate varpart into variable name and domain part
            varname, domainpart = parts
            # Clean parts of trailing spaces, and extra chars
            varname: str = varname.strip()
            domainpart: str = domainpart.replace('>', '').strip()
            # Separate domainpart into start and end
            domstart, domend = [float(v.strip()) for v in domainpart.split(',')]
            # Setpart must start and end with ( and ) respectively
            if not (setpart.startswith('(') and setpart.endswith(')')): return None
            # Clean part of trailing spaces, and extra chars
            setpart = setpart[1:-1].strip()
            # Compute the universe of discourse
            universe: np.ndarray = np.linspace(domstart, domend, PRECISION)
            # Create the variable object
            variable: Variable = Variable(varname, universe)
            # Separate into set definitions
            setparts: list[str] = setpart.split(';')
            # Loop through sets
            for set in setparts:
                # Clean trailing spaces
                set: str = set.strip()
                if not set: continue
                # Separate by <
                parts = set.split('<')
                # Must have two parts divided by a <
                if (len(parts) != 2): return None
                # Separate into set name and set membership function
                setname, setmf = parts
                # Clean parts of trailing spaces, and extra chars
                setname: str = setname.strip()
                setmf: str = setmf.replace('>', '').strip()
                # Get function name (first value) and args (rest)
                fn, *args = [a.strip() for a in setmf.split(',')]
                # Check the function name ends in mf
                if not fn.endswith('mf'): return None
                # Ensure arguments are floats
                args = [float(a) for a in args]
                # Add the set to the variable
                variable.add_term(
                    setname,
                    cast(
                        Callable[[np.ndarray, list[float]], np.ndarray],
                        getattr(fuzz, fn)
                    )(universe, args)
                )
            return variable
        except Exception:
            return None

    @override
    def parse(self, text: str) -> list[Variable]:
        '''
        Parse variable definitions from text.

        :param text: Text containing variable definitions.
        :return: List of parsed Variable objects.
        '''
        variables: list[Variable] = []
        # Loop through lines
        for line in text.split('\n'):
            line: str = line.strip()
            # Ignore empty lines and comments
            if (not line) or line.startswith('#'):
                continue
            # Parse line
            variable: Variable | None = self._parse_line(line)
            # Append if parsed successfully
            if (variable is not None):
                variables.append(variable)
        return variables

class RuleParser(Parser):
    '''
    Parser for fuzzy rules definitions.

    Format: IF Var1 OR Var2 AND (Var3 OR NOT Var4) THEN OutputVar IS OutputSet

    :ivar _pos: Current index position in the token list during parsing.
    :vartype _pos: int
    :ivar _tokens: List of extracted string tokens from the rule antecedent.
    :vartype _tokens: list[str]

    :Example:
        >>> parser = RuleParser()
        >>> rule = parser.parse("IF exhaustion IS high AND cynicism IS high THEN burnout IS high")
    '''
    def __init__(self) -> None:
        '''
        Initialize RuleParser instance.
        '''
        self._pos: int = 0
        self._tokens: list[str] = []

    @property
    def tokens(self) -> list[str]:
        '''
        Get current tokens.

        :return: List of tokens.
        '''
        return self._tokens

    @tokens.setter
    def tokens(self, value: list[str]) -> None:
        '''
        Set current tokens.

        :param value: List of tokens.
        '''
        self._tokens = value

    @property
    def pos(self) -> int:
        '''
        Get current position.

        :return: Current position index.
        '''
        return self._pos

    @pos.setter
    def pos(self, value: int) -> None:
        '''
        Set current position.

        :param value: New position index.
        '''
        self._pos = value

    def _parse_line(self, line: str) -> Rule | None:
        '''
        Parse single line into rule.

        :param line: Text line.
        :return: Parsed Rule or None if invalid.
        '''
        # Separate by THEN
        parts: list[str] = line.split(' THEN ')
        # Must have two parts divided by THEN
        if (len(parts) != 2): return None
        # Separate into if and then parts
        ifpart, thenpart = parts
        # Clean parts of trailing spaces, and extra chars
        ifpart: str = ifpart[3:].strip()
        thenpart: str = thenpart.strip()
        # Tokenize and parse antecedent
        self._tokenize(ifpart)
        antecedent: Node | None = self._parse_tokens()
        # Antecedent must exist
        if antecedent is None: return None
        # Tokenize and parse consequent
        self._tokenize(thenpart)
        consequent: Node | None = self._parse_tokens()
        # Consequent must exist
        if consequent is None: return None
        # Consequent must not have any strange logic
        if not isinstance(consequent, LeafNode): return None
        # Create rule from both parts
        return Rule(antecedent, consequent)

    def _tokenize(self, text: str) -> None:
        '''
        Tokenize a part of rule.

        :param text: Text to tokenize.
        '''
        # Ensure parenthesis have spaces around them
        text = text.replace('(', ' ( ').replace(')', ' ) ')
        # Get raw tokens splitting on spaces
        rwtokens: list[str] = text.split()
        # Initialize token list
        self._tokens, i = [], 0
        # Loop until all tokens processed
        while (i < len(rwtokens)):
            tk = rwtokens[i]
            # Processs token if recognized
            if tk in ('AND', 'OR', 'NOT', '(', ')'):
                self._tokens.append(tk)
                i += 1
            else:
                # Process leaf as one token (Var IS Set)
                leaf_parts: list[str] = []
                # Loop while we have tokens and they are not recognized
                while (i < len(rwtokens)) and not (rwtokens[i] in ('AND', 'OR', 'NOT', '(', ')')):
                    leaf_parts.append(rwtokens[i])
                    i += 1
                self._tokens.append(' '.join(leaf_parts))

    def _match(self, expected: str) -> bool:
        '''
        Match and consume next token if it equals expected value.

        :param expected: Expected token string.
        :return: True if matched, False otherwise.
        '''
        # If no more tokens left
        if (self.pos >= len(self._tokens)): return False
        # If current token doesnt match
        if (self._tokens[self.pos] != expected): return False
        # Consume token
        self.pos += 1
        return True

    def _parse_tokens(self) -> Node | None:
        '''
        Parse tokens into AST.

        :return: Root node of AST.
        '''
        self.pos = 0
        return self._parse_or() # Precedence: NOT, AND, OR, ()

    def _parse_or(self) -> Node | None:
        '''
        Parse OR expression.

        :return: AST Node.
        '''
        left: Node | None = self._parse_and()
        # Match all OR in the same precedence level
        while self._match('OR'):
            # Check left side is defined
            if left is None: return None
            # Parse the next operation level
            right: Node | None = self._parse_and() # Precedence: NOT, AND, OR, ()
            # Check right side is defined
            if right is None: return None
            # Get Branch with OR operation
            left = left | right
        return left

    def _parse_and(self) -> Node | None:
        '''
        Parse AND expression.

        :return: AST Node.
        '''
        left: Node | None = self._parse_not()
        # Match all AND in the same precedence level
        while self._match('AND'):
            # Check left side is defined
            if left is None: return None
            # Parse the next operation level
            right: Node | None = self._parse_not() # Precedence: NOT, AND, OR, ()
            # Check right side is defined
            if right is None: return None
            # Get Branch with AND operation
            left = left & right
        return left

    def _parse_not(self) -> Node | None:
        '''
        Parse NOT expression.

        :return: AST Node.
        '''
        # Match all sequential NOT in the same precedence level
        if self._match('NOT'):
            # Parse the next operation level, recursively caching more sequential NOTs
            node: Node | None = self._parse_not() # Precedence: NOT, AND, OR, (), IS
            # Check node is defined
            if node is None: return None
            # Get Branch with NOT operation
            node = ~node
            return node
        return self._parse_factor()

    def _parse_factor(self) -> Node | None:
        '''
        Parse factor expression.

        :return: AST Node.
        '''
        if self._match('('):
            node = self._parse_or()
            if not self._match(')'): return None
            return node
        return self._parse_is()

    def _parse_is(self) -> Node | None:
        '''
        Parse IS expression.

        :return: AST Node.
        '''
        # Check if we are out of bounds
        if (self.pos >= len(self.tokens)):
            return None
        # Get current token and consume it
        token: str = self.tokens[self.pos]
        self.pos += 1
        # Separate by IS
        parts: list[str] = token.split(' IS ')
        # Must have two parts divided by IS
        if (len(parts) != 2): return None
        # Separate into var name and term name
        varname, termname = parts
        # Clean parts of trailing spaces
        varname: str = varname.strip()
        termname: str = termname.strip()
        return LeafNode(varname, termname)

    @override
    def parse(self, text: str) -> list[Rule]:
        '''
        Parse rule definitions from text.

        :param text: Text containing rule definitions.
        :return: List of parsed Rule objects.
        '''
        rules: list[Rule] = []
        # Loop through lines
        for line in text.split('\n'):
            line: str = line.strip()
            # Ignore empty lines and comments (non-rules)
            if not line or not line.startswith('IF '):
                continue
            # Parse line
            rule: Rule | None = self._parse_line(line)
            # Append if parsed successfully
            if (rule is not None):
                rules.append(rule)
        return rules
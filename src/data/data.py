'''
Data Container
==============
This module provides the central ``Data`` container class. It acts as the
in-memory repository for the entire application state, storing parsed rules,
linguistic variables, mappings, and the raw and processed pandas DataFrames.
'''
import os
import pandas as pd

from inference.fuzzy import Rule, Variable
from .parsers import RuleParser, VariableParser

class Data:
    '''
    Container for managing application data, including input sets, rules, variables, and inference results.

    :ivar _data: Internal Pandas DataFrame holding processed inputs.
    :vartype _data: pd.DataFrame | None
    :ivar _mappings: Column mappings from the raw CSV.
    :vartype _mappings: dict[str, str] | None
    :ivar _rules: Tuple of loaded fuzzy logic rules.
    :vartype _rules: tuple[Rule, ...] | None
    :ivar _vars: Dictionary of loaded linguistic variables mapped by name.
    :vartype _vars: dict[str, Variable] | None
    :ivar _outvar: The final output linguistic variable for inference.
    :vartype _outvar: Variable | None
    :ivar _results: Dictionary caching generated results DataFrames by engine ID.
    :vartype _results: dict[str, pd.DataFrame]
    '''
    def __init__(self) -> None:
        '''
        Initialize the Data container with empty attributes.
        '''
        self._data: pd.DataFrame | None = None
        self._mappings: dict[str, str] | None = None
        self._rules: tuple[Rule, ...] | None = None
        self._vars: dict[str, Variable] | None = None
        self._outvar: Variable | None = None
        self._results: dict[str, pd.DataFrame] = {}

    @property
    def data(self) -> pd.DataFrame:
        '''
        Get processed input data.

        :return: DataFrame containing processed data.
        '''
        if (self._data is None):
            return pd.DataFrame()
        return self._data.copy()

    @property
    def rules(self) -> tuple[Rule, ...]:
        '''
        Get the loaded fuzzy rules.

        :return: Tuple of Rule objects.
        '''
        if (self._rules is None):
            return tuple()
        return self._rules

    @property
    def variables(self) -> dict[str, Variable]:
        '''
        Get the loaded fuzzy variables.

        :return: Dict of Variable objects mapped by their names.
        '''
        if (self._vars is None):
            return dict()
        return self._vars

    @property
    def outvar(self) -> Variable | None:
        '''
        Get the output variable.

        :return: Output variable, if any, or None.
        '''
        return self._outvar

    @property
    def results(self) -> dict[str, pd.DataFrame]:
        '''
        Get results data.

        :return: Dictionary containing results DataFrames indexed by id.
        '''
        return self._results

    def load_csv(self, path: str) -> bool:
        '''
        Ingest data from a CSV file.

        .. warning::
           If pandas fails to parse the CSV or the file is empty, this method
           will catch the exception internally and reset the ``_data`` attribute
           to ``None`` to prevent corrupted states.

        :param path: Path to the CSV file.
        :type path: str
        :return: True if successful, False otherwise.
        :rtype: bool
        :raises ValueError: Caught internally if the CSV data is empty.
        '''
        try:
            # Load with pandas
            self._data = pd.read_csv(
                os.path.abspath(path),
                sep=os.getenv('SEP', ',')
            )
            # Check if loaded empty
            if self._data.empty:
                raise ValueError('Data is empty!')
            # Apply mappings (summing columns) if loaded
            if not (self._mappings is None):
                self._data = self._data.T.groupby(self._mappings).sum().T
            return True
        except Exception:
            self._data = None
            return False

    def load_map(self, path: str) -> bool:
        '''
        Load column mappings from a .map file and apply summation to the data.

        :param path: Path to the mapping file.
        :type path: str
        :return: True if successful, False otherwise.
        :rtype: bool
        :raises ValueError: Caught internally if the mapping file resolves to empty.
        '''
        try:
            self._mappings = {}
            with open(
                os.path.abspath(path), 'r',
                encoding=os.getenv('ENC', 'utf-8')
            ) as file:
                # Parse each line here
                for line in file:
                    line = line.strip()
                    if ('->' in line):
                        key, value = line.split('->', 1)
                        self._mappings[key.strip()] = value.strip()
            # Check if loaded empty
            if (len(self._mappings) == 0):
                raise ValueError('Mappings are empty!')
            # Apply mappings (summing columns) if data loaded
            if not (self._data is None):
                self._data = self._data.T.groupby(self._mappings).sum().T
            return True
        except Exception:
            self._mappings = None
            return False

    def load_rules(self, path: str) -> bool:
        '''
        Load fuzzy rules from a .rules file.

        :param path: Path to the rules file.
        :type path: str
        :return: True if successful, False otherwise.
        :rtype: bool
        :raises ValueError: Caught internally if rules payload resolves to empty.
        '''
        try:
            with open(
                os.path.abspath(path), 'r',
                encoding=os.getenv('ENC', 'utf-8')
            ) as file:
                # Load with parser
                self._rules = tuple(RuleParser().parse(file.read()))
            # Check if loaded empty
            if (len(self._rules) == 0):
                raise ValueError('Rules are empty!')
            return True
        except Exception:
            self._rules = None
            return False

    def load_vars(self, path: str) -> bool:
        '''
        Load fuzzy variables from a .vars file.

        :param path: Path to the vars file.
        :type path: str
        :return: True if successful, False otherwise.
        :rtype: bool
        :raises ValueError: Caught internally if variable payload resolves to empty.
        '''
        try:
            with open(
                os.path.abspath(path), 'r',
                encoding=os.getenv('ENC', 'utf-8')
            ) as file:
                # Load with parser
                self._vars = {var.name: var for var in VariableParser().parse(file.read())}
            # Check if loaded empty
            if (len(self._vars) == 0):
                raise ValueError('Vars are empty!')
            # Get output variable (last variable)
            self._outvar = next(reversed(self._vars.values()))
            return True
        except Exception:
            self._vars = None
            return False

    def store(self, results: pd.DataFrame, engine: type[object]) -> None:
        '''
        Store inference results in the container.

        :param results: DataFrame containing the inference results.
        :type results: pd.DataFrame
        :param engine: Engine instance used to compute the results.
        :type engine: type[object]
        '''
        self.results[f'<{len(self.results)}>{engine.__class__.__name__}'] = results

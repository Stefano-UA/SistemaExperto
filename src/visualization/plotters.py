'''
Visualization Plotters
======================
This module provides utilities for rendering high-quality plots of fuzzy logic
variables, rule aggregations, and inference comparisons. It relies on matplotlib
and seaborn to produce static image assets.
'''
import numpy as np
import pandas as pd
import seaborn as sns
import skfuzzy as fuzz
from typing import Callable, cast
from pathlib import Path
import matplotlib.pyplot as plt

from data import Data
from evaluation import Evaluator
from inference.fuzzy import Variable

class Plotter:
    '''
    Utility class for generating visualizations from application Data.

    :ivar _data: Central Data container tracking all parsed values and results.
    :vartype _data: Data
    '''
    def __init__(self, data: Data) -> None:
        '''
        Initialize Plotter.

        :param data: Application Data container.
        :type data: Data
        '''
        self._data: Data = data
        # Use seaborn style for modern looking plots
        sns.set_theme(style='whitegrid')

    def plot_variable(self, var: str, path: str) -> None:
        '''
        Plot the membership functions of a single linguistic variable.

        :param var: Name of the variable to plot.
        :type var: str
        :param path: Base directory where the plot will be saved.
        :type path: str
        '''
        # Check if variable exists
        if not (var in self._data.variables): return
        # Retrieve the variable
        variable: Variable = self._data.variables[var]
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_title(f'Variable {variable.name}')
        # Plot each term
        for term_name, term_mf in variable.terms.items():
            ax.plot(variable.universe, term_mf, linewidth=1.5, label=term_name)
        # Add legend
        ax.legend()
        # Save figure
        out_dir: Path = Path(path) / 'variables'
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f'{variable.name}.png', bbox_inches='tight')
        plt.close(fig)

    def plot_variables(self, path: str, progress_fn: Callable[[int, int], None] | None=None) -> None:
        '''
        Plot all linguistic variables stored in the Data container.

        :param path: Base directory where plots will be saved.
        :type path: str
        :param progress_fn: Optional callback for reporting progress (current, total).
        :type progress_fn: Callable[[int, int], None] | None
        '''
        nvars: int = len(self._data.variables)
        # Iterate over all variables and plot them
        for ix, var in enumerate(self._data.variables.keys()):
            # Update progress, if any
            if progress_fn: progress_fn(ix, nvars)
            # Plot variable
            self.plot_variable(var, path)
        # Update progress, if any
        if progress_fn: progress_fn(nvars, nvars)

    def plot_result(self, key: str, path: str, row_idx: int=0) -> None:
        '''
        Plot the output variable's membership functions alongside the aggregated
        activation area and the final defuzzified decision.

        :param key: Result key representing the engine execution.
        :type key: str
        :param path: Base directory where the plot will be saved.
        :type path: str
        :param row_idx: Index of the data row to visualize.
        :type row_idx: int
        '''
        # Check for results and output variable
        if not (key in self._data.results) or (self._data.outvar is None):
            return
        # Retrieve the result dataframe
        results: pd.DataFrame = self._data.results[key]
        if results.empty or (row_idx >= len(results)): return
        # Extract row and output variable
        outvar: Variable = self._data.outvar
        row: pd.Series = results.iloc[row_idx]
        # Ensure fuzzy outputs are present
        if not (outvar.name in row) or not ('RESULTS' in row): return
        # Extract aggregated array and final decision
        aggregated: np.ndarray = cast(np.ndarray, row[outvar.name])
        final_decision: float = cast(float, row['RESULTS'])
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_title(f'Evaluation Result: {outvar.name} (Row {row_idx})')
        # Get a modern color map for dynamic term coloring without deprecation warning
        colors: list[str] = cast(list[str], plt.colormaps['tab10'].colors) # pyright: ignore[reportAttributeAccessIssue]
        # Plot each term of the output variable
        for i, (term_name, term_mf) in enumerate(outvar.terms.items()):
            color: str = colors[i % len(colors)]
            ax.plot(outvar.universe, term_mf, color=color, linewidth=1.0, linestyle='--', label=term_name)
        # Fill the aggregated area
        ax.fill_between(
            outvar.universe,
            np.zeros_like(outvar.universe),
            aggregated,
            facecolor='orange',
            label='Aggregated Area',
            alpha=0.7
        )
        # Calculate the y-value intersection for the final decision line
        y_val: float = cast(
            float,
            fuzz.interp_membership(outvar.universe, aggregated, final_decision)
        )
        ax.plot(
            [final_decision, final_decision],
            [0, max(y_val, 0.1)],
            'k', alpha=0.9,
            linewidth=2.0,
            label=f'Defuzzified: {final_decision:.2f}'
        )
        # Add legend
        ax.legend()
        # Save figure
        out_dir: Path = Path(path) / 'outvar' / key
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f'results_row{row_idx}.png', bbox_inches='tight')
        plt.close(fig)

    def plot_results(self, key: str, path: str, progress_fn: Callable[[int, int], None] | None=None) -> None:
        '''
        Plot all results for a results DataFrame.

        :param key: Result key representing the engine execution.
        :type key: str
        :param path: Base directory where plots will be saved.
        :type path: str
        :param progress_fn: Optional callback for reporting progress (current, total).
        :type progress_fn: Callable[[int, int], None] | None
        '''
        nrows: int = len(self._data.results[key])
        # Iterate over all result rows and plot them
        for row in range(len(self._data.results[key])):
            # Update progress, if any
            if progress_fn: progress_fn(row, nrows)
            # Plot result
            self.plot_result(key, path, row_idx=row)
        # Update progress, if any
        if progress_fn: progress_fn(nrows, nrows)

    def plot_comparison(self, key1: str, key2: str, path: str) -> None:
        '''
        Plot a comparison scatter plot between two engine evaluation results,
        overlaying the MAE and MSE metrics.

        :param key1: First result key.
        :type key1: str
        :param key2: Second result key.
        :type key2: str
        :param path: Base directory where the plot will be saved.
        :type path: str
        '''
        # Check if both keys exist in results
        if not (key1 in self._data.results) or not (key2 in self._data.results):
            return
        # Retrieve results dataframes
        res1: pd.DataFrame = self._data.results[key1]
        res2: pd.DataFrame = self._data.results[key2]
        # Identify score columns
        col1: str | None = 'RESULTS' if ('RESULTS' in res1) else ('mbi_score' if ('mbi_score' in res1) else None)
        col2: str | None = 'RESULTS' if ('RESULTS' in res2) else ('mbi_score' if ('mbi_score' in res2) else None)
        # Verify columns exist
        if (not col1) or (not col2): return
        # Extract score series
        scores1: pd.Series[float] = res1[col1]
        scores2: pd.Series[float] = res2[col2]
        # Evaluate metrics
        evaluator: Evaluator = Evaluator(scores1, scores2)
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(x=scores1, y=scores2, ax=ax, alpha=0.7, color='purple')
        # Plot the ideal match reference line
        min_val: float = min(scores1.min(), scores2.min())
        max_val: float = max(scores1.max(), scores2.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Ideal Match')
        # Set titles and labels
        ax.set_title(f'Result Comparison\nMAE: {evaluator.mae:.4f} | MSE: {evaluator.mse:.4f}')
        ax.set_xlabel(f'Model X({key1})')
        ax.set_ylabel(f'Model Y ({key2})')
        ax.legend()
        # Save figure
        out_dir: Path = Path(path) / 'comparisons'
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f'{key1}_vs_{key2}.png', bbox_inches='tight')
        plt.close(fig)

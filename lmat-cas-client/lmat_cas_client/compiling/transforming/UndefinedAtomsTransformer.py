from typing import Iterator

from lark import Token, Transformer, v_args
from sympy import Abs, Expr, Function, Symbol, cbrt, ceiling, root, sqrt
from sympy.physics.units import Quantity

from lmat_cas_client.compiling import DefinitionStore
from lmat_cas_client.compiling.Definitions import SympyDefinition
from lmat_cas_client.math_lib.units import UnitUtils

# Mapping from plain/Typst function names to their SymPy equivalents.
# Functions in this map are NOT in SymPy's FunctionClass registry, so
# Function('name')(*args) would create an unevaluated custom function instead
# of calling the real SymPy operation.
#
# Note: Typst's root(n, x) has reversed argument order vs SymPy's root(x, n).
_TYPST_TO_SYMPY_FUNCTION = {
    "sqrt": lambda *args: sqrt(*args),
    "cbrt": lambda *args: cbrt(*args),
    "root": lambda *args: root(args[1], args[0]) if len(args) == 2 else root(*args),
    "abs": lambda *args: Abs(*args),
    "ceil": lambda *args: ceiling(*args),
}


@v_args(inline=True)
class UndefinedAtomsTransformer(Transformer):
    """
    Handles transformation of rules relating to user defined (or undefined for that matter) symbols or functions.
    """

    def __init__(self, definition_store: DefinitionStore):
        self.__definition_store = definition_store

    def combine_symbol(self, *symbol_strings: str) -> str:
        return "".join(map(str, symbol_strings))

    def substitute_symbol(self, symbol_name: str) -> Symbol | Expr:
        definition = self.__definition_store.get_definition(
            str(symbol_name), default=SympyDefinition(Symbol(symbol_name))
        )

        return definition.defined_value(self.__definition_store)

    def indexed_symbol(
        self, symbol: Expr, index: Expr | str, primes: str | None
    ) -> str:
        primes = "" if primes is None else primes
        indexed_text = str(index)

        if not indexed_text.startswith("{") or not indexed_text.endswith("}"):
            indexed_text = f"{{{indexed_text}}}"

        return f"{symbol}_{indexed_text}{primes}"

    def formatted_symbol(
        self, formatter: Token, text: str | list[str], primes: str | None
    ) -> str:
        formatter_text = str(formatter)
        primes = "" if primes is None else primes

        if not text.startswith("{") and not text.endswith("}"):
            text = f"{{{str(text)}}}"

        return f"{formatter_text}{text}{primes}"

    @v_args(inline=False)
    def brace_surrounded_text(self, tokens):
        return "".join(map(str, tokens))

    def unit(self, unit_symbol: str) -> Quantity | Symbol:
        print(unit_symbol, flush=True)
        unit = UnitUtils.str_to_unit(unit_symbol)
        print(unit, flush=True)
        if unit is not None:
            return unit
        else:
            return self.substitute_symbol(unit_symbol)

    def undefined_function(
        self, func_name: str, func_args: Iterator[Expr] = None
    ) -> Function | Expr:
        func_definition = self.__definition_store.get_definition(func_name)

        if func_definition is not None and isinstance(
            func_definition, DefinitionStore.FunctionDefinition
        ):
            return func_definition.applied_value(
                self.__definition_store, [SympyDefinition(arg) for arg in func_args]
            )
        elif func_name in _TYPST_TO_SYMPY_FUNCTION:
            return _TYPST_TO_SYMPY_FUNCTION[func_name](*func_args)
        else:
            return Function(func_name)(*func_args)

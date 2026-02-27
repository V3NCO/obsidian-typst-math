from typing import Any

from sympy import *
from sympy.logic.boolalg import BooleanFalse, BooleanTrue
from sympy.physics.units import Quantity
from sympy.printing.precedence import precedence
from sympy.printing.str import StrPrinter

from lmat_cas_client.compiling.transforming.LatexMatrix import LatexMatrix

# Map LaTeX symbol names (with leading backslash) to Typst names.
_LATEX_TO_TYPST_SYMBOL: dict[str, str] = {
    # Lowercase Greek
    "\\alpha": "alpha",
    "\\beta": "beta",
    "\\gamma": "gamma",
    "\\delta": "delta",
    "\\epsilon": "epsilon",
    "\\varepsilon": "epsilon.alt",
    "\\zeta": "zeta",
    "\\eta": "eta",
    "\\theta": "theta",
    "\\vartheta": "theta.alt",
    "\\iota": "iota",
    "\\kappa": "kappa",
    "\\lambda": "lambda",
    "\\mu": "mu",
    "\\nu": "nu",
    "\\xi": "xi",
    "\\pi": "pi",
    "\\varpi": "pi.alt",
    "\\rho": "rho",
    "\\varrho": "rho.alt",
    "\\sigma": "sigma",
    "\\varsigma": "sigma.alt",
    "\\tau": "tau",
    "\\upsilon": "upsilon",
    "\\phi": "phi",
    "\\varphi": "phi.alt",
    "\\chi": "chi",
    "\\psi": "psi",
    "\\omega": "omega",
    # Uppercase Greek
    "\\Gamma": "Gamma",
    "\\Delta": "Delta",
    "\\Theta": "Theta",
    "\\Lambda": "Lambda",
    "\\Xi": "Xi",
    "\\Pi": "Pi",
    "\\Sigma": "Sigma",
    "\\Upsilon": "Upsilon",
    "\\Phi": "Phi",
    "\\Psi": "Psi",
    "\\Omega": "Omega",
}

# Map LaTeX formatting commands to Typst equivalents.
_LATEX_FORMAT_TO_TYPST: dict[str, str] = {
    "\\pmb": "bold",
    "\\mathbf": "bold",
    "\\vec": "arrow",
    "\\vectorarrow": "arrow",
    "\\hat": "hat",
    "\\bar": "macron",
    "\\overline": "overline",
    "\\mathit": "italic",
    "\\mathrm": "upright",
}


def _convert_symbol_name(name: str) -> str:
    """Convert a LaTeX/internal symbol name to Typst math notation."""
    if name in _LATEX_TO_TYPST_SYMBOL:
        return _LATEX_TO_TYPST_SYMBOL[name]

    # Handle formatting commands like \pmb{x}, \vec{x}, \hat{x}, etc.
    for latex_cmd, typst_cmd in _LATEX_FORMAT_TO_TYPST.items():
        if name.startswith(latex_cmd + "{") and name.endswith("}"):
            inner = name[len(latex_cmd) + 1 : -1]
            return f"{typst_cmd}({_convert_symbol_name(inner)})"

    # Remove leading backslash if present (fallback for unknown LaTeX commands).
    if name.startswith("\\"):
        return name[1:]

    return name


class LmatTypstPrinter(StrPrinter):
    """Converts Sympy expressions to Typst math notation."""

    def _print_Mul(self, expr: Mul) -> str:
        # Use StrPrinter output (which uses '*' between factors), then convert to
        # Typst's implicit multiplication notation (juxtaposition / space-separated).
        result = super()._print_Mul(expr)
        return result.replace("*", " ")

    def _print_Relational(self, expr) -> str:
        _REL_MAP = {
            "Equality": "=",
            "Unequality": "!=",
            "StrictLessThan": "<",
            "LessThan": "<=",
            "StrictGreaterThan": ">",
            "GreaterThan": ">=",
        }
        rel_op = _REL_MAP.get(type(expr).__name__, "=")
        return f"{self._print(expr.lhs)} {rel_op} {self._print(expr.rhs)}"

    def _print_Or(self, expr) -> str:
        return " or ".join(self._print(arg) for arg in expr.args)

    def _print_And(self, expr) -> str:
        return " and ".join(self._print(arg) for arg in expr.args)

    def _print_Not(self, expr) -> str:
        return f"not {self._print(expr.args[0])}"

    def _print_Float(self, expr: Float) -> str:
        # Re-implement without delegating to LatexPrinter, which uses LaTeX scientific
        # notation like r'\cdot 10^{exp}'. Use Typst 'times 10^(exp)' instead.
        from mpmath.libmp import to_str as mlib_to_str
        from sympy.core.numbers import prec_to_dps

        dps = prec_to_dps(expr._prec)
        str_real = mlib_to_str(expr._mpf_, dps, strip_zeros=True)
        # Ensure there is always a decimal point.
        if "." not in str_real and "e" not in str_real.lower():
            str_real += ".0"
        if "e" in str_real:
            mant, exp_str = str_real.split("e")
            if exp_str.startswith("+"):
                exp_str = exp_str[1:]
            return f"{mant} times 10^({exp_str})"
        return str_real

    def _print_Symbol(self, expr: Symbol) -> str:
        return _convert_symbol_name(expr.name)

    def _print_Dummy(self, expr: Dummy) -> str:
        return _convert_symbol_name(expr.name)

    def _print_Pow(self, expr: Pow, rational: bool = False) -> str:
        PREC = precedence(expr)
        base, exp = expr.base, expr.exp

        if exp is S.Half and not rational:
            return f"sqrt({self._print(base)})"

        if -exp is S.Half and not rational:
            return f"1/sqrt({self._print(base)})"

        if isinstance(exp, Rational) and exp.p == 1 and exp.q > 2 and not rational:
            return f"root({exp.q}, {self._print(base)})"

        # Negative integer exponents: x^-n → 1/x^n (fraction notation).
        if isinstance(exp, Integer) and exp < S.Zero:
            pos_exp = Integer(-exp)
            denom_base_str = self.parenthesize(base, PREC, strict=False)
            if pos_exp == S.One:
                return f"1/{denom_base_str}"
            return f"1/{denom_base_str}^{pos_exp}"

        base_str = self.parenthesize(base, PREC, strict=False)
        exp_str = self._print(exp)

        # Wrap complex exponents in parentheses.
        if isinstance(exp, (Add, Mul)) or (isinstance(exp, Rational) and exp.q != 1):
            exp_str = f"({exp_str})"

        return f"{base_str}^{exp_str}"

    def _print_Abs(self, expr) -> str:
        return f"abs({self._print(expr.args[0])})"

    def _print_ceiling(self, expr) -> str:
        return f"ceil({self._print(expr.args[0])})"

    def _print_factorial(self, expr) -> str:
        arg = expr.args[0]
        arg_str = self.parenthesize(arg, precedence(expr), strict=False)
        return f"{arg_str}!"

    def _print_Exp1(self, expr) -> str:
        return "e"

    def _print_Infinity(self, expr) -> str:
        return "oo"

    def _print_NegativeInfinity(self, expr) -> str:
        return "-oo"

    def _print_ImaginaryUnit(self, expr) -> str:
        return "i"

    def _print_BooleanTrue(self, _: BooleanTrue) -> str:
        return "T"

    def _print_BooleanFalse(self, _: BooleanFalse) -> str:
        return "F"

    def _print_Integral(self, expr) -> str:
        func_str = self._print(expr.function)
        parts = []
        for limit in expr.limits:
            if len(limit) == 1:
                # Indefinite integral: (x,)
                var = self._print(limit[0])
                parts.append(f"integral {func_str} dif {var}")
            else:
                # Definite integral: (x, a, b)
                var, lower, upper = limit
                parts.append(
                    f"integral_{self._print(lower)}^{self._print(upper)} {func_str} dif {self._print(var)}"
                )
        return " ".join(parts)

    def _print_Sum(self, expr) -> str:
        func_str = self._print(expr.function)
        (var, lower, upper) = expr.limits[0]
        return f"sum_({self._print(var)} = {self._print(lower)})^{self._print(upper)} {func_str}"

    def _print_Product(self, expr) -> str:
        func_str = self._print(expr.function)
        (var, lower, upper) = expr.limits[0]
        return f"product_({self._print(var)} = {self._print(lower)})^{self._print(upper)} {func_str}"

    def _print_Limit(self, expr) -> str:
        func, var, point, direction = expr.args
        point_str = self._print(point)
        # Standard mathematical notation: direction indicator on the limit point.
        # SymPy '+' is the default (right-hand / bilateral limit) — shown without marker.
        # SymPy '-' is an explicit left-hand limit — shown as a⁻.
        if str(direction) == "-":
            point_str = f"{point_str}^-"
        return f"lim_({self._print(var)} -> {point_str}) {self._print(func)}"

    def _print_Derivative(self, expr) -> str:
        func = expr.args[0]
        # Count order for each variable from the (var, order) pairs in args[1:]
        var_orders: list[tuple[Any, Any]] = list(expr.args[1:])
        total_order = sum(int(order) for _, order in var_orders)
        func_str = self._print(func)
        # Build denominator: dif x dif y or dif x^2 for repeated vars
        denom_parts = []
        for var, order in var_orders:
            var_str = self._print(var)
            if int(order) == 1:
                denom_parts.append(f"dif {var_str}")
            else:
                denom_parts.append(f"dif {var_str}^{order}")
        denom = " ".join(denom_parts)
        if total_order == 1:
            return f"(dif {func_str}) / ({denom})"
        return f"(dif^{total_order} {func_str}) / ({denom})"

    def _print_Piecewise(self, expr) -> str:
        cases = []
        for value, cond in expr.args:
            value_str = self._print(value)
            if cond is S.true:
                cases.append(f"{value_str} otherwise")
            else:
                cases.append(f"{value_str} if {self._print(cond)}")
        return "cases(" + ", ".join(cases) + ")"

    def _print_Quantity(self, expr: Quantity) -> str:
        # Prefer the unit's abbreviation (e.g. 'km', 'm', 'kg') for display.
        abbrev = getattr(expr, "abbrev", None)
        if abbrev is not None:
            return str(abbrev)
        # Fall back to the full name string.
        name = getattr(expr, "name", None)
        if isinstance(name, str) and name:
            return name
        # Final fallback: generic string printer (non-LaTeX).
        return StrPrinter().doprint(expr)

    def _print_matrix_contents(self, expr) -> str:
        """Print matrix contents using Typst mat() notation."""
        rows = []
        for i in range(expr.rows):
            row = ", ".join(self._print(expr[i, j]) for j in range(expr.cols))
            rows.append(row)
        return f"mat({'; '.join(rows)})"

    def _print_MutableDenseMatrix(self, expr) -> str:
        return self._print_matrix_contents(expr)

    def _print_ImmutableDenseMatrix(self, expr) -> str:
        return self._print_matrix_contents(expr)

    def _print_MatrixBase(self, expr) -> str:
        return self._print_matrix_contents(expr)

    def _print_LatexMatrix(self, expr: LatexMatrix) -> str:
        rows = []
        for row_index in range(expr.rows):
            row = ", ".join(self._print(expr[row_index, j]) for j in range(expr.cols))
            rows.append(row)
        return f"mat({'; '.join(rows)})"


def lmat_typst(expr: Expr) -> str:
    return LmatTypstPrinter().doprint(expr)

import sympy.physics.units as u
from lmat_cas_client.compiling.transforming.LatexMatrix import LatexMatrix
from lmat_cas_client.LmatTypstPrinter import LmatTypstPrinter, lmat_typst
from sympy import *


class TestLmatTypstPrinter:
    printer = LmatTypstPrinter()

    def test_integer(self):
        assert lmat_typst(Integer(2)) == "2"

    def test_float(self):
        assert lmat_typst(Float("0.5")) == "0.5"

    def test_numeric_fraction(self):
        assert lmat_typst(Rational(1, 2)) == "1/2"

    def test_power(self):
        x = Symbol("x")
        assert lmat_typst(x**2) == "x^2"

    def test_negative_power(self):
        x = Symbol("x")
        assert lmat_typst(x**-1) == "1/x"
        assert lmat_typst(Pow(x - 1, -1)) == "1/(x - 1)"
        assert lmat_typst(x**-2) == "1/x^2"

    def test_sqrt(self):
        x = Symbol("x")
        assert lmat_typst(sqrt(x)) == "sqrt(x)"

    def test_cbrt(self):
        x = Symbol("x")
        assert lmat_typst(cbrt(x)) == "root(3, x)"

    def test_greek_symbol(self):
        assert lmat_typst(Symbol("\\alpha")) == "alpha"
        assert lmat_typst(Symbol("\\beta")) == "beta"
        assert lmat_typst(Symbol("\\omega")) == "omega"
        assert lmat_typst(Symbol("\\Gamma")) == "Gamma"

    def test_trig_function(self):
        x = Symbol("x")
        assert lmat_typst(sin(x)) == "sin(x)"
        assert lmat_typst(cos(x)) == "cos(x)"

    def test_infinity(self):
        assert lmat_typst(oo) == "oo"
        assert lmat_typst(-oo) == "-oo"

    def test_boolean(self):
        from sympy.logic.boolalg import BooleanFalse, BooleanTrue
        assert lmat_typst(BooleanTrue()) == "T"
        assert lmat_typst(BooleanFalse()) == "F"

    def test_relational(self):
        x = Symbol("x")
        assert lmat_typst(Eq(x, 2)) == "x = 2"
        assert lmat_typst(Ne(x, 0)) == "x != 0"

    def test_or(self):
        x = Symbol("x")
        result = lmat_typst(Or(Eq(x, -2), Eq(x, 2)))
        assert "x = -2" in result
        assert "x = 2" in result
        assert "or" in result

    def test_matrix(self):
        m = Matrix([[1, 2], [3, 4]])
        assert lmat_typst(m) == "mat(1, 2; 3, 4)"

    def test_latex_matrix(self):
        latex_matrix = LatexMatrix(
            [[1, 2], [3, 4]], env_begin=r"\begin{matrix}", env_end=r"\end{matrix}"
        )
        assert lmat_typst(latex_matrix) == "mat(1, 2; 3, 4)"

    def test_fraction_with_symbols(self):
        a, b = symbols("a b")
        result = lmat_typst((a + b) / (a - b))
        assert result == "(a + b)/(a - b)"

    def test_fraction_apart(self):
        x = Symbol("x")
        result = lmat_typst(apart(1 / (x**2 - x), x))
        self._assert_str_equal("1/(x - 1) - 1/x", result)

    def test_units(self):
        result = lmat_typst(u.km)
        assert "km" in result

    def _assert_str_equal(self, expected, actual):
        assert "".join(expected.split()) == "".join(actual.split())

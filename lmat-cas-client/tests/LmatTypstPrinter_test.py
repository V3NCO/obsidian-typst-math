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
        assert lmat_typst(Float("9.0")) == "9.0"

    def test_float_scientific(self):
        # Scientific notation must use Typst 'times 10^(exp)' syntax, not LaTeX '\cdot 10^{exp}'.
        result = lmat_typst(Float(1e-10))
        assert "times" in result
        assert "10^" in result
        assert "\\" not in result  # No backslash/LaTeX commands

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

    def test_mul(self):
        a, b, x = symbols("a b x")
        # Typst uses juxtaposition (space) for multiplication, not '*'.
        assert lmat_typst(2 * a) == "2 a"
        assert lmat_typst(2 * a + 2 * b) == "2 a + 2 b"
        assert lmat_typst(a * b) == "a b"
        assert lmat_typst(-2 * a) == "-2 a"
        assert lmat_typst(expand((a + b) * 2)) == "2 a + 2 b"

    def test_fraction_with_symbols(self):
        a, b = symbols("a b")
        result = lmat_typst((a + b) / (a - b))
        assert result == "(a + b)/(a - b)"

    def test_fraction_apart(self):
        x = Symbol("x")
        result = lmat_typst(apart(1 / (x**2 - x), x))
        self._assert_str_equal("1/(x - 1) - 1/x", result)

    def test_units(self):
        # Uses the unit's abbreviation for display.
        assert lmat_typst(u.km) == "km"
        assert lmat_typst(u.meter) == "m"
        assert lmat_typst(u.kilogram) == "kg"
        assert lmat_typst(5 * u.km / u.hour) == "5 km/hour"

    def test_abs(self):
        x = Symbol("x")
        assert lmat_typst(Abs(x)) == "abs(x)"
        assert lmat_typst(Abs(x - 1)) == "abs(x - 1)"

    def test_ceiling(self):
        x = Symbol("x")
        assert lmat_typst(ceiling(x)) == "ceil(x)"

    def test_factorial(self):
        n = Symbol("n")
        assert lmat_typst(factorial(n)) == "n!"
        assert lmat_typst(factorial(5)) == "120"

    def test_euler_constant(self):
        # Euler's number must render as lowercase 'e', not uppercase 'E'.
        assert lmat_typst(E) == "e"
        x = Symbol("x")
        assert lmat_typst(exp(x)) == "e^x"

    def test_integral_indefinite(self):
        x = Symbol("x")
        assert lmat_typst(Integral(sin(x), x)) == "integral sin(x) dif x"

    def test_integral_definite(self):
        x = Symbol("x")
        assert lmat_typst(Integral(x**2, (x, 0, 1))) == "integral_0^1 x^2 dif x"

    def test_sum(self):
        x, n = symbols("x n")
        assert lmat_typst(Sum(x**2, (x, 0, n))) == "sum_(x = 0)^n x^2"

    def test_product(self):
        x, n = symbols("x n")
        assert lmat_typst(Product(x, (x, 1, n))) == "product_(x = 1)^n x"

    def test_limit(self):
        x = Symbol("x")
        # Standard (right-hand / bilateral) limit — no direction marker on point.
        assert lmat_typst(Limit(sin(x) / x, x, 0)) == "lim_(x -> 0) sin(x)/x"
        # Explicit left-hand limit — direction marker ⁻ on the limit point.
        assert lmat_typst(Limit(S.One / x, x, 0, "-")) == "lim_(x -> 0^-) 1/x"

    def test_derivative(self):
        x = Symbol("x")
        assert lmat_typst(Derivative(x**2, x)) == "(dif x^2) / (dif x)"
        assert lmat_typst(Derivative(sin(x), x, 2)) == "(dif^2 sin(x)) / (dif x^2)"

    def test_piecewise(self):
        x = Symbol("x")
        result = lmat_typst(Piecewise((x, x > 0), (-x, S.true)))
        assert result == "cases(x if x > 0, -x otherwise)"

    def _assert_str_equal(self, expected, actual):
        assert "".join(expected.split()) == "".join(actual.split())

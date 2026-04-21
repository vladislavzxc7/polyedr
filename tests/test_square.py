from pytest import approx
from common.r3 import R3
from shadow.polyedr import Polyedr, Segment


def r3approx(self, other):
    return (
        self.x == approx(other.x)
        and self.y == approx(other.y)
        and self.z == approx(other.z)
    )


setattr(R3, "approx", r3approx)


def seg_approx(self, other):
    return (
        self.beg == approx(other.beg)
        and self.fin == approx(other.fin)
        or self.beg == approx(other.fin)
        and self.fin == approx(other.beg)
    )


setattr(Segment, "approx", seg_approx)


class TestSquareVisible:

    def test_tes1_basic_visible(self, capsys):
        P = Polyedr("tests/test1.geom")
        res = P.square_visible()
        assert res == approx(16.0)

    def test_tes2_cube_boundary(self, capsys):
        P = Polyedr("tests/test2.geom")
        res = P.square_visible()
        assert res == approx(0.0)

    def test_tes3_shadow_logic(self, capsys):
        P = Polyedr("tests/test3.geom")
        res = P.square_visible()
        assert res == approx(36.0)

    def test_tes4_triangle_area(self, capsys):
        P = Polyedr("tests/test4.geom")
        res = P.square_visible()
        assert res == approx(8.0)

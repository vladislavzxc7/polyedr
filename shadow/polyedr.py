from math import pi
from functools import reduce
from operator import add
from common.r3 import R3
from common.tk_drawer import TkDrawer


class Segment:
    """Одномерный отрезок"""

    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin

    def is_degenerate(self):
        return self.beg >= self.fin

    def intersect(self, other):
        if other.beg > self.beg:
            self.beg = other.beg
        if other.fin < self.fin:
            self.fin = other.fin
        return self

    def subtraction(self, other):
        return [
            Segment(self.beg, self.fin if self.fin < other.beg else other.beg),
            Segment(self.beg if self.beg > other.fin else other.fin, self.fin),
        ]


class Edge:
    """Ребро полиэдра"""

    SBEG, SFIN = 0.0, 1.0

    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin
        self.gaps = [Segment(Edge.SBEG, Edge.SFIN)]

    def shadow(self, facet):
        if facet.is_vertical():
            return
        shade = Segment(Edge.SBEG, Edge.SFIN)
        for u, v in zip(facet.vertexes, facet.v_normals()):
            shade.intersect(self.intersect_edge_with_normal(u, v))
            if shade.is_degenerate():
                return

        shade.intersect(
            self.intersect_edge_with_normal(
                facet.vertexes[0], facet.h_normal()
            )
        )
        if shade.is_degenerate():
            return

        gaps = [s.subtraction(shade) for s in self.gaps]
        self.gaps = [s for s in reduce(add, gaps, []) if not s.is_degenerate()]

    def r3(self, t):
        return self.beg * (Edge.SFIN - t) + self.fin * t

    def intersect_edge_with_normal(self, a, n):
        f0, f1 = n.dot(self.beg - a), n.dot(self.fin - a)
        if f0 >= 0.0 and f1 >= 0.0:
            return Segment(Edge.SFIN, Edge.SBEG)
        if f0 < 0.0 and f1 < 0.0:
            return Segment(Edge.SBEG, Edge.SFIN)
        x = -f0 / (f1 - f0)
        return Segment(Edge.SBEG, x) if f0 < 0.0 else Segment(x, Edge.SFIN)


class Facet:
    """Грань полиэдра"""

    def __init__(self, vertexes, orig_vertexes, orig_center, edges=None):
        self.vertexes = vertexes
        self.orig_vertexes = orig_vertexes
        self.orig_center = orig_center
        self.edges = edges if edges is not None else []

    def is_vertical(self):
        if len(self.vertexes) < 3:
            return True
        return self.h_normal().dot(Polyedr.V) == 0.0

    def h_normal(self):
        n = (self.vertexes[1] - self.vertexes[0]).cross(
            self.vertexes[2] - self.vertexes[0]
        )
        return n * (-1.0) if n.dot(Polyedr.V) < 0.0 else n

    def v_normals(self):
        return [self._vert(x) for x in range(len(self.vertexes))]

    def _vert(self, k):
        n = (self.vertexes[k] - self.vertexes[k - 1]).cross(Polyedr.V)
        return (
            n * (-1.0)
            if n.dot(self.vertexes[k - 1] - self.center()) < 0.0
            else n
        )

    def center(self):
        return sum(self.vertexes, R3(0.0, 0.0, 0.0)) * (
            1.0 / len(self.vertexes)
        )


class Polyedr:
    """Полиэдр"""

    V = R3(0.0, 0.0, 1.0)

    def __init__(self, file):
        self.vertexes, self.orig_vertexes, self.edges, self.facets = (
            [],
            [],
            [],
            [],
        )

        with open(file) as f:
            for i, line in enumerate(f):
                if i == 0:
                    buf = line.split()
                    c = float(buf.pop(0))
                    alpha, beta, gamma = (float(x) * pi / 180.0 for x in buf)
                elif i == 1:
                    nv, nf, ne = (int(x) for x in line.split())
                elif i < nv + 2:
                    x, y, z = (float(x) for x in line.split())

                    self.orig_vertexes.append(R3(x, y, z))

                    self.vertexes.append(
                        self.orig_vertexes[-1].rz(alpha).ry(beta).rz(gamma) * c
                    )
                else:
                    buf = line.split()
                    size = int(buf.pop(0))
                    vertexes_trans = [self.vertexes[int(n) - 1] for n in buf]
                    vertexes_orig = [
                        self.orig_vertexes[int(n) - 1] for n in buf
                    ]

                    orig_center = sum(vertexes_orig, R3(0.0, 0.0, 0.0)) * (
                        1.0 / len(vertexes_orig)
                    )

                    facet_edges = []
                    for n in range(size):
                        edge = Edge(vertexes_trans[n - 1], vertexes_trans[n])
                        self.edges.append(edge)
                        facet_edges.append(edge)

                    self.facets.append(
                        Facet(
                            vertexes_trans,
                            vertexes_orig,
                            orig_center,
                            facet_edges,
                        )
                    )

    def square_visible(self):
        for e in self.edges:
            e.gaps = [Segment(Edge.SBEG, Edge.SFIN)]
            for f in self.facets:
                e.shadow(f)

        result_area = 0
        eps = 1e-7

        for facet in self.facets:
            flag_visible = True
            for edge in facet.edges:
                if (
                    len(edge.gaps) != 1
                    or edge.gaps[0].beg > eps
                    or edge.gaps[0].fin < 1 - eps
                ):
                    flag_visible = False
                    break

            if not flag_visible:
                continue

            c = facet.orig_center
            if abs(c.x) > 0.5 or abs(c.y) > 0.5 or abs(c.z) > 0.5:
                vs = facet.orig_vertexes
                n = len(vs)
                if n < 3:
                    continue

                v0_x, v0_y = vs[0].x, vs[0].y
                area = 0
                for i in range(1, n - 1):
                    v1_x, v1_y = vs[i].x, vs[i].y
                    v2_x, v2_y = vs[i + 1].x, vs[i + 1].y
                    cross_z = (v1_x - v0_x) * (v2_y - v0_y) - (v1_y - v0_y) * (
                        v2_x - v0_x
                    )
                    area += abs(cross_z) * 0.5

                result_area += area

        print(f"{result_area:.4f}")
        return result_area

    def draw(self, tk):  # pragma: no cover
        tk.clean()
        for e in self.edges:
            for f in self.facets:
                e.shadow(f)
            for s in e.gaps:
                tk.draw_line(e.r3(s.beg), e.r3(s.fin))
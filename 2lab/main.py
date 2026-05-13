import math
from functools import reduce, wraps
from itertools import count, islice, chain, tee, combinations
from typing import Iterable, Iterator, Callable, Tuple, List, Sequence, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


Point = Tuple[float, float]
Polygon = Tuple[Point, ...]


def pairwise_cyclic(poly: Polygon) -> Iterator[Tuple[Point, Point]]:
    return zip(poly, poly[1:] + poly[:1])


def distance(p1: Point, p2: Point) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def polygon_perimeter(poly: Polygon) -> float:
    return sum(distance(a, b) for a, b in pairwise_cyclic(poly))


def polygon_area(poly: Polygon) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in pairwise_cyclic(poly))) / 2.0


def polygon_centroid(poly: Polygon) -> Point:
    area2 = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in pairwise_cyclic(poly))
    if abs(area2) < 1e-12:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    cx = sum((x1 + x2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in pairwise_cyclic(poly)) / (3 * area2)
    cy = sum((y1 + y2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in pairwise_cyclic(poly)) / (3 * area2)
    return (cx, cy)


def side_lengths(poly: Polygon) -> Tuple[float, ...]:
    return tuple(distance(a, b) for a, b in pairwise_cyclic(poly))


def dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def angle_at(prev_p: Point, p: Point, next_p: Point) -> float:
    v1 = sub(prev_p, p)
    v2 = sub(next_p, p)
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cosv = max(-1.0, min(1.0, dot(v1, v2) / (n1 * n2)))
    return math.acos(cosv)


def polygon_angles(poly: Polygon) -> Tuple[float, ...]:
    n = len(poly)
    return tuple(angle_at(poly[(i - 1) % n], poly[i], poly[(i + 1) % n]) for i in range(n))


def bounding_box(poly: Polygon) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def point_on_segment(p: Point, a: Point, b: Point, eps: float = 1e-9) -> bool:
    if abs(cross(a, b, p)) > eps:
        return False
    return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps and
            min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps)


def segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point, eps: float = 1e-9) -> bool:
    d1 = cross(a1, a2, b1)
    d2 = cross(a1, a2, b2)
    d3 = cross(b1, b2, a1)
    d4 = cross(b1, b2, a2)

    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True

    if abs(d1) <= eps and point_on_segment(b1, a1, a2, eps):
        return True
    if abs(d2) <= eps and point_on_segment(b2, a1, a2, eps):
        return True
    if abs(d3) <= eps and point_on_segment(a1, b1, b2, eps):
        return True
    if abs(d4) <= eps and point_on_segment(a2, b1, b2, eps):
        return True

    return False


def point_in_convex_polygon(point: Point, poly: Polygon, strict: bool = False, eps: float = 1e-9) -> bool:
    n = len(poly)
    if n < 3:
        return False

    signs = []
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        c = cross(a, b, point)
        if abs(c) <= eps:
            if point_on_segment(point, a, b, eps):
                return not strict
            c = 0.0
        if abs(c) > eps:
            signs.append(c > 0)

    if not signs:
        return not strict

    return all(s == signs[0] for s in signs)


def polygons_intersect(poly1: Polygon, poly2: Polygon) -> bool:
    for a1, a2 in pairwise_cyclic(poly1):
        for b1, b2 in pairwise_cyclic(poly2):
            if segments_intersect(a1, a2, b1, b2):
                return True

    if flt_convex_polygon(poly1) and point_in_convex_polygon(poly1[0], poly2):
        return True
    if flt_convex_polygon(poly2) and point_in_convex_polygon(poly2[0], poly1):
        return True

    return False


def visualize_polygons(
    polygons: Iterable[Polygon],
    title: str = "Polygons",
    figsize: Tuple[int, int] = (10, 8),
    facecolors: Optional[Sequence[str]] = None,
    edgecolor: str = "black",
    alpha: float = 0.5,
    show_vertices: bool = False,
) -> None:
    polys = list(polygons)
    fig, ax = plt.subplots(figsize=figsize)

    if not polys:
        ax.set_title(title + " (empty)")
        ax.set_aspect("equal")
        ax.grid(True)
        plt.show()
        return

    if facecolors is None:
        palette = ["#ff9999", "#99ccff", "#99ff99", "#ffcc99", "#d9b3ff", "#ffd966", "#a4c2f4"]
    else:
        palette = list(facecolors)

    for i, poly in enumerate(polys):
        patch = MplPolygon(poly, closed=True, facecolor=palette[i % len(palette)],
                           edgecolor=edgecolor, alpha=alpha, linewidth=1.5)
        ax.add_patch(patch)
        if show_vertices:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            ax.plot(xs + [xs[0]], ys + [ys[0]], "ko", markersize=3)

    min_x = min(x for poly in polys for x, _ in poly)
    max_x = max(x for poly in polys for x, _ in poly)
    min_y = min(y for poly in polys for _, y in poly)
    max_y = max(y for poly in polys for _, y in poly)

    pad_x = max(1.0, (max_x - min_x) * 0.1)
    pad_y = max(1.0, (max_y - min_y) * 0.1)

    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.set_title(title)
    plt.show()



def regular_polygon(n: int, center: Point = (0.0, 0.0), radius: float = 1.0,
                    angle0: float = 0.0) -> Polygon:
    cx, cy = center
    return tuple(
        (
            cx + radius * math.cos(angle0 + 2 * math.pi * k / n),
            cy + radius * math.sin(angle0 + 2 * math.pi * k / n),
        )
        for k in range(n)
    )


def gen_rectangle(width: float = 2.0, height: float = 1.0, gap: float = 1.0,
                  start: Point = (0.0, 0.0), direction: Point = (1.0, 0.0)) -> Iterator[Polygon]:
    dx, dy = direction
    norm = math.hypot(dx, dy)
    ux, uy = dx / norm, dy / norm
    step = width + gap
    x0, y0 = start

    return map(
        lambda i: (
            (x0 + i * step * ux, y0 + i * step * uy),
            (x0 + i * step * ux + width, y0 + i * step * uy),
            (x0 + i * step * ux + width, y0 + i * step * uy + height),
            (x0 + i * step * ux, y0 + i * step * uy + height),
        ),
        count(0)
    )


def gen_triangle(side: float = 2.0, gap: float = 1.0,
                 start: Point = (0.0, 0.0), direction: Point = (1.0, 0.0)) -> Iterator[Polygon]:
    dx, dy = direction
    norm = math.hypot(dx, dy)
    ux, uy = dx / norm, dy / norm
    h = math.sqrt(3) * side / 2
    step = side + gap
    x0, y0 = start

    return map(
        lambda i: (
            (x0 + i * step * ux, y0 + i * step * uy),
            (x0 + i * step * ux + side, y0 + i * step * uy),
            (x0 + i * step * ux + side / 2, y0 + i * step * uy + h),
        ),
        count(0)
    )


def gen_hexagon(side: float = 1.0, gap: float = 1.0,
                start: Point = (0.0, 0.0), direction: Point = (1.0, 0.0)) -> Iterator[Polygon]:
    dx, dy = direction
    norm = math.hypot(dx, dy)
    ux, uy = dx / norm, dy / norm
    radius = side
    width = 2 * radius
    step = width + gap
    x0, y0 = start

    return map(
        lambda i: regular_polygon(
            6,
            center=(x0 + i * step * ux + radius, y0 + i * step * uy + radius),
            radius=radius,
            angle0=math.pi / 6,
        ),
        count(0)
    )



def transform_polygon(poly: Polygon, point_fn: Callable[[Point], Point]) -> Polygon:
    return tuple(map(point_fn, poly))


def tr_translate(dx: float, dy: float) -> Callable[[Polygon], Polygon]:
    return lambda poly: transform_polygon(poly, lambda p: (p[0] + dx, p[1] + dy))


def tr_rotate(angle: float, center: Point = (0.0, 0.0)) -> Callable[[Polygon], Polygon]:
    cx, cy = center
    c = math.cos(angle)
    s = math.sin(angle)

    def point_fn(p: Point) -> Point:
        x, y = p[0] - cx, p[1] - cy
        return (cx + x * c - y * s, cy + x * s + y * c)

    return lambda poly: transform_polygon(poly, point_fn)


def tr_symmetry(axis: str = "x", line_value: float = 0.0) -> Callable[[Polygon], Polygon]:
    if axis == "x":
        return lambda poly: transform_polygon(poly, lambda p: (p[0], 2 * line_value - p[1]))
    if axis == "y":
        return lambda poly: transform_polygon(poly, lambda p: (2 * line_value - p[0], p[1]))
    if axis == "origin":
        return lambda poly: transform_polygon(poly, lambda p: (-p[0], -p[1]))
    if axis == "y=x":
        return lambda poly: transform_polygon(poly, lambda p: (p[1], p[0]))
    if axis == "y=-x":
        return lambda poly: transform_polygon(poly, lambda p: (-p[1], -p[0]))
    raise ValueError("axis must be one of: 'x', 'y', 'origin', 'y=x', 'y=-x'")


def tr_homothety(k: float, center: Point = (0.0, 0.0)) -> Callable[[Polygon], Polygon]:
    cx, cy = center
    return lambda poly: transform_polygon(poly, lambda p: (cx + k * (p[0] - cx), cy + k * (p[1] - cy)))


def flt_convex_polygon(poly: Polygon) -> bool:
    if len(poly) < 3:
        return False
    vals = []
    for i in range(len(poly)):
        o = poly[i]
        a = poly[(i + 1) % len(poly)]
        b = poly[(i + 2) % len(poly)]
        c = cross(o, a, b)
        if abs(c) > 1e-9:
            vals.append(c > 0)
    return bool(vals) and all(v == vals[0] for v in vals)


def flt_angle_point(point: Point) -> Callable[[Polygon], bool]:
    return lambda poly: any(distance(v, point) < 1e-9 for v in poly)


def flt_square(max_area: float) -> Callable[[Polygon], bool]:
    return lambda poly: polygon_area(poly) < max_area


def flt_short_side(max_length: float) -> Callable[[Polygon], bool]:
    return lambda poly: min(side_lengths(poly)) < max_length


def flt_point_inside(point: Point) -> Callable[[Polygon], bool]:
    return lambda poly: flt_convex_polygon(poly) and point_in_convex_polygon(point, poly)


def flt_polygon_angles_inside(other: Polygon) -> Callable[[Polygon], bool]:
    return lambda poly: flt_convex_polygon(poly) and any(point_in_convex_polygon(v, poly) for v in other)


def _decorate_iterables(args, kwargs, iterable_transform: Callable[[Iterable[Polygon]], Iterable[Polygon]]):
    new_args = [
        iterable_transform(a) if hasattr(a, "__iter__") and not isinstance(a, (str, bytes, tuple)) else a
        for a in args
    ]
    new_kwargs = {
        k: iterable_transform(v) if hasattr(v, "__iter__") and not isinstance(v, (str, bytes, tuple)) else v
        for k, v in kwargs.items()
    }
    return new_args, new_kwargs


def polygon_filter_decorator(filter_fn: Callable[[Polygon], bool]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            new_args, new_kwargs = _decorate_iterables(args, kwargs, lambda it: filter(filter_fn, it))
            return func(*new_args, **new_kwargs)
        return wrapper
    return decorator


def polygon_transform_decorator(transform_fn: Callable[[Polygon], Polygon]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            new_args, new_kwargs = _decorate_iterables(args, kwargs, lambda it: map(transform_fn, it))
            return func(*new_args, **new_kwargs)
        return wrapper
    return decorator


def dec_flt_convex_polygon(func=None):
    dec = polygon_filter_decorator(flt_convex_polygon)
    return dec if func is None else dec(func)


def dec_flt_angle_point(point: Point):
    return polygon_filter_decorator(flt_angle_point(point))


def dec_flt_square(max_area: float):
    return polygon_filter_decorator(flt_square(max_area))


def dec_flt_short_side(max_length: float):
    return polygon_filter_decorator(flt_short_side(max_length))


def dec_flt_point_inside(point: Point):
    return polygon_filter_decorator(flt_point_inside(point))


def dec_flt_polygon_angles_inside(other: Polygon):
    return polygon_filter_decorator(flt_polygon_angles_inside(other))


def dec_tr_translate(dx: float, dy: float):
    return polygon_transform_decorator(tr_translate(dx, dy))


def dec_tr_rotate(angle: float, center: Point = (0.0, 0.0)):
    return polygon_transform_decorator(tr_rotate(angle, center))


def dec_tr_symmetry(axis: str = "x", line_value: float = 0.0):
    return polygon_transform_decorator(tr_symmetry(axis, line_value))


def dec_tr_homothety(k: float, center: Point = (0.0, 0.0)):
    return polygon_transform_decorator(tr_homothety(k, center))


def take(n: int, iterable: Iterable[Polygon]) -> List[Polygon]:
    return list(islice(iterable, n))


def line_band_polygons(base_iter: Iterable[Polygon], angle: float, offset: Point = (0.0, 0.0)) -> Iterator[Polygon]:
    return map(
        lambda poly: tr_translate(*offset)(tr_rotate(angle)(poly)),
        base_iter
    )


def no_intersections_filter(polygons: Iterable[Polygon]) -> List[Polygon]:
    selected = []
    for poly in polygons:
        if all(not polygons_intersect(poly, s) for s in selected):
            selected.append(poly)
    return selected


def demo_generators():
    rects = take(7, gen_rectangle(width=2, height=1, gap=0.7, start=(0, 0)))
    tris = take(7, gen_triangle(side=2, gap=0.7, start=(0, 3)))
    hexs = take(7, gen_hexagon(side=1, gap=1.0, start=(0, 7)))

    visualize_polygons(rects, "7 прямоугольников")
    visualize_polygons(tris, "7 треугольников")
    visualize_polygons(hexs, "7 шестиугольников")


def demo_transformations():
    base = gen_rectangle(width=1.8, height=0.8, gap=0.5, start=(0, 0))
    band1 = take(7, line_band_polygons(base, angle=math.radians(30), offset=(0, 0)))
    base = gen_rectangle(width=1.8, height=0.8, gap=0.5, start=(0, 0))
    band2 = take(7, line_band_polygons(base, angle=math.radians(30), offset=(0, 2)))
    base = gen_rectangle(width=1.8, height=0.8, gap=0.5, start=(0, 0))
    band3 = take(7, line_band_polygons(base, angle=math.radians(30), offset=(0, 4)))
    visualize_polygons(chain(band1, band2, band3), "Три параллельные ленты под острым углом")

    base1 = gen_rectangle(width=1.8, height=0.8, gap=0.3, start=(-2, 2))
    base2 = gen_rectangle(width=1.8, height=0.8, gap=0.3, start=(1, -3))
    tape1 = take(8, map(tr_rotate(math.radians(35), center=(2, 2)), base1))
    tape2 = take(8, map(tr_rotate(math.radians(120), center=(2, 2)), base2))
    visualize_polygons(chain(tape1, tape2), "Две пересекающиеся ленты прямоугольников")

    base3 = take(8, line_band_polygons(gen_triangle(side=1.7, gap=0.5, start=(0, 0)), angle=math.radians(20), offset=(0, 2)))
    base4 = list(map(tr_symmetry("x", line_value=0.0), base3))
    visualize_polygons(chain(base3, base4), "Параллельные симметричные ленты треугольников")

    quad = ((1.0, 0.5), (2.0, 1.0), (1.6, 2.2), (0.8, 1.4))
    scales = [0.7, 1.0, 1.4, 1.9, 2.5, 3.2]
    quads = list(map(lambda k: tr_homothety(k, center=(0, 0))(quad), scales))
    quads = list(filter(lambda p: all(0.3 * x <= y <= 2.5 * x for x, y in p if x >= 0), quads))
    visualize_polygons(quads, "Четырехугольники разного масштаба между двумя прямыми")


def demo_filters():
    base = chain(
        take(10, line_band_polygons(gen_rectangle(width=1.2, height=0.7, gap=0.4), math.radians(25), (0, 0))),
        take(10, line_band_polygons(gen_triangle(side=1.6, gap=0.5), math.radians(25), (0, 3)))
    )
    filtered1 = list(islice(filter(flt_square(1.5), base), 6))
    visualize_polygons(filtered1, "Фильтрация из фигур п.4: ровно 6 фигур")

    quad = ((1.0, 0.5), (2.0, 1.0), (1.8, 2.0), (0.7, 1.4))
    many_scaled = map(lambda k: tr_homothety(k, center=(0, 0))(quad), [0.2 + i * 0.15 for i in range(15)])
    filtered2 = list(islice(filter(flt_short_side(0.9), many_scaled), 4))
    visualize_polygons(filtered2, "<=4 из >=15 по кратчайшей стороне")

    overlapping = list(
        map(
            tr_translate(0.25, 0.2),
            take(15, gen_hexagon(side=1.2, gap=-1.5, start=(0, 0)))
        )
    )
    non_intersecting = no_intersections_filter(overlapping)
    visualize_polygons(overlapping, "15 пересекающихся фигур")
    visualize_polygons(non_intersecting, "После удаления пересекающихся фигур")


def demo_decorators():
    @dec_tr_translate(5, 0)
    @dec_tr_rotate(math.radians(20))
    @dec_flt_square(2.0)
    def collect_first_n(polys: Iterable[Polygon], n: int) -> List[Polygon]:
        return take(n, polys)

    result = collect_first_n(gen_triangle(side=1.6, gap=0.4), 6)
    visualize_polygons(result, "Декораторы: фильтрация + трансформации")

    @dec_flt_convex_polygon
    @dec_flt_point_inside((1.5, 1.0))
    def collect(polys: Iterable[Polygon]) -> List[Polygon]:
        return list(polys)

    sample = [
        ((0, 0), (4, 0), (4, 3), (0, 3)),
        ((5, 5), (6, 5), (6, 6), (5, 6)),
        ((0, 0), (3, 0), (1, 1), (3, 3), (0, 3)),
    ]
    result2 = collect(iter(sample))
    visualize_polygons(result2, "Декораторы-фильтры")

def main():
    demo_generators()
    demo_transformations()
    demo_filters()
    demo_decorators()


if __name__ == "__main__":
    main()

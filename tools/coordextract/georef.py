"""Affine georeferencing: pixel coordinates -> real-world (projected) coordinates.

The user supplies control points (pixel -> known X/Y from the map grid labels).
We fit a 2D affine transform by least squares and then map arbitrary pixels
(e.g. polygon vertices) to real X/Y.

    X = a*px + b*py + c
    Y = d*px + e*py + f

Two control points give an under-determined system; three non-collinear points
give an exact affine fit; more points are solved in a least-squares sense, and
a residual (RMSE) is reported so the user can judge accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np


@dataclass
class ControlPoint:
    px: float  # pixel x (in ORIGINAL image space)
    py: float  # pixel y
    X: float   # real-world easting / X
    Y: float   # real-world northing / Y


class GeoReferenceError(Exception):
    pass


@dataclass
class AffineModel:
    """Full 6-parameter affine transform pixel -> world."""

    # coefficients for X and Y
    ax: float
    bx: float
    cx: float
    ay: float
    by: float
    cy: float
    rmse: float          # overall residual on the control points (world units)
    n_points: int

    def apply(self, px: float, py: float) -> Tuple[float, float]:
        X = self.ax * px + self.bx * py + self.cx
        Y = self.ay * px + self.by * py + self.cy
        return X, Y

    def apply_many(self, pts: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
        return [self.apply(px, py) for px, py in pts]


def _fit_axis(A: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Least-squares solve A @ coef = target. Returns (coef, predictions)."""
    coef, *_ = np.linalg.lstsq(A, target, rcond=None)
    pred = A @ coef
    return coef, pred


def fit_affine(points: Sequence[ControlPoint]) -> AffineModel:
    """Fit an affine model from >=3 non-collinear control points.

    For exactly 2 points we fall back to a similarity transform (uniform scale +
    rotation + translation), which is the best you can do with two points.
    """
    n = len(points)
    if n < 2:
        raise GeoReferenceError(
            "geo-referencing needs at least 2 control points "
            "(3+ recommended for a full affine fit)."
        )

    px = np.array([p.px for p in points], dtype=float)
    py = np.array([p.py for p in points], dtype=float)
    X = np.array([p.X for p in points], dtype=float)
    Y = np.array([p.Y for p in points], dtype=float)

    if n == 2:
        return _fit_similarity(px, py, X, Y)

    # Full affine: design matrix [px, py, 1]
    A = np.column_stack([px, py, np.ones(n)])

    # Guard against collinear / degenerate control points.
    if np.linalg.matrix_rank(A) < 3:
        raise GeoReferenceError(
            "control points are collinear (or coincident); "
            "pick points that are spread out, not on one line."
        )

    cx, predX = _fit_axis(A, X)
    cy, predY = _fit_axis(A, Y)

    resid = np.concatenate([predX - X, predY - Y])
    rmse = float(np.sqrt(np.mean(resid ** 2)))

    return AffineModel(
        ax=cx[0], bx=cx[1], cx=cx[2],
        ay=cy[0], by=cy[1], cy=cy[2],
        rmse=rmse, n_points=n,
    )


def _fit_similarity(px, py, X, Y) -> AffineModel:
    """Similarity transform from exactly 2 point correspondences.

        X = s*cos*px - s*sin*py + tx      -> X =  a*px - b*py + tx
        Y = s*sin*px + s*cos*py + ty      -> Y =  b*px + a*py + ty
    """
    dpx = px[1] - px[0]
    dpy = py[1] - py[0]
    dX = X[1] - X[0]
    dY = Y[1] - Y[0]

    denom = dpx ** 2 + dpy ** 2
    if denom == 0:
        raise GeoReferenceError("the two control points are at the same pixel.")

    a = (dpx * dX + dpy * dY) / denom
    b = (dpx * dY - dpy * dX) / denom
    tx = X[0] - (a * px[0] - b * py[0])
    ty = Y[0] - (b * px[0] + a * py[0])

    return AffineModel(
        ax=a, bx=-b, cx=tx,
        ay=b, by=a, cy=ty,
        rmse=0.0, n_points=2,
    )


def polygon_area(coords: Sequence[Tuple[float, float]]) -> float:
    """Shoelace area for a closed polygon given world coordinates (map units^2)."""
    n = len(coords)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0

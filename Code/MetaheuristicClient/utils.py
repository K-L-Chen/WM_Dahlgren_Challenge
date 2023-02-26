"""
This file contains some utility functions for the AI, to make the code more consise
"""

"""@cvar MAX_DISTANCE A maximum distance between two entities"""
MAX_DISTANCE = 5e9

"""@cvar DISTANCE_SCALE A scaling factor for the distance so that it is not enormous"""
DISTANCE_SCALE = 1e-7

def distance(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
    """
    Computes the square of the Euclidean distance between two 3D points.

    @param x1: The x coordinate for the first point
    @param y1: The y coordinate for the first point
    @param z1: The z coordinate for the first point
    @param x2: The x coordinate for the second point
    @param y2: The y coordinate for the second point
    @param z2: The z coordinate for the second point

    @return: The square of the Euclidean distance between two 3D points.
    """
    return (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2) + (z1 - z2) * (z1 - z2)


def magnitude(m1: float, m2: float, m3: float) -> float:
    """
    Computes the square of the magnitude of a velocity vector.

    @param m1: The X component of the velocity vector
    @param m2: The Y component of the velocity vector
    @param m3: The Z component of the velocity vector

    @return: The square of the magnitude of a velocity vector.
    """
    return m1 * m1 + m2 * m2 + m3 * m3


def dot(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
    """
    Computes the dot product between two 3D vectors.

    @param x1: The x component for the first vector
    @param y1: The y component for the first vector
    @param z1: The z component for the first vector
    @param x2: The x component for the second vector
    @param y2: The y component for the second vector
    @param z2: The z component for the second vector

    @return: The square of the Euclidean distance between two 3D vectors.
    """
    return x1 * x2 + y1 * y2 + z1 * z2
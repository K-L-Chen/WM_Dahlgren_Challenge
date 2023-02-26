"""
This file contains some utility functions for AIManager.py, to make code more concise.

"""


def distance(x1, y1, z1, x2, y2, z2):
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

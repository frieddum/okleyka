"""Approximate price bands per ordinary bottle/can, never per litre."""
from bisect import bisect_left

LIMITS = {"bottle": (1000, 3000, 6000, 15000), "beer": (150, 300, 500, 1000)}


def level(price, scale):
    if price <= 0:
        raise ValueError("Price must be positive")
    return bisect_left(LIMITS[scale], price) + 1


def ordinary_volume(ml, scale):
    return (450 <= ml <= 568) if scale == "beer" else (700 <= ml <= 1000)

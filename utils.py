import numpy as np

def euclidean_distance(loc1, loc2):
    return np.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

def get_traffic_delay(loc, traffic_zones):
    for zone in traffic_zones:
        zx, zy, radius, multiplier = zone
        if euclidean_distance(loc, (zx, zy)) <= radius:
            return multiplier
    return 1.0
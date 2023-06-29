import os
from math import pow, sqrt

distance_between_points = int(os.environ.get('DISTANCE_BETWEEN_POINTS'))

def delta(init, fin):
    return fin - init

def distance(init_x, init_y, fin_x, fin_y):
    deltaX = delta(init_x, fin_x)
    deltaY = delta(init_y, fin_y)

    return sqrt(pow(deltaX, 2) + pow(deltaY, 2)) * 1000

def generate_extra_points(coordinates):
    
    new_coordinates = []
    
    for i in range(len(coordinates)-1):

        latitude_in     = coordinates[i][1]
        longitude_in    = coordinates[i][0]

        latitude_fin    = coordinates[i+1][1]
        longitude_fin   = coordinates[i+1][0]

        new_coordinates.append(coordinates[i])

        deltaLat = delta(latitude_in, latitude_fin)
        deltaLon = delta(longitude_in, longitude_fin)

        dist        = distance(latitude_in, longitude_in, latitude_fin, longitude_fin)
        n_points    = int(dist / distance_between_points)

        print(n_points)

        t1 = 0
        t2 = n_points

        for t in range(t1, t2, 1):

            t0_1 = (t - t1) / (t2 - t1)
            latInter = latitude_in  + deltaLat * t0_1
            lonInter = longitude_in + deltaLon * t0_1

            new_coordinates.append([lonInter, latInter])

    new_coordinates.append(coordinates[-1])
                
    return new_coordinates






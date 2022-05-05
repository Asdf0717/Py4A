from random import random

N = 1000000
inside = 0

for i in range(0, N):
    (x, y) = (random(), random())
    if x**2 + y**2 < 1:
        inside = inside + 1

print(4.0 * inside / N)

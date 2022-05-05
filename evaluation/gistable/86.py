# couple things I'd throw in there:
# moar whitespace
res = [
    [
        [
            kriger.predict(x,y,z)
            for x in grid[0]
        ]
        for y in grid[1]
    ]
    for z in grid[2]
]
# sure it looks big, but lines are cheap and they make the loops far more grokkable

# moar intermediate variables. 
# One way to do this (This doesn't help too much here but if x,y, and z correspond to more interesting column names it might)
exes, whys, zees = grid
...
# another way, using map, itertools and more intermediate variables:
prediction_inputs = zip(itertools.product(*grid)) # You could flatten this out here with xs, ys, zs = zip(...)
predictions = map(kriger.predict, *prediction_inputs)
predictions_grid = array(predictions).reshape(*grid.dimensions)
# ^ not sure what you're using this output format for, but it seems like it's the reason for a large part of the 
# awkwardness of what you're trying to to. Take the reshape out onto its own line to encapsulate the craziness 
# separate from the beauty of the actual predictions you're doing

# and of course, you can always
import antigravity
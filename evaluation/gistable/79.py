#!/usr/bin/env python3

# Two solutions to http://www.bittorrent.com/company/about/developer_challenge

from itertools import combinations

bowls   = 40
oranges = 9

def brute_force():
    '''A brute force method. There are only about a quarter billion
    possibilities to examine so this is not completely untenable. Runs
    in a bit over half an hour on my machine.'''
    return sum(all(b - a != c - b for a,b,c in combinations(p, 3)) 
               for p in combinations(range(bowls), oranges))

def less_dumb():
    '''A slightly less dumb version that builds up legal positionings
    by figuring out all the places the next orange can go given a list
    of already-positioned oranges. Also we only generate positionings
    with the first orange in the first bowl and then know that each
    such positioning can be shifted into N different actual positions
    where N is one plus the number of empty bowls after the last
    orange. Runs in about a minute on my machine.'''

    def nexts(placed):
        '''Return legal positions the next orange can go.'''

        def ok(next):
            '''Check one possible position for the next orange.'''
            for i in reversed(range(len(placed))):
                previous = placed[i]
                distance = next - previous
                possible_problem  = previous - distance
                if possible_problem < 0:
                    return True
                else:
                    for j in range(i - 1, -1, -1):
                        other = placed[j]
                        if other == possible_problem: return False
                        elif other < possible_problem: break;
            return True

        return filter(ok, range(placed[-1] + 1, bowls))

    def count(placed):
        '''Recursively count the number of solutions.'''
        if len(placed) < oranges:
            return sum(count(placed + [n]) for n in nexts(placed))
        else:
            return bowls - placed[-1]

    return count([0])

if __name__ == '__main__':

    from timeit import timeit
    print('Brute force: {}'.format(timeit(lambda: print(brute_force()), number=1)))
    print('Less dumb:   {}'.format(timeit(lambda: print(less_dumb()), number=1)))

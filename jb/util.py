import functools
import operator

def powerOfTwoEqualOrMoreThan(n):
    o = 2
    while o < n:
        o *= 2
    return o

# TODO just make this recursive to handle any number of dimensions
def unflattenArray(a, dims):
    def chunkify_array(ia, chunksize):
        oa = []
        for i in range(int(len(ia)/ chunksize)):
            start = i * chunksize
            end   = start + chunksize
            oa.append(ia[start:end])
        return oa

    dimlen = len(dims)
    if dimlen == 1:
        if dims[0] == 1:
            return a[0]
        else:
            return a
    elif dimlen == 2:
        return chunkify_array(a, dims[1])
    elif dimlen == 3:
        v0 = chunkify_array(a, dims[2])
        v1 = chunkify_array(v0, dims[1])
        return v1
    elif dimlen == 4:
        v0 = chunkify_array(a, dims[3])
        v1 = chunkify_array(v0, dims[2])
        v2 = chunkify_array(v0, dims[1])
        return v2
 
def flattenArrays(a):
    if not isinstance(a,(list, tuple)):
        return [a]
    elif isinstance(a[0], (list, tuple)):
        return functools.reduce(lambda x, y: x + flattenArrays(y), a, []) 
    else:
        return a


def is_scalar(m_info):
    counts = m_info.get('counts',[1])
    return len(counts) == 1 and not isinstance(counts[0],(list, tuple)) and counts[0] == 1


def total_array_count(m_info):
    return functools.reduce(operator.mul, m_info['counts'])

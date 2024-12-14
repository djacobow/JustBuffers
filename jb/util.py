import functools
import operator
import subprocess

def get_shell_output(args, **runargs):
    runargs['stdout'] = subprocess.PIPE
    r = subprocess.run(args, **runargs)
    return (r.returncode, r.stdout.decode("utf-8", errors="ignore"))
    

def powerOfTwoEqualOrMoreThan(n):
    o = 2
    while o < n:
        o *= 2
    return o

# TODO just make this recursive to handle any number of dimensions


# takes a one dimensional list and a list of dimensions and turns
# it into an n-dimensional list of lists of list ...
def unflattenArray(a, dims):
    def chunkify_array(ia, chunksize):
        oa = []
        for i in range(int(len(ia)/ chunksize)):
            start = i * chunksize
            end   = start + chunksize
            oa.append(ia[start:end])
        return oa

    if len(dims) == 0:
        return a[0]
    else:
        ca = chunkify_array(a,dims[-1])
        ua = unflattenArray(ca, dims[:-1])
        # a list of one item is a special case. It's will be converted
        # into a scalar
        if len(ua) == 1 and not isinstance(ua[0],list):
            return ua[0]
        return ua


# takes an n-dimensional list of list of list.. and turns it into
# just one list
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

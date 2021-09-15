import numpy
import pandas as pd
print("Hello tester")
# Stolen from https://dfm.io/posts/autocorr/

def next_pow_two(n):
    i = 1
    while i < n:
        i = i << 1
    return i

def autocorr_func_1d(x, norm=True):
    x = numpy.atleast_1d(x)
    if len(x.shape) != 1:
        raise ValueError("invalid dimensions for 1D autocorrelation function")
    n = next_pow_two(len(x))

    # Compute the FFT and then (from that) the auto-correlation function
    f = numpy.fft.fft(x - numpy.mean(x), n=2*n)
    acf = numpy.fft.ifft(f * numpy.conjugate(f))[:len(x)].real
    acf /= 4*n
    
    # Optionally normalize
    if norm:
        acf /= acf[0]

    return acf

# Automated windowing procedure following Sokal (1989)
def auto_window(taus, c):
    m = numpy.arange(len(taus)) < c * taus
    if numpy.any(m):
        return numpy.argmin(m)
    return len(taus) - 1

# Following the suggestion from Goodman & Weare (2010)
def autocorr_gw2010(y, c=5.0):
    f = autocorr_func_1d(y)
    taus = 2.0*numpy.cumsum(f)-1.0
    window = auto_window(taus, c)
    return taus[window]


def reblock_by_autocorr(y, name = "ETotal"):
    print("# Reblock based on autocorrelation time")
    Nmax = int(numpy.log2(len(y)))
    Ndata = []
    tacs = []
    for i in range(Nmax):
        n = int(len(y)/2**i)
        Ndata += [n]
        tacs += [autocorr_gw2010(y[:n])]
    
    for n, tac in zip(Ndata, tacs):
        print("nsamples, tac = {}, {}".format(n,tac))
    
    block_size = int(numpy.round(numpy.max(tacs)))
    nblocks = len(y) // block_size
    yblocked = []
    
    for i in range(nblocks):
        offset = i*block_size
        yblocked += [numpy.mean(y[offset:offset+block_size])]
    
    yavg = numpy.mean(yblocked)
    ystd = numpy.std(yblocked) / numpy.sqrt(nblocks)

    df = pd.DataFrame({"%s_ac"%name:[yavg], "%s_error_ac"%name:[ystd], "%s_nsamp_ac"%name:[nblocks], "ac":[block_size]})

    return df
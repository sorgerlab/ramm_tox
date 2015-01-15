import numpy as np
import scipy.special

def pearsonr(x, y, pvalue=True):
    """
    Calculates a Pearson correlation coefficient and the p-value for testing
    non-correlation.

    Copied from scipy.stats.pearsonr and vectorized for "wide" x, i.e.
    correlating multiple datasets against y. See the documentation there for
    more information.

    Parameters
    ----------
    x : 2D array
    y : 1D array the same length as x's second dimension
    pvalue : boolean
        If true, p-values will be calculated using Student's t-distribution. If
        false, that calculation will be skipped and there will be only one
        return value instead of two. For small datasets (i.e. length of y is
        small), this method of calculating p-values is unreliable as well as
        expensive to compute relative to the correlation calculation itself, so
        one may with to skip it altogether. Furthermore, when performing a
        permutation test, (the suggested method for calculating p-values for
        small datasets) calculating the p-values is entirely irrelevant and only
        further compounds the computational expense.

    Returns
    -------
    (Pearson's correlation coefficient,
    2-tailed p-value)

    """

    # X is 2-D with shape (v,n), Y is 1-D with length (n)
    # number of samples
    n = len(y)
    # number of variables in X
    v = x.shape[0]
    mx = x.mean(axis=1)
    my = y.mean()
    xm, ym = x-mx[:,None], y-my
    r_num = n*(np.add.reduce(xm*ym, axis=1))
    r_den = n*np.sqrt(np.sum(xm*xm, axis=1)*np.sum(ym*ym))
    r = (r_num / r_den)
    # Presumably, if abs(r) > 1, then it is only some small artifact of floating
    # point arithmetic.
    r = np.maximum(np.minimum(r, 1.0), -1.0)

    df = n-2
    t_squared = r*r * (df / ((1.0 - r) * (1.0 + r)))
    # Save 25% of the overhead of scipy.stats.betai which clamps the upper bound
    # of the 3rd argument to 1.0 (we already know it's always less than 1).
    prob = scipy.special.betainc(0.5*df, 0.5, df / (df + t_squared))

    return r, prob

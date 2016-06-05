import numpy as np
import pandas as pd

__all__ = ['fieldID', 'angSep', 'overlapSummary']


def angSep( ra1, dec1, ra2, dec2):
    """
    Angular separation between to points on a sphere with coordinates ra, dec
    in the usual conditions for astronomy.
    """
    th1 = - dec1 + np.pi / 2.
    th2 = - dec2 + np.pi / 2.
    ph1 = ra1
    ph2 = ra2
    # Take the dot product
    cos = np.sin(th1) * np.sin(th2) * np.cos(ph1 - ph2)\
        + np.cos(th1)*np.cos(th2)
    # Calculate arccos differently to avoid loss of precision
    # sinhalftheta = np.sqrt(0.5*(1.0 - cos))
    # return 2.*(np.arcsin(sinhalftheta))
    return np.arccos(cos)

def overlapSummary(ra, dec, df, sep=1.75, 
                    raCol='fieldRA', decCol='fieldDec'):

    sep = np.radians(sep)

    df['overlap'] = angSep(ra, dec, df[raCol], df[decCol]) < sep
    summary = df[df['overlap']].copy()
    summary.drop('dist', axis=1, inplace=True)
    return summary
def angDistance(ra, dec, df, raCol='fieldRA', decCol='fieldDec'):
    """
    """
    df['dist'] = angSep(ra, dec, df[raCol], df[decCol])
    idx = df.dist.idxmin()
    rval = df.ix[idx]
    df.drop('dist', axis=1, inplace=True)
    return rval

def obsIndex(opsimDF, ra, dec, raCol='fieldRA', decCol='fieldDec',
              pointinRadius=1.75):
    """
    """
    df = opsimDF[['fieldID', raCol, decCol]].copy().drop_duplicates()
    df['dist'] = angSep(ra, dec, df[raCol], df[decCol])
    pointingRad = np.radians(pointinRadius)
    df = df.query('dist < {}'.format(pointingRad))
    return df.index



def fieldID(opsimDF, ra, dec, raCol='fieldRA', decCol='fieldDec'):
    """
    """

    df = opsimDF[['fieldID', raCol, decCol]].copy().drop_duplicates()

    rval = angDistance(ra, dec, df)
    return rval['fieldID']


"""
Class for associating Healpixels with OpSim Pointings. An example of usage can
be found in `examples/ObsHistIDsForTile`
"""
from __future__ import print_function, absolute_import, division
import numpy as np
import healpy as hp
import pandas as pd
from scipy.sparse import csr_matrix
from itertools import repeat 
import sqlite3

__all__  = ['addVec', 'HealPixelizedOpSim']

def addVec(df, raCol='ditheredRA', decCol='ditheredDec'):
    """
    Add a column of vectors to the dataFrame df

    Parameters
    ----------
    df : `pd.DataFrame`
        dataframe with two columns raCol and decCol having ra,
        dec in radians.
    raCol : string, optional, defaults to 'ditheredRA'
        column name for the column which has ra values
    decCol : string, optional, defaults to 'ditheredDec'
        column name for the column which has dec values
    """
    thetas  = - df[decCol] + np.pi /2.
    phis = df[raCol]
    df['vec'] = list(hp.ang2vec(thetas, phis))

class HealPixelizedOpSim(object):
    """
    Class to associate opsim pointings represented as records indexed by an
    integer variable obsHistID, with a set of healpixel tileIds. This class
    computes the (maximal set) of healpixel IDs associated with a certain
    pointing, as also the set of pointings associated with a healpixel ID.


    Parameters
    ----------
    opsimDF : `pd.DataFrame`, mandatory
        a dataframe representing the OpSim records of interest. The mandatory
        columns are an index column (obsHistID), raCol (specified by raCol), 
        dec Col (specified as decCol)
    raCol : string, defaults to 'ditheredRa', col should have units of radians
        column name for column of ras to use 
    decCol : string, defaults to 'ditheredDec', col should have units of radians
        column name for column of dec to use
    NSIDE : integer, `healpy.NSIDE`
        `NSIDE` for healpix giving rise to 12NSIDE **2 pixels on the sphere
    vecColName : string, optional, defaults to 'vec'
        column name where 3D vectors are computed corresponding to the angles
        of the pointing direction of the OpSim record.
    fieldRadius : float, optional, defaults to 1.75, units is degrees
        radius of the field in degrees

    Methods
    -------
    """

    def __init__(self, opsimDF, raCol='ditheredRA', decCol='ditheredDec',
                 NSIDE=1,
                 vecColName='vec',  fieldRadius=1.75):

        self.raCol = raCol
        self.decCol = decCol
        self.opsimdf = opsimDF.reset_index()
        self.cols = opsimDF.columns
        self.vecColName = vecColName
        self.validateDF()
        self._fieldRadius = np.radians(fieldRadius)

        if vecColName not in self.cols:
            addVec(self.opsimdf)
        self.nside = NSIDE
        self.nested = True
        self._rowdata = None
        self._coldata = None
        self._spmat = None

    def obsHistIdsForTile(self, tileID):
        """
        return a `np.ndarray` of obsHistID values that intersect with the
        healpix tileID.
        """
        inds = self.sparseMat.getcol(tileID).nonzero()[0]
        return self.opsimdf.ix[inds, 'obsHistID'].values

    @property
    def sparseMat(self):
        """
        Sparse Matrix representation of the association between the obsHistIDs
        and healpix tileIDs.
        """
        if self._spmat is None:
            shape=(len(self.opsimdf), hp.nside2npix(self.nside))
            # numpy ones like number of intersections
            ones_int = np.ones(len(self.rowdata))
            self._spmat = csr_matrix((ones_int, (self.rowdata, self.coldata)),
                                     shape=shape)
        return self._spmat 

    @property
    def rowdata(self):
        if self._rowdata is None:
            self.doPreCalcs()
        return np.asarray(self._rowdata)


    @property
    def coldata(self):
        if self._coldata is None:
            self.doPreCalcs()
        return self._coldata

    def writeToDB(self, dbName):
        """
        Write association of obsHistIDs and Healpix TileIDs to a SQLITE
        database with absolute path dbName. This is thus a two column database.

        Parameters
        ----------
        dbName : string, mandatory
            absolute path to the location of the database to be written

        .. notes : It is assumed that the file does not exist but the directory
        does.
        """
        rowdata = self.rowdata
        coldata = self.coldata
        obsHistIDs = self.opsimdf.ix[rowdata, 'obsHistID'].values

        conn = sqlite3.Connection(dbName)
        cur = conn.cursor()
        cur.execute('CREATE TABLE simlib (ipix int, obsHistId int)')
        for i in range(len(rowdata)):
            cur.execute('INSERT INTO simlib VALUES'
                        '({1}, {0})'.format(obsHistIDs[i], coldata[i]))
            if i % 10000000 == 0:
                conn.commit()
        conn.commit()
        print('Committed the table to disk\n')
        # create index
        print('Createing ipix index\n')
        cur.execute('CREATE INDEX {ix} on {tn}({cn})'\
                    .format(ix='ipix_ind', tn='simlib', cn='ipix'))
        print('Createing obsHistID index\n')
        cur.execute('CREATE INDEX {ix} on {tn}({cn})'\
                .format(ix='obshistid_ind', tn='simlib', cn='obsHistId'))
        conn.close()
        
    def doPreCalcs(self):
        """
        Perform the precalculations necessary to set up the sparse matrix.
        """
        self.opsimdf['hids'] = [hp.query_disc(self.nside, vec, self._fieldRadius,
                                              inclusive=True,
                                              nest=True)
                                for vec in self.opsimdf[self.vecColName]]
        lens = map(len, self.opsimdf.hids.values)
        rowdata = []
        _ = list(rowdata.extend(repeat(i, lens[i]))
                 for i in xrange(len(self.opsimdf)))
        coldata = np.concatenate(self.opsimdf.hids.values)
        self._rowdata = rowdata
        self._coldata = coldata

    def validateDF(self):
        if self.raCol not in self.cols:
            raise ValueError('raCol {} not in OpSim cols'.format(self.raCol))
        if self.decCol not in self.cols:
            raise ValueError('decCol {} not in OpSim cols'.format(self.decCol))
        return

#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
A library of Reader classes to read flat data from .csv + .mdata files.
If provides the classes:

- FileReader: to read a pair of files (metadata, data) from a directory
- ZipReader: to read a pair of files (metadata, data) from a zip file
- StringReader: to wrap two strings (metadata, data)
- DataReader: to wrap the node and list iterator (metadata, data)

Moreover it provided a generator collect_readers(readercls, container)
which reads all the files in the container and yields pairs
(readername, readergroup) where readergroup is a list of readers
with the same name.
"""

import os
import csv
import itertools
import warnings
import cStringIO
from openquake.nrmllib import InvalidFile
from openquake.nrmllib.node import node_from_xml
from openquake.nrmllib import model


def collect_readers(readercls, container, fnames=None):
    """
    Given a list of filenames, instantiates several readers and yields
    them in groups. Display a warning for invalid files and ignore
    unpaired files.

    :param readercls: Reader subclass
    :param container: the container of the files
    :param fnames: the names of the files to consider

    If fnames is not None, consider only the files listed there.
    """
    if fnames is None:
        if hasattr(container, 'infolist'):  # zip archive
            fnames = [i.filename for i in container.infolist()]
        else:  # assume container is a directory
            fnames = os.listdir(container)

    def getprefix(f):
        return f.rsplit('.', 1)[0]
    fnames = sorted(f for f in fnames if f.endswith(('.csv', '.mdata')))
    readers = []
    for name, group in itertools.groupby(fnames, getprefix):
        gr = list(group)
        if len(gr) == 2:  # pair (.mdata, .csv)
            try:
                readers.append(readercls(container, name))
            except Exception as e:
                raise
                # the reader could not be instantiated, due to an invalid file
                warnings.warn(str(e))
        # ignore unpaired files

    def getgroupname(reader):
        """Extract the groupname for readers named <groupname>__<subname>"""
        return reader.name.rsplit('__', 1)[0]
    for name, readergroup in itertools.groupby(readers, getgroupname):
        yield name, list(readergroup)


class Reader(object):
    """
    Base class of all Readers. A Reader object has a name and a container,
    and various methods to extracted the underlying data and metadata.
    When instantiated only the metadata are read; the data are extracted
    only when iterating on the reader, which has a list-like interface.

    NB: in real application you will not instantiate this class, but only
    specific subclasses. Still, this class can be instantiated for testing
    purposes, as a stub; in that case it will have fieldnames lon,lat,gmv
    and no data.
    """
    def __init__(self, container, name):
        self.container = container
        self.name = name
        self.fieldnames = None  # set in read_fieldnames
        with self.openmdata() as j:
            self.load_metadata(j)
        with self.opencsv() as c:
            self.check_fieldnames(c)

    def load_metadata(self, fileobj):
        """
        Parse the metadata file and set the .metadata node and the
        .fieldnames list.
        """
        try:
            self.metadata = node_from_xml(fileobj)
        except Exception as e:
            raise InvalidFile('%s:%s' % (fileobj.name, e))
        try:
            self.read_fieldnames()
        except Exception as e:
            raise InvalidFile('%s: could not extract fieldnames: %s' %
                              (fileobj.name, e))

    def read_fieldnames(self):
        """
        Set the .fieldnames list by parsing the .metadata with the
        appropriate function (depending on the model).
        """
        getfields = getattr(model, '%s_fieldnames' %
                            self.metadata.tag.lower())
        self.fieldnames = getfields(self.metadata)

    def check_fieldnames(self, fileobj):
        """
        Check that the header of the CSV file contains the expected
        fieldnames, consistent with the ones in the metadata file.
        """
        try:
            fieldnames = csv.DictReader(fileobj).fieldnames
        except ValueError:
            raise InvalidFile(self.name + '.csv')
        if fieldnames is None or any(
                f1.lower() != f2.lower()
                for f1, f2 in zip(fieldnames, self.fieldnames)):
            raise ValueError(
                'According to %s.mdata the field names should be '
                '%s, but the header in %s.csv says %s' % (
                    self.name, self.fieldnames,
                    self.name, fieldnames))

    def openmdata(self):
        """
        Return a file-like object with the metadata (to be overridden)
        """
        return FileObject(self.name + '.mdata', '<gmfSet/>')

    def opencsv(self):
        """
        Return a file-like object with the data (to be overridden)
        """
        return FileObject(self.name + '.csv', 'lon,lat,gmv')

    def __getitem__(self, index):
        """
        Extract rows from the underlying data structure as lists.

        :param index: integer or slice object
        """
        with self.opencsv() as f:
            reader = csv.DictReader(f)
            reader.fieldnames  # read the fieldnames from the header
            if isinstance(index, int):
                # skip the first lines
                for i in xrange(index):
                    next(f)
                return next(reader)
            else:  # slice object
                # skip the first lines
                for i in xrange(index.start):
                    next(f)
                rows = []
                for i in xrange(index.stop - index.start):
                    rows.append(next(reader))
                return rows

    def __iter__(self):
        """Data iterator yielding dictionaries"""
        with self.opencsv() as f:
            for record in csv.DictReader(f):
                yield record

    def __len__(self):
        """Number of data records in the underlying data structure"""
        return sum(1 for line in self.opencsv()) - 1  # skip header

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class FileReader(Reader):
    """
    Read from a couple of files .mdata and .csv
    """
    def openmdata(self):
        """
        Open the metadata file <name>.mdata inside the directory
        """
        return open(os.path.join(self.container, self.name + '.mdata'))

    def opencsv(self):
        """
        Open the metadata file <name>.csv inside the directory
        """
        return open(os.path.join(self.container, self.name + '.csv'))


class ZipReader(Reader):
    """
    Read from .zip archives.
    """

    def openmdata(self):
        """
        Extract the metadata file <name>.mdata from the archive
        """
        return self.container.open(self.name + '.mdata')

    def opencsv(self):
        """
        Extract the CSV file <name>.csv from the archive
        """
        return self.container.open(self.name + '.csv')


class FileObject(object):
    """
    A named cStringIO for reading, useful for the tests
    """
    def __init__(self, name, bytestring):
        self.name = name
        self.io = cStringIO.StringIO(bytestring)

    def __iter__(self):
        return self

    def next(self):
        return self.io.next()

    def readline(self):
        return self.io.readline()

    def read(self, n=-1):
        return self.io.read(n)

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        pass


class StringReader(Reader):
    """
    Read data from the given strings, not from the file system.
    Assume the strings are UTF-8 encoded. The intended usage is
    for unittests.
    """
    def __init__(self, name, mdata_str, csv_str):
        self.name = name
        self.mdata_str = mdata_str
        self.csv_str = csv_str
        Reader.__init__(self, None, name)

    def opencsv(self):
        """
        Returns a file-like object with the content of csv_str
        """
        return FileObject(self.name + '.csv', self.csv_str)

    def openmdata(self):
        """
        Returns a file-like object with the content of mdata_str
        """
        return FileObject(self.name + '.mdata', self.mdata_str)


class DataReader(Reader):
    """
    Given name, metadata and data returns a reader yielding
    dictionaries when iterated over.
    """
    def __init__(self, name, metadata, rows):
        self.name = name
        self.metadata = metadata
        self.read_fieldnames()
        self.rows = rows

    def __iter__(self):
        for row in self.rows:
            yield dict(zip(self.fieldnames, row))

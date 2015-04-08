# from http://docs.python.org/library/csv.html#csv-examples

import csv
import cStringIO
import codecs

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class Reader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class RowWriter(object):
    """
    A CSV writer that generates rows of CSV bytes in a given encoding.
    """

    def __init__(self, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        def stringify(value):
            if isinstance(value, unicode):
                pass
            elif isinstance(value, basestring):
                value = value.decode('utf-8')
            elif hasattr(value, '__unicode__'):
                value = unicode(value)
            elif hasattr(value, '__str__'):
                value = str(value).decode('utf-8')
            else:
                raise NotImplementedError
            return value.encode('utf-8')
        self.queue.truncate(0)
        self.writer.writerow(map(stringify, row))
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        return self.encoder.encode(data)


class Writer(RowWriter):
    """
    A CSV writer that writes rows of CSV to file "f" in a given encoding.

    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        super(Writer, self).__init__(dialect, encoding, **kwds)
        self.stream = f

    def writerow(self, row):
        self.stream.write(super(Writer, self).writerow(row))

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

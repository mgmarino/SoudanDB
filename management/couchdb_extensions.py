from couchdb.mapping import Field

# MappingField rolled by jabronson (see http://code.google.com/p/couchdb-python/issues/detail?id=106)
class MappingField(Field):
    """
    Field type for mappings between strings and a Field type. 
    
    A different Field type for keys may be specified, but it
    must serialize to a string in order to be a valid key in
    a json dictionary. 

    N.B. Keys with the same json representation according to 
    the key schema are considered equal -- alternate key types
    are provided as a convenient and consistent way to map to and from 
    strings only.  If you're nervous about this, use strings as your keys
    instead.

    >>> from couchdb import Server
    >>> server = Server('http://localhost:5984/')
    >>> db = server.create('python-tests')

    >>> class Book(Mapping):
    ...     title = TextField()
    ...     authors = ListField(TextField())
    ...     publish_date = DateField()
    >>> class Library(Document):
    ...     books = MappingField(DictField(Book))
    >>> couch_book_info = {'title': 'CouchDB: The Definitive Guide', 
    ...                    'authors': ['J. Anderson', 'Jan Lehnardt', 'Noah Slater'],
    ...                    'publish_date': date(2009, 11, 15)}
    >>> isbn = 'URN:ISBN:978-059-61-5589-6'
    >>> library = Library()
    >>> library.books[isbn] = couch_book_info
    >>> len(library.books)
    1
    >>> library.store(db) # doctest: +ELLIPSIS
    <Library ...>
    >>> isbn in library.books
    True
    >>> book = library.books[isbn]
    >>> book.title
    u'CouchDB: The Definitive Guide'
    >>> book.publish_date
    datetime.date(2009, 11, 15)
    >>> 'Jan Lehnardt' in book.authors
    True
    
    >>> del server['python-tests']
    """

    def __init__(self, field, key_field=Field, name=None, default=None):
        Field.__init__(self, name=name, default=default or {})

        def mkfield(f):
            if type(f) is type:
                if issubclass(f, Field):
                    return f()
                elif issubclass(f, Mapping):
                    return DictField(f)
            return f

        self.field = mkfield(field)
        self.key_field = mkfield(key_field)

    def _to_python(self, value):
        return self.Proxy(value, self.field, self.key_field)

    def _to_json(self, value):
        return dict([(self.key_field._to_json(k), 
                      self.field._to_json(v)) for (k, v) in value.items()])


    class Proxy(dict):

        def __init__(self, wdict, field, key_field):
            self.dict = wdict
            self.field = field
            self.key_field = key_field

        def __cmp__(self, other):
            return self.dict.__cmp__(other)

        def __contains__(self, item):
            try:
                jsonk = self.key_field._to_json(item)
            except:
                return False
            
            return self.dict.__contains__(jsonk)


        # def __delattr__(self, name):

        def __delitem__(self, key):
            try:
                jsonk = self.key_field._to_json(key)
            except ValueError:
                raise KeyError(key)

            return self.dict.__delitem__(jsonk)

        def __eq__(self, other):
            return self.dict.__eq__(other)

        def __ge__(self, other):
            return self.dict.__ge__(other)

        # def __getattribute__(self, name):

        def __getitem__(self, key):
            try:
                jsonk = self.key_field._to_json(key)
            except:
                raise KeyError(key)
            
            return self.field._to_python(self.dict.__getitem__(jsonk))
            
        def __gt__(self, other):
            return self.dict.__gt__(other)

        # def __hash__(self):

        def __iter__(self):
            for k in self.dict.__iter__():
                yield self.key_field._to_python(k)

        def __le__(self, other):
            return self.dict.__le__(other)

        def __len__(self):
            return self.dict.__len__()

        def __lt__(self, other):
            return self.dict.__lt__(other)

        def __ne__(self, other):
            return self.dict.__ne__(other)

        # def __reduce__(self):
        # def __reduce_ex__(self):

        def __repr__(self):
            return self.dict.__repr__()

        # def __setattr__(self, name, value)

        def __setitem__(self, key, value):
            self.dict.__setitem__(self.key_field._to_json(key), 
                                  self.field._to_json(value))

        def __str__(self):
            return str(self.dict)

        def __unicode__(self):
            return unicode(self.dict)

        def clear(self):
            return self.dict.clear()

        # def copy():

        @classmethod
        def fromkeys(cls, seq, value=None):
            raise NotImplementedError('Cannot initialize class of type %s without Field type' % cls.__name__)

        def get(self, key, default=None):
            try:
                return self.field._to_python(self[key])
            except KeyError:
                return default

        def has_key(self, key):
            try:
                return self.dict.has_key(self.key_field._to_json(key))
            except ValueError:
                return False

        def items(self):
            return list(self.iteritems())

        def iteritems(self):
            for (k, v) in self.dict.iteritems():
                yield (self.key_field._to_python(k),
                       self.field._to_python(v))

        def iterkeys(self):
            for k in self.dict.iterkeys():
                yield self.key_field._to_python(k)

        def itervalues(self):
            for v in self.dict.itervalues():
                yield self.field._to_python(v)

        def keys(self):
            return list(self.iterkeys())

        def pop(self, *args):
            if len(args) == 0:
                raise TypeError('pop expected at least 1 arguments, got 0')
            if len(args) > 2:
                raise TypeError('pop expected at most 2 arguments, got %d' % len(args))


            try:
                try:
                    popkey = self.key_field._to_json(args[0])
                except ValueError:
                    raise KeyError(args[0])
                return self.field._to_python(self.dict.pop(popkey))
            except KeyError:
                if len(args) == 1:
                    raise
                else:
                    return args[1]

        def popitem(self):
            k, v = self.dict.popitem()
            return (self.key_field._to_python(k), self.field._to_python(v))

        def setdefault(self, key, default=None):
            try:
                jsonk = self.key_field._to_json(key)
                default_json = self.field._to_json(default)
            except:
                raise ValueError

            v = self.dict.setdefault(jsonk, default_json)
            
            return self.field._to_python(v)

        def update(self, other):
            for (k, v) in other.iteritems():
                self[k] = v

        def values(self):
            return [self.field._to_python(v) for v in self.dict.values()]


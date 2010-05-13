try:
    import sqlalchemy
except:
    sqlalchemy_available = False
else:
    sqlalchemy_available = sqlalchemy.__version__

def get_wrapper(obj, sqlalchemy_session=None):
    """
    Auto-detect the kind of object and return a list/tuple
    to access items from the collection.
    """
    # See if the collection is a sequence
    if isinstance(obj, (list, tuple)):
        return obj
    # Is SQLAlchemy 0.4 available? (0.3 is not supported - sorry)
    if sqlalchemy_available.startswith('0.4') or sqlalchemy_available.startswith('0.5'):
        # Is the collection a query?
        if isinstance(obj, sqlalchemy.orm.query.Query):
            return _SQLAlchemyQuery(obj)

        # Is the collection an SQLAlchemy select object?
        if isinstance(obj, sqlalchemy.sql.expression.CompoundSelect) \
            or isinstance(obj, sqlalchemy.sql.expression.Select):
                return _SQLAlchemySelect(obj, sqlalchemy_session)

    raise TypeError("Sorry, your collection type is not supported by the paginate module. "
            "You can either provide a list, a tuple, an SQLAlchemy 0.4 select object or an "
            "SQLAlchemy 0.4 ORM-query object.")

class _SQLAlchemySelect(object):
    """
    Iterable that allows to get slices from an SQLAlchemy Select object
    """
    def __init__(self, obj, sqlalchemy_session=None):
        if not isinstance(sqlalchemy_session, sqlalchemy.orm.scoping.ScopedSession):
            raise TypeError("If you want to page an SQLAlchemy 'select' object then you "
                    "have to provide a 'sqlalchemy_session' argument. See also: "
                    "http://www.sqlalchemy.org/docs/04/session.html")

        self.sqlalchemy_session = sqlalchemy_session
        self.obj = obj

    def __getitem__(self, range):
        if not isinstance(range, slice):
            raise Exception, "__getitem__ without slicing not supported"
        offset = range.start
        limit = range.stop - range.start
        select = self.obj.offset(offset).limit(limit)
        return self.sqlalchemy_session.execute(select).fetchall()

    def __len__(self):
        return self.sqlalchemy_session.execute(self.obj).rowcount

class _SQLAlchemyQuery(object):
    """
    Iterable that allows to get slices from an SQLAlchemy Query object
    """
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, range):
        if not isinstance(range, slice):
            raise Exception, "__getitem__ without slicing not supported"
        return self.obj[range]

    def __len__(self):
        return self.obj.count()
        

class Paginator(list):
    def __init__ (self, collection, page = 1, items_per_page = 15, sqlalchemy_session = None):
        if collection:
            self.collection = get_wrapper(collection, sqlalchemy_session)
        else:
            self.collection = []
        try:
            self.items_per_page = items_per_page
        except ValueError:
            self.items_per_page = 15
        try:
            self.page = int(page) # make it int() if we get it as a string
        except ValueError:
            self.page = 1
        self.count = len(self.collection)
        if self.count > 0:
            self.first_page = 1
            self.page_count = self.last_page = ((self.count - 1) / self.items_per_page) + 1
            self.page = min(self.page, self.last_page)
            self.page = max(self.page, 1)
            self.start = page * items_per_page - items_per_page
            self.end = min(page*items_per_page, self.count)
            if self.page > self.first_page:
                self.previous_page = page-1
            else:
                self.previous_page = None
            if self.page < self.last_page:
                self.next_page = page+1
            else:
                self.next_page = None
            self.next_page = None            
            self.items = list(collection[self.start:self.end])
        else:
            self.first_page = None
            self.page_count = 0
            self.last_page = None
            self.start = None
            self.end = None
            self.previous_page = None
            self.next_page = None
            self.items = []        
        list.__init__(self, self.items)

    def __repr__(self):
        return ("Page:\n"
            "Collection type:  %(type)s\n"
            "(Current) page:   %(page)s\n"
            "First item:       %(first_item)s\n"
            "Last item:        %(last_item)s\n"
            "First page:       %(first_page)s\n"
            "Last page:        %(last_page)s\n"
            "Previous page:    %(previous_page)s\n"
            "Next page:        %(next_page)s\n"
            "Items per page:   %(items_per_page)s\n"
            "Number of items:  %(item_count)s\n"
            "Number of pages:  %(page_count)s\n"
            % {
            'type':type(self.collection),
            'page':self.page,
            'first_item':self.start+1,
            'last_item':self.end,
            'first_page':self.first_page,
            'last_page':self.last_page,
            'previous_page':self.previous_page,
            'next_page':self.next_page,
            'items_per_page':self.items_per_page,
            'item_count':self.count,
            'page_count':self.page_count,
            })
        


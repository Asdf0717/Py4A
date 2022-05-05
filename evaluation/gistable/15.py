"""
SQLAlchemy Enum type based on Integer indices.
"""
from sqlalchemy import types

class Enum(types.TypeDecorator):
    impl = types.Integer

    def __init__(self, value_map, strict=True, *args, **kw):
        """Emulate Enum type with integer-based indexing.

        value_map:
            An integer_id:name dictionary of possible values, or a list of value
            names (which gets converted to corresponding index numbers starting from 1).
        strict:
            Assert that data read from the database matches with the expected
            valid value definitions.
        """

        self.strict = strict

        if isinstance(value_map, list):
            value_map = dict((k+1,v) for k,v in enumerate(value_map))

        # Enum lookup indices
        self.id_lookup = value_map
        self.name_lookup = dict((v,k) for k,v in value_map.iteritems())

        super(Enum, self).__init__(self, *args, **kw)

    def process_bind_param(self, value, dialect):
        id = self.name_lookup.get(value)
        if not id:
            raise AssertionError("Name '{0}' is not one of: {1}".format(value, self.name_lookup.keys()))
        return id

    def process_result_value(self, value, dialect):
        name = self.id_lookup.get(value)
        if self.strict and not name:
            raise AssertionError("Id '{0}' is not one of: {1}".format(value, self.id_lookup.keys()))
        return name

    def copy_value(self, value):
        "Convert named value to internal id representation"
        return self.name_lookup.get(value)

import re
from functools import reduce


class Resolver:

    @staticmethod
    def _walk(item, index):
        if index.isdigit():
            return item[int(index)]
        return item[index]

    @classmethod
    def handside(cls, item, data):
        return cls.object(item, data)

    @staticmethod
    def stringify(value):
        if type(value) is str:
            return '"""{}"""'.format(value.replace('"', '\"'))
        return str(value)

    @classmethod
    def values(cls, items_list, data=None):
        """
        Parses a list of values objects. The list may contain other objects.
        """
        if data is not None:
            mapping = map(lambda item: cls.object(item, data), items_list)
            return list(mapping)

        values = []
        for value in items_list:
            values.append(value['paths'][0])
        return values

    @classmethod
    def string(cls, string, data, values=None):
        """
        Resolves a string to itself. If values are given, the string
        is formatted against data, using the order in values.
        """
        if values:
            keys = Resolver.values(values)
            arguments = []
            for key in keys:
                if key in data:
                    arguments.append(data[key])

            if len(arguments) != len(keys):
                raise ValueError('Not enough string arguments from data')
            return string.format(*arguments)
        return string

    @classmethod
    def path(cls, paths, data):
        """
        Resolves a path against some data, for example the path 'a.b'
        with data {'a': {'b': 'value'}} produces 'value'
        """
        try:
            return reduce(cls._walk, paths[0].split('.'), data)
        except (KeyError, TypeError):
            return None

    @classmethod
    def dictionary(cls, dictionary, data):
        result = {}
        for key, value in dictionary.items():
            result[key] = cls.resolve(value, data)
        return result

    @staticmethod
    def method(method, left, right):
        if method == 'like':
            return right.match(left) is not None
        elif method == 'notlike':
            return right.match(left) is None
        elif method == 'in':
            return left in right
        elif method in ('has', 'contains'):
            return right in left
        elif method == 'excludes':
            return left not in right
        elif method == 'isnt':
            return right != left
        elif method == 'is':
            return right == left
        raise ValueError('Method not supported')

    @classmethod
    def expression(cls, data, expression, values):
        mapping = map(cls.stringify, cls.values(values, data=data))
        return eval(expression.format(*mapping))

    @classmethod
    def object(cls, item, data):
        object_type = item.get('$OBJECT')
        if object_type == 'string':
            if 'values' in item:
                return cls.string(item['string'], data, values=item['values'])
            return cls.string(item['string'], data)
        elif object_type == 'path':
            return cls.path(item['paths'], data)
        elif object_type == 'regexp':
            return re.compile(item['regexp'])
        elif object_type == 'value':
            return item['value']
        elif object_type == 'method':
            left = cls.handside(item['left'], data)
            right = cls.handside(item['right'], data)
            return cls.method(item['method'], left, right)
        elif object_type == 'expression':
            expression = item['expression']
            values = item['values']
            return cls.expression(data, expression, values)
        return cls.dictionary(item, data)

    @classmethod
    def list(cls, items, data):
        result = []
        for item in items:
            result.append(cls.resolve(item, data))
        return ' '.join(result)

    @classmethod
    def resolve(cls, item, data):
        if type(item) is dict:
            return cls.object(item, data)
        elif type(item) is list:
            return cls.list(item, data)
        return item

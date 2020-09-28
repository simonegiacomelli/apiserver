from typing import Dict


class Dispatch:
    def __init__(self, ):
        self.registered = {}
        self.prefix: str = None

    def register(self, clazz, prefix):
        self.registered = {d[len(prefix):]: getattr(clazz, d) for d in dir(clazz) if
                           d.startswith(prefix) and not d.startswith('__')}
        self.prefix = prefix
        return self

    def dispatch(self, instance, method_name, params: Dict = {}):
        if method_name not in self.registered.keys():
            raise MethodNotRegistered(method_name)
        m = getattr(instance, self.prefix + method_name)
        return m(**params)


class MethodNotRegistered(Exception):
    pass

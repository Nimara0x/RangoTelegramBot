from decimal import Decimal
from typing import Union


class Singleton(object):
    def __new__(cls, *args, **kwds):
        self = "__self__"
        if not hasattr(cls, self):
            instance = object.__new__(cls)
            instance.init(*args, **kwds)
            setattr(cls, self, instance)
        return getattr(cls, self)

    def init(self, *args, **kwargs):
        pass

    def __init__(self):
        pass


def amount_to_human_readable(amount: Union[str, float], decimal_places: int, fraction: int) -> str:
    formatter = f'%.{fraction}f'
    return formatter % (Decimal(Decimal(amount) / (10 ** decimal_places)))


def format_output_amount(amount: float) -> str:
    return '%.5f' % Decimal(amount)

from functools import lru_cache, wraps
from datetime import datetime, timedelta

def timed_lru_cache(days: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        
        # инструментирование декоратора двумя атрибутами,
        # представляющими время жизни кэша lifetime
        # и дату истечения срока его действия expiration
        func.lifetime = timedelta(days=days)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime

            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache
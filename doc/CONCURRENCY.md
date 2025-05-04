Procedures that run in a separate thread (and don't return value to the call site, except for the unawaited "promise" monad) will have their name suffixed with `_async`. From now on, we call these _async procedures_.

Async procedures will have to be manually kick-started with a `.start()` method call.

```python
def submit_info_async(*args):
    # ...
    return fetch_async(*args)

def on_submitted(*args):
    # ...

if __name__ == "__main__":
    submit_info_async().then(on_submitted).start()
```

## Internal

Async procedures are implemented using `Promise` a.k.a. the PeerChat Promise API. It is a light wrapper over `threading.Thread` a.k.a. Python Thread API, and was made to resemble JavaScript's Promise API.

It works very like Python Thread, in that you have to instantiate an object with target handler and arguments, and have to call `.start()` to run it. It also resembles JS Promise, in that you can bind a response handler with `then()`, and you can bind in succession a.k.a. method-chaining. There are some key differences:

- Unlike JS Promise, PeerChat Promise requires **specifically one** `.then()` call. There is exactly one `.then()` slot, and it is mandatory. This only means that, when you chain multiple `.then()`'s, only the lastest one is registered. It is undefined behavior if `.start()` is called before `.then()`

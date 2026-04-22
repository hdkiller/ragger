__all__ = ["app", "main"]


def __getattr__(name: str):
    if name in __all__:
        from ragger.server.app import app, main

        return {"app": app, "main": main}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

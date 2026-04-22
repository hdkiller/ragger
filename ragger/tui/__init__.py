__all__ = ["RaggerApp"]


def __getattr__(name: str):
    if name == "RaggerApp":
        from ragger.tui.app import RaggerApp

        return RaggerApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

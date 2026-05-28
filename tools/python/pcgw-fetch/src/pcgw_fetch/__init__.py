"""PCGamingWiki metadata fetcher — writes <game>/metadata.jsonc."""

__version__ = "0.1.0"

from .cli import app  # noqa: E402  (must follow __version__)

__all__ = ["app", "__version__"]

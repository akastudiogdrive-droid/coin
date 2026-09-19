"""Pluggable context sources. To add one: create a module with NAME and
update(health) that saves its data under data/context/, then list it below."""
from . import fear_greed, weather

CONTEXT_SOURCES = [fear_greed, weather]

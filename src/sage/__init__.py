"""Sage - Intelligent semantic tagging for markdown files."""

__version__ = "0.1.1"
__author__ = "Marius Høgli Aasarød"
__email__ = "marius@aasarod.no"

from .tagger import AsyncMarkdownTagger

__all__ = ["AsyncMarkdownTagger"]

"""Sage - Intelligent semantic tagging for markdown files."""

__version__ = "0.1.0"
__author__ = "Marius Høglia Åsarod"
__email__ = "marius@aasarod.no"

from .tagger import AsyncMarkdownTagger

__all__ = ["AsyncMarkdownTagger"]
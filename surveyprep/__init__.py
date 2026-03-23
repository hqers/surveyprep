"""
SurveyPrep — Modular preprocessing framework for household expenditure surveys.
Metadata basis: Susenas 2020 Maret (KOR)
"""
try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("surveyprep")
except PackageNotFoundError:
    # Fallback kalau dijalankan langsung dari source tanpa install
    __version__ = "1.9.6"

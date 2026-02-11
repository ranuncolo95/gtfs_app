# src/error.py
class AppError(Exception):
    """Base class per errori applicativi (cross-layer)."""
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(msg)


class InvalidInput(AppError):
    """Input non valido (coords/date/time/...)"""


class NotFound(AppError):
    """Nessun risultato (nessun trip/nessuna rotta/...)"""


class DataFailure(AppError):
    """Errore tecnico nel data layer (DB/GeoPandas/etc)"""

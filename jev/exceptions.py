"""Excepciones de dominio para la arquitectura del sistema de trading Jev."""

class JevError(Exception):
    """Excepción base para todos los errores en el sistema Jev."""
    pass

class DataIngestionError(JevError):
    """Error al ingerir, descargar o parsear datos de mercado."""
    pass

class FeatureExtractionError(JevError):
    """Error durante el cómputo de indicadores o estado de mercado."""
    pass

class AIDecisionError(JevError):
    """Error en la inferencia, parsing JSON o validación del modelo de IA."""
    pass

class RiskValidationError(JevError):
    """Error o rechazo emitido por el motor determinista de control de riesgo."""
    pass

class KillSwitchTriggeredError(RiskValidationError):
    """Error crítico: Kill Switch activado por volatilidad, drawdown o fallo anómalo."""
    pass

class ExecutionError(JevError):
    """Error durante el enrutamiento o confirmación de la orden en el broker."""
    pass

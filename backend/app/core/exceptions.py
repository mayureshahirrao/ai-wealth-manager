"""
exceptions.py — Typed exception hierarchy for the entire application.
"""

from typing import Optional, Any, Dict


class WealthManagerException(Exception):
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(WealthManagerException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class ClientNotFoundException(NotFoundException):
    def __init__(self, client_id: str):
        super().__init__(resource="Client", identifier=client_id)


class PortfolioNotFoundException(NotFoundException):
    def __init__(self, client_id: str):
        super().__init__(resource="Portfolio", identifier=client_id)


class UnauthorizedException(WealthManagerException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, error_code="UNAUTHORIZED", status_code=401)


class ForbiddenException(WealthManagerException):
    def __init__(self, role: str, resource: str):
        super().__init__(
            message=f"Role '{role}' is not permitted to access '{resource}'",
            error_code="FORBIDDEN",
            status_code=403,
            details={"role": role, "resource": resource},
        )


class ValidationException(WealthManagerException):
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field, "reason": reason},
        )


class InvalidPANException(ValidationException):
    def __init__(self, pan: str):
        super().__init__(field="pan", reason=f"'{pan}' is not a valid Indian PAN format")


class InsufficientDataError(WealthManagerException):
    def __init__(self, field: str, context: Optional[str] = None):
        super().__init__(
            message=f"Required data '{field}' is not available" + (f" for {context}" if context else ""),
            error_code="INSUFFICIENT_DATA",
            status_code=422,
            details={"missing_field": field, "context": context},
        )


class InvalidTokenException(WealthManagerException):
    def __init__(self):
        super().__init__(
            message="JWT token is invalid or has expired",
            error_code="INVALID_TOKEN",
            status_code=401,
        )


class AIToolExecutionError(WealthManagerException):
    def __init__(self, tool_name: str, reason: str, client_id: Optional[str] = None):
        super().__init__(
            message=f"AI tool '{tool_name}' failed: {reason}",
            error_code="AI_TOOL_ERROR",
            status_code=500,
            details={"tool_name": tool_name, "reason": reason, "client_id": client_id},
        )


class AgentExecutionError(WealthManagerException):
    def __init__(self, agent_name: str, step: str, reason: str):
        super().__init__(
            message=f"Agent '{agent_name}' failed at step '{step}': {reason}",
            error_code="AGENT_EXECUTION_ERROR",
            status_code=500,
            details={"agent_name": agent_name, "step": step, "reason": reason},
        )


class RAGRetrievalError(WealthManagerException):
    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"Knowledge base retrieval failed: {reason}",
            error_code="RAG_ERROR",
            status_code=500,
            details={"query": query[:100], "reason": reason},
        )


class PortfolioCalculationError(WealthManagerException):
    def __init__(self, calculation: str, reason: str):
        super().__init__(
            message=f"Calculation '{calculation}' failed: {reason}",
            error_code="CALCULATION_ERROR",
            status_code=500,
            details={"calculation": calculation, "reason": reason},
        )


class DatabaseError(WealthManagerException):
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation, "reason": reason},
        )


class SEBIValidationError(WealthManagerException):
    def __init__(self, clause: str, reason: str):
        super().__init__(
            message=f"SEBI compliance check failed [{clause}]: {reason}",
            error_code="SEBI_VALIDATION_ERROR",
            status_code=422,
            details={"clause": clause, "reason": reason},
        )


class ComplianceViolationError(WealthManagerException):
    def __init__(self, rule: str, action: str):
        super().__init__(
            message=f"Action '{action}' violates compliance rule: {rule}",
            error_code="COMPLIANCE_VIOLATION",
            status_code=403,
            details={"rule": rule, "action": action},
        )


class LowConfidenceEscalationError(WealthManagerException):
    def __init__(self, confidence: float, threshold: float, query: str):
        super().__init__(
            message=(
                f"AI confidence {confidence:.0%} is below minimum threshold {threshold:.0%}. "
                "This query requires human review."
            ),
            error_code="LOW_CONFIDENCE_ESCALATION",
            status_code=200,
            details={"confidence": confidence, "threshold": threshold, "query": query[:100]},
        )

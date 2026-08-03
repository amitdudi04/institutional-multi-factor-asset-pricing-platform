"""Domain exceptions shared by platform foundation components."""


class PlatformError(Exception):
    """Base class for expected, actionable platform failures."""


class ConfigurationError(PlatformError):
    """Raised when configuration is missing, malformed, or unsafe to use."""


class ProjectRootError(PlatformError):
    """Raised when the repository root cannot be resolved unambiguously."""

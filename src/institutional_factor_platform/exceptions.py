"""Domain exceptions shared by platform foundation components."""


class PlatformError(Exception):
    """Base class for expected, actionable platform failures."""


class ConfigurationError(PlatformError):
    """Raised when configuration is missing, malformed, or unsafe to use."""


class ProjectRootError(PlatformError):
    """Raised when the repository root cannot be resolved unambiguously."""


class DataPlatformError(PlatformError):
    """Base class for Phase 1 data-platform failures."""


class DataSourceError(DataPlatformError):
    """A source request or response failed."""


class RateLimitError(DataSourceError):
    """A provider rate limit prevented retrieval."""


class RetrievalError(DataSourceError):
    """A provider retrieval failed completely."""


class PartialRetrievalError(DataSourceError):
    """A multi-entity retrieval returned only a subset."""


class RawStorageError(DataPlatformError):
    """Raw artifact persistence or verification failed."""


class ChecksumMismatchError(RawStorageError):
    """Stored bytes no longer match their recorded checksum."""


class SchemaValidationError(DataPlatformError):
    """Data violates a versioned contract."""


class DataQualityError(DataPlatformError):
    """Data failed a blocking quality rule."""


class ManifestError(DataPlatformError):
    """Manifest validation or persistence failed."""


class CatalogError(DataPlatformError):
    """DuckDB catalog operation failed."""


class TemporalIntegrityError(DataPlatformError):
    """Temporal ordering would permit invalid research use."""


class UnsupportedDatasetError(DataPlatformError):
    """A dataset type or schema is not approved."""


class SecurityMappingError(DataPlatformError):
    """A security identity is invalid or ambiguous."""

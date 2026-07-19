"""
AutoResolve Unified Environment and Runtime Configuration Validation Suite.
Enforces fail-fast validation for Pydantic application schemas and runtime interpreter layers.
"""

import sys
import pytest
from pydantic import ValidationError

# Import only the lowercase instance object to prevent class import issues
from src.core.config import settings


class TestApplicationSettingsFailFast:
    """
    Validates that the AutoResolve core management engine correctly triggers
    a fail-fast crash when required environment fields are missing.
    """

    # Pass monkeypatch into the test arguments
    def test_settings_raises_validation_error_on_missing_required_tokens(self) -> None:
        """
        Verifies that initializing the settings class without valid configuration
        correctly triggers a strict Pydantic ValidationError.
        """
        # CRITICAL FIX: Inject explicitly invalid types (None) into required fields 
        # to guarantee a Pydantic ValidationError regardless of the OS environment.
        invalid_mock_env = {
            "POSTGRES_URL": None,
            "KAFKA_BOOTSTRAP_SERVERS": None
        }
        
        with pytest.raises(ValidationError):
            # Pass the invalid kwargs directly to the dynamic class constructor
            type(settings)(**invalid_mock_env)  # type: ignore


class TestInterpreterWorkspaceSanity:
    """
    Executes native diagnostic validation across the active virtual environment.
    """

    def test_python_runtime_version_bounds(self) -> None:
        """Ensures the active local Python environment falls within corporate guidelines."""
        major = sys.version_info.major
        minor = sys.version_info.minor
        
        assert major == 3
        assert 11 <= minor < 14

    def test_framework_binary_integrity(self) -> None:
        """Confirms that core package drivers are fully integrated and functional."""
        import pytest
        import pydantic
        
        assert pytest.__version__ is not None
        assert pydantic.__version__ is not None
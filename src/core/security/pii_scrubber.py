# src/core/security/pii_scrubber.py
# PII Scrubber for Data Privacy
import logging

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine

    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class PIIScrubber:
    """
    Enterprise PII Scrubber to ensure Data Privacy and prevent sensitive
    customer data from being transmitted to third-party LLMs.
    """

    def __init__(self) -> None:
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self.entities = [
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "CREDIT_CARD",
                "US_SSN",
                "IP_ADDRESS",
            ]
            logger.info("Presidio PII Scrubber initialized successfully.")
        else:
            logger.warning(
                "Presidio not installed. PII Scrubber running in regex fallback mode."
            )

    def scrub(self, text: str) -> str:
        """Analyzes text for PII entities and redacts them."""
        if not text:
            return text

        if not PRESIDIO_AVAILABLE:
            # Fallback for environments where heavy NLP models cannot be loaded
            return self._regex_fallback_scrub(text)

        try:
            results = self.analyzer.analyze(
                text=text, entities=self.entities, language="en"
            )
            anonymized = self.anonymizer.anonymize(text=text, analyzer_results=results)
            return anonymized.text
        except Exception as e:
            logger.error(
                f"Failed to scrub PII from payload. Dropping payload for safety. Error: {e}" # noqa: E501
            )
            return "[REDACTED DUE TO SCRUBBER FAILURE]"

    def _regex_fallback_scrub(self, text: str) -> str:
        """Basic regex-based scrubber (Implementation deferred)."""
        import re

        # Basic email redaction
        text = re.sub(r"[\w\.-]+@[\w\.-]+", "[EMAIL_REDACTED]", text)
        # Basic IP redaction
        text = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_REDACTED]", text)
        return text


# Singleton instance
pii_scrubber = PIIScrubber()

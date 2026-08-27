"""Pure domain value objects enforcing financial invariants and typing."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MonetaryAmount:
    """
    Immutable monetary amount stored in the lowest currency unit (cents/paise).
    Guarantees deterministic, precision-loss-free arithmetic.
    """

    cents: int
    currency: str = "INR"

    def __post_init__(self) -> None:
        if self.cents < 0:
            raise ValueError(f"Monetary amount cannot be negative: {self.cents}")
        if not self.currency or len(self.currency) != 3:
            raise ValueError(f"Invalid 3-letter ISO currency code: {self.currency}")

    @classmethod
    def from_paise(cls, paise: int, currency: str = "INR") -> "MonetaryAmount":
        """Factory constructor from integer paise."""
        return cls(cents=paise, currency=currency)

    @property
    def amount_in_cents(self) -> int:
        """Alias for cents."""
        return self.cents

    @property
    def decimal_value(self) -> Decimal:
        """Returns standard decimal representation (e.g. ₹10.50)."""
        return Decimal(self.cents) / Decimal(100)

    def add(self, other: "MonetaryAmount") -> "MonetaryAmount":
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add amounts with mismatched currencies: {self.currency} vs {other.currency}"
            )
        return MonetaryAmount(cents=self.cents + other.cents, currency=self.currency)

    def subtract(self, other: "MonetaryAmount") -> "MonetaryAmount":
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract amounts with mismatched currencies: {self.currency} vs {other.currency}"
            )
        return MonetaryAmount(cents=max(0, self.cents - other.cents), currency=self.currency)


@dataclass(frozen=True)
class RiskScore:
    """
    Calibrated customer or transaction risk score normalized to [0.0, 1.0].
    """

    score: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Risk score must be between 0.0 and 1.0, got: {self.score}")


@dataclass(frozen=True)
class RecoveryProbability:
    """
    Tabular ML statistical recovery probability estimate in range [0.0, 1.0].
    """

    probability: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.probability <= 1.0):
            raise ValueError(
                f"Recovery probability must be between 0.0 and 1.0, got: {self.probability}"
            )

    @classmethod
    def from_float(cls, p: float) -> "RecoveryProbability":
        """Factory constructor from float probability."""
        return cls(probability=p)

    @property
    def value(self) -> float:
        """Numeric float representation."""
        return self.probability


@dataclass(frozen=True)
class ModelConfidence:
    """
    Qualitative LLM epistemic certainty score in range [0.0, 1.0].
    Used strictly for human escalation triggers, NEVER as a probability multiplier.
    """

    confidence: float
    reasoning: str

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Model confidence must be between 0.0 and 1.0, got: {self.confidence}"
            )

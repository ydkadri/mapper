"""Base module with parent classes."""


class Animal:
    """Base animal class."""

    def __init__(self, name: str):
        """Initialize animal."""
        self.name = name

    def speak(self) -> str:
        """Make animal speak."""
        return "..."


class Vehicle:
    """Base vehicle class."""

    def __init__(self, wheels: int):
        """Initialize vehicle."""
        self.wheels = wheels

    def move(self) -> str:
        """Move vehicle."""
        return "moving"

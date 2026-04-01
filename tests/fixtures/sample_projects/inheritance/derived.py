"""Derived module with child classes."""

from inheritance.base import Animal, Vehicle


class Dog(Animal):
    """Dog class inheriting from Animal."""

    def speak(self) -> str:
        """Make dog speak."""
        return "Woof!"

    def fetch(self) -> str:
        """Fetch action."""
        return f"{self.name} is fetching"


class Car(Vehicle):
    """Car class inheriting from Vehicle."""

    def __init__(self, wheels: int, fuel: str):
        """Initialize car."""
        super().__init__(wheels)
        self.fuel = fuel

    def move(self) -> str:
        """Move car."""
        return f"Driving on {self.wheels} wheels using {self.fuel}"


class Cat(Animal):
    """Cat class inheriting from Animal."""

    def speak(self) -> str:
        """Make cat speak."""
        return "Meow!"

from typing import Dict


class PositionBook:
    def __init__(self, max_positions: int) -> None:
        self.max_positions = max_positions
        self.positions: Dict[str, float] = {}

    def can_open(self, mint: str) -> bool:
        return mint in self.positions or len(self.positions) < self.max_positions

    def open_or_add(self, mint: str, amount: float) -> None:
        self.positions[mint] = self.positions.get(mint, 0.0) + amount

    def reduce_or_close(self, mint: str, amount: float) -> None:
        current = self.positions.get(mint, 0.0)
        new_amount = max(0.0, current - amount)
        if new_amount == 0.0:
            self.positions.pop(mint, None)
        else:
            self.positions[mint] = new_amount


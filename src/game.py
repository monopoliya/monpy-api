import random
from src.apps.games.models import Game


class GameService:
    @staticmethod
    def roll_dice() -> tuple[int, int]:
        return random.randint(1, 6), random.randint(1, 6)

    @staticmethod
    def move_player(game: Game, player_idx: int, steps: int) -> None:
        ps = game.players[player_idx]
        prev = ps.position

        ps.position = (prev + steps) % len(game.board)
        # bunus for passing "START" (e.g., collecting $200)
        if prev + steps >= len(game.board):
            ps.balance += 200

    @staticmethod
    def purchase_property(game: Game, player_idx: int) -> bool:
        ps = game.players[player_idx]
        prop = game.board[ps.position]

        if prop.owner_id is None and ps.balance >= prop.price:
            ps.balance -= prop.price
            prop.owner_id = ps.player_id
            ps.properties.append(prop)
            return True

        return False

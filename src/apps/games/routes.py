from .models import \
    Game, Property, Player

from src.utils import tmsnow
from src.game import GameService
from src.websocket import manager

from src.apps.depends import get_user_id

from typing import Any
from fastapi import APIRouter, \
    Depends, WebSocket, HTTPException

router = APIRouter(prefix='/games', tags=['games'])


@router.post(
    path='/',
    response_model=dict[str, Any]
)
async def create_game(
    max_players: int = 4,
    player_id: int = Depends(get_user_id)
):
    if max_players < 2 or max_players > 4:
        raise HTTPException(400, 'Max players must be between 2 and 4')

    board = [
        Property(
            id=i,
            name=f'Field {i}',
            price=100 + i*10,
            rent=[10, 20, 30]
        )
        for i in range(40)
    ]

    game = Game(
        max_players=max_players,
        board=board,
        players=[Player(
            player_id=player_id
        )]
    )
    await game.insert()

    return {
        'game_id': str(game.id),
        'status': game.status,
        'players': [p.player_id for p in game.players]
    }


@router.post(
    path='/{game_id}/join',
    response_model=dict[str, Any]
)
async def join_game(game_id: str, player_id: int):
    game = await Game.get(game_id)
    if not game:
        raise HTTPException(404, 'Game not found')

    if any(p.player_id == player_id for p in game.players):
        raise HTTPException(400, 'Player already joined')
    if len(game.players) >= game.max_players:
        raise HTTPException(400, 'Game is full')

    game.players.append(Player(player_id=player_id))
    if len(game.players) == game.max_players:
        game.status = 'active'
        game.started_at = tmsnow()

    await game.save()

    return {
        'status': game.status,
        'players': [p.player_id for p in game.players]
    }


@router.websocket(
    path='/ws/{game_id}'
)
async def game_ws(ws: WebSocket, game_id: str):
    await manager.connect(game_id, ws)

    try:
        game = await Game.get(game_id)
        await ws.send_json({'type': 'init', 'game': game.to_dict()})

        while True:
            data = await ws.receive_json()
            action: str = data.get('action')
            pid: str = data.get('player_id')

            idx = next((
                i for i, p in enumerate(game.players)
                if p.player_id == pid
            ), None)

            if idx is None:
                await ws.send_json({'detail': 'Player not in game'})
                continue

            if action == 'roll':
                d1, d2 = GameService.roll_dice()
                steps = d1 + d2

                # move player by steps
                GameService.move_player(game, idx, steps)

                await manager.broadcast(game_id, {
                    'type': 'rolled',
                    'player_id': pid,
                    'dice': [d1, d2],
                    'position': game.players[idx].position,
                    'balance': game.players[idx].balance
                })

            elif action == 'prompt_buy':
                # check if player can buy property
                prop = game.board[game.players[idx].position]

                can_buy = (
                    prop.owner_id is None and
                    game.players[idx].balance >= prop.price
                )

                await ws.send_json({
                    'type': 'can_buy',
                    'can_buy': can_buy,
                    'property': prop.to_dict()
                })

            elif action == 'buy':
                success = GameService.purchase_property(game, idx)
                await manager.broadcast(game_id, {
                    'type': 'bought',
                    'player_id': pid,
                    'success': success,
                    'property_id': game.board[game.players[idx].position].id,
                    'balance': game.players[idx].balance
                })

            await game.save()

    except Exception:
        pass
    finally:
        manager.disconnect(game_id, ws)

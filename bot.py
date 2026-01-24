import os
import json
import asyncio
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional

import discord
from discord import app_commands

STATE_FILE = "turn_state.json"
REMINDER_HOURS = 24


def normalize_game_name(name: str) -> str:
    return " ".join(name.lower().strip().split())


@dataclass
class TurnState:
    players: List[int]
    index: int
    active: bool
    reactions: List[int] = field(default_factory=list)
    message_id: Optional[int] = None

    def current_normal_player(self) -> int:
        return self.players[self.index]

    def current_actor(self) -> int:
        if self.reactions:
            return self.reactions[-1]
        return self.current_normal_player()

    def is_reacting(self) -> bool:
        return len(self.reactions) > 0

    def start_reaction(self, user_id: int) -> bool:
        if user_id in self.reactions:
            return False
        self.reactions.append(user_id)
        return True

    def resolve_reaction(self) -> Optional[int]:
        if not self.reactions:
            return None
        return self.reactions.pop()

    def advance_normal_turn(self) -> int:
        self.index = (self.index + 1) % len(self.players)
        return self.current_normal_player()


def load_state() -> Dict[str, TurnState]:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)

        out: Dict[str, TurnState] = {}
        for k, v in raw.items():
            out[k] = TurnState(
                players=list(map(int, v.get("players", []))),
                index=int(v.get("index", 0)),
                active=bool(v.get("active", False)),
                reactions=list(map(int, v.get("reactions", []))),
                message_id=v.get("message_id", None),
            )
        return out
    except Exception:
        return {}


def save_state(state: Dict[str, TurnState]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({k: asdict(v) for k, v in state.items()}, f, indent=2)


def state_key(channel_id: int, game: str) -> str:
    return f"{channel_id}:{normalize_game_name(game)}"


def parse_mentions(text: str) -> List[int]:
    ids: List[int] = []
    for token in text.replace(",", " ").split():
        if token.startswith("<@") and token.endswith(">"):
            token = token.replace("<@", "").replace(">", "").replace("!", "")
            if token.isdigit():
                uid = int(token)
                if uid not in ids:
                    ids.append(uid)
    return ids


def build_panel_text(game: str, state: TurnState, include_order: bool) -> str:
    game_norm = normalize_game_name(game)
    actor = f"<@{state.current_actor()}>"
    normal = f"<@{state.current_normal_player()}>"

    lines: List[str] = [f"Game: {game_norm}"]

    if include_order:
        order = ", ".join(f"<@{i}>" for i in state.players)
        lines.append(f"Order: {order}")

    if state.is_reacting():
        lines.append(f"Paused normal turn: {normal}")
        lines.append(f"Reacting now: {actor}")
        lines.append(f"{actor} it is your reaction turn. Click Done when finished.")
    else:
        lines.append(f"Current: {actor}")
        lines.append(f"{actor} it is your turn.")

    return "\n".join(lines)


async def safe_delete_message(channel: discord.abc.Messageable, message_id: Optional[int]) -> None:
    if not message_id:
        return
    try:
        if isinstance(channel, discord.TextChannel):
            msg = await channel.fetch_message(message_id)
            await msg.delete()
    except Exception:
        pass


async def replace_game_message(
    bot: "TurnBot",
    channel_id: int,
    game: str,
    content: str,
    old_message_id: Optional[int],
) -> Optional[int]:
    channel = bot.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return None

    view = TurnView(channel_id, game)
    bot.add_view(view)

    new_msg = await channel.send(content, view=view)
    await safe_delete_message(channel, old_message_id)
    return new_msg.id


async def reminder_task(bot: "TurnBot", key: str, channel_id: int, user_id: int):
    try:
        await asyncio.sleep(REMINDER_HOURS * 60 * 60)

        state = bot.games.get(key)
        if not state or not state.active:
            return
        if state.current_actor() != user_id:
            return

        game = key.split(":", 1)[1]
        content = build_panel_text(game, state, include_order=False) + "\n\nReminder: still waiting on you."
        new_id = await replace_game_message(bot, channel_id, game, content, state.message_id)

        if new_id:
            state.message_id = new_id
            save_state(bot.games)

    except asyncio.CancelledError:
        pass


def cancel_reminder(bot: "TurnBot", key: str) -> None:
    old = bot.reminder_tasks.pop(key, None)
    if old:
        old.cancel()


def start_reminder(bot: "TurnBot", key: str, channel_id: int, user_id: int) -> None:
    cancel_reminder(bot, key)
    bot.reminder_tasks[key] = asyncio.create_task(reminder_task(bot, key, channel_id, user_id))


class ReactionSelectView(discord.ui.View):
    def __init__(self, channel_id: int, game: str):
        super().__init__(timeout=60)
        self.channel_id = channel_id
        self.game = normalize_game_name(game)

        self.select = discord.ui.UserSelect(
            placeholder="Select the reacting player",
            min_values=1,
            max_values=1,
        )
        self.select.callback = self.on_select  # type: ignore
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        bot: "TurnBot" = interaction.client  # type: ignore
        key = state_key(self.channel_id, self.game)
        state = bot.games.get(key)

        if not state or not state.active:
            await interaction.response.send_message("No active game.", ephemeral=True)
            return

        normal_player = state.current_normal_player()
        if interaction.user.id != normal_player:
            await interaction.response.send_message(
                "Only the current normal turn player can start a reaction.",
                ephemeral=True,
            )
            return

        if state.is_reacting():
            await interaction.response.send_message("A reaction is already in progress.", ephemeral=True)
            return

        reacting_user = self.select.values[0]
        reacting_id = reacting_user.id

        if reacting_id == normal_player:
            await interaction.response.send_message("You cannot react to your own turn.", ephemeral=True)
            return

        if not state.start_reaction(reacting_id):
            await interaction.response.send_message("That player is already reacting.", ephemeral=True)
            return

        save_state(bot.games)
        start_reminder(bot, key, self.channel_id, reacting_id)

        content = build_panel_text(self.game, state, include_order=False)
        new_id = await replace_game_message(bot, self.channel_id, self.game, content, state.message_id)
        if new_id:
            state.message_id = new_id
            save_state(bot.games)

        await interaction.response.send_message("Reaction started.", ephemeral=True)


class DoneButton(discord.ui.Button):
    def __init__(self, channel_id: int, game: str):
        game_norm = normalize_game_name(game)
        super().__init__(
            label="Done",
            style=discord.ButtonStyle.success,
            custom_id=f"turn_done:{channel_id}:{game_norm}",
        )
        self.channel_id = channel_id
        self.game = game_norm

    async def callback(self, interaction: discord.Interaction) -> None:
        bot: "TurnBot" = interaction.client  # type: ignore
        key = state_key(self.channel_id, self.game)
        state = bot.games.get(key)

        if not state or not state.active:
            await interaction.response.send_message("No active game.", ephemeral=True)
            return

        if interaction.user.id != state.current_actor():
            await interaction.response.send_message("It is not your turn.", ephemeral=True)
            return

        old_message_id = state.message_id

        if state.is_reacting():
            state.resolve_reaction()
            save_state(bot.games)

            next_actor = state.current_actor()
            start_reminder(bot, key, self.channel_id, next_actor)

            content = build_panel_text(self.game, state, include_order=False)
            await interaction.response.send_message(content, view=TurnView(self.channel_id, self.game))

            try:
                msg = await interaction.original_response()
                state.message_id = msg.id
                save_state(bot.games)
            except Exception:
                pass

            if old_message_id:
                channel = bot.get_channel(self.channel_id)
                if isinstance(channel, discord.TextChannel):
                    await safe_delete_message(channel, old_message_id)
            return

        state.advance_normal_turn()
        save_state(bot.games)

        next_actor = state.current_actor()
        start_reminder(bot, key, self.channel_id, next_actor)

        content = build_panel_text(self.game, state, include_order=False)
        await interaction.response.send_message(content, view=TurnView(self.channel_id, self.game))

        try:
            msg = await interaction.original_response()
            state.message_id = msg.id
            save_state(bot.games)
        except Exception:
            pass

        if old_message_id:
            channel = bot.get_channel(self.channel_id)
            if isinstance(channel, discord.TextChannel):
                await safe_delete_message(channel, old_message_id)


class SkipButton(discord.ui.Button):
    def __init__(self, channel_id: int, game: str):
        game_norm = normalize_game_name(game)
        super().__init__(
            label="Skip",
            style=discord.ButtonStyle.secondary,
            custom_id=f"turn_skip:{channel_id}:{game_norm}",
        )
        self.channel_id = channel_id
        self.game = game_norm

    async def callback(self, interaction: discord.Interaction) -> None:
        bot: "TurnBot" = interaction.client  # type: ignore
        key = state_key(self.channel_id, self.game)
        state = bot.games.get(key)

        if not state or not state.active:
            await interaction.response.send_message("No active game.", ephemeral=True)
            return

        old_message_id = state.message_id

        if state.is_reacting():
            state.resolve_reaction()
        else:
            state.advance_normal_turn()

        save_state(bot.games)

        next_actor = state.current_actor()
        start_reminder(bot, key, self.channel_id, next_actor)

        content = build_panel_text(self.game, state, include_order=False)
        await interaction.response.send_message(content, view=TurnView(self.channel_id, self.game))

        try:
            msg = await interaction.original_response()
            state.message_id = msg.id
            save_state(bot.games)
        except Exception:
            pass

        if old_message_id:
            channel = bot.get_channel(self.channel_id)
            if isinstance(channel, discord.TextChannel):
                await safe_delete_message(channel, old_message_id)


class ReactButton(discord.ui.Button):
    def __init__(self, channel_id: int, game: str):
        game_norm = normalize_game_name(game)
        super().__init__(
            label="React",
            style=discord.ButtonStyle.primary,
            custom_id=f"turn_react:{channel_id}:{game_norm}",
        )
        self.channel_id = channel_id
        self.game = game_norm

    async def callback(self, interaction: discord.Interaction) -> None:
        bot: "TurnBot" = interaction.client  # type: ignore
        key = state_key(self.channel_id, self.game)
        state = bot.games.get(key)

        if not state or not state.active:
            await interaction.response.send_message("No active game.", ephemeral=True)
            return

        if interaction.user.id != state.current_normal_player():
            await interaction.response.send_message(
                "Only the current normal turn player can start a reaction.",
                ephemeral=True,
            )
            return

        if state.is_reacting():
            await interaction.response.send_message("A reaction is already in progress.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Pick the reacting player.",
            ephemeral=True,
            view=ReactionSelectView(self.channel_id, self.game),
        )


class EndButton(discord.ui.Button):
    def __init__(self, channel_id: int, game: str):
        game_norm = normalize_game_name(game)
        super().__init__(
            label="End Game",
            style=discord.ButtonStyle.danger,
            custom_id=f"turn_end:{channel_id}:{game_norm}",
        )
        self.channel_id = channel_id
        self.game = game_norm

    async def callback(self, interaction: discord.Interaction) -> None:
        bot: "TurnBot" = interaction.client  # type: ignore
        key = state_key(self.channel_id, self.game)
        state = bot.games.get(key)

        if not state or not state.active:
            await interaction.response.send_message("No active game.", ephemeral=True)
            return

        old_message_id = state.message_id

        state.active = False
        state.reactions = []
        state.message_id = None
        save_state(bot.games)

        cancel_reminder(bot, key)

        await interaction.response.send_message(f"Game ended: {self.game}", ephemeral=True)

        if old_message_id:
            channel = bot.get_channel(self.channel_id)
            if isinstance(channel, discord.TextChannel):
                await safe_delete_message(channel, old_message_id)


class TurnView(discord.ui.View):
    def __init__(self, channel_id: int, game: str):
        super().__init__(timeout=None)
        self.add_item(DoneButton(channel_id, game))
        self.add_item(ReactButton(channel_id, game))
        self.add_item(SkipButton(channel_id, game))
        self.add_item(EndButton(channel_id, game))


class TurnBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.games: Dict[str, TurnState] = load_state()
        self.reminder_tasks: Dict[str, asyncio.Task] = {}

    async def setup_hook(self) -> None:
        self.tree.add_command(turn)
        await self.tree.sync()

        for key, state in self.games.items():
            if not state.active:
                continue
            try:
                channel_id_str, game = key.split(":", 1)
                channel_id = int(channel_id_str)
            except Exception:
                continue
            self.add_view(TurnView(channel_id, game))


bot = TurnBot()
turn = app_commands.Group(name="turn", description="Turn order commands")


@turn.command(name="start")
@app_commands.describe(game="Game name", players="Mention players in turn order")
async def start(interaction: discord.Interaction, game: str, players: str):
    ids = parse_mentions(players)
    if len(ids) < 2:
        await interaction.response.send_message("Mention at least two players.", ephemeral=True)
        return

    game_norm = normalize_game_name(game)
    key = state_key(interaction.channel_id, game_norm)

    old_message_id: Optional[int] = None
    existing = bot.games.get(key)
    if existing:
        old_message_id = existing.message_id

    bot.games[key] = TurnState(players=ids, index=0, active=True, reactions=[], message_id=None)
    save_state(bot.games)

    start_reminder(bot, key, interaction.channel_id, ids[0])

    state = bot.games[key]
    content = build_panel_text(game_norm, state, include_order=True)

    await interaction.response.send_message(content, view=TurnView(interaction.channel_id, game_norm))
    try:
        msg = await interaction.original_response()
        state.message_id = msg.id
        save_state(bot.games)
    except Exception:
        pass

    if old_message_id:
        channel = bot.get_channel(interaction.channel_id)
        if isinstance(channel, discord.TextChannel):
            await safe_delete_message(channel, old_message_id)


@turn.command(name="panel", description="Repost the current controls for a game")
@app_commands.describe(game="Game name")
async def panel(interaction: discord.Interaction, game: str):
    game_norm = normalize_game_name(game)
    key = state_key(interaction.channel_id, game_norm)
    state = bot.games.get(key)

    if not state or not state.active:
        await interaction.response.send_message("No active game with that name.", ephemeral=True)
        return

    old_message_id = state.message_id
    content = build_panel_text(game_norm, state, include_order=False)

    await interaction.response.send_message(content, view=TurnView(interaction.channel_id, game_norm))
    try:
        msg = await interaction.original_response()
        state.message_id = msg.id
        save_state(bot.games)
    except Exception:
        pass

    if old_message_id:
        channel = bot.get_channel(interaction.channel_id)
        if isinstance(channel, discord.TextChannel):
            await safe_delete_message(channel, old_message_id)


@turn.command(name="status")
@app_commands.describe(game="Game name")
async def status(interaction: discord.Interaction, game: str):
    game_norm = normalize_game_name(game)
    key = state_key(interaction.channel_id, game_norm)
    state = bot.games.get(key)

    if not state or not state.active:
        await interaction.response.send_message("No active game.", ephemeral=True)
        return

    order = ", ".join(f"<@{i}>" for i in state.players)
    actor = f"<@{state.current_actor()}>"
    normal = f"<@{state.current_normal_player()}>"

    if state.is_reacting():
        text = (
            f"Game: {game_norm}\n"
            f"Order: {order}\n"
            f"Paused normal turn: {normal}\n"
            f"Reacting now: {actor}"
        )
    else:
        text = (
            f"Game: {game_norm}\n"
            f"Order: {order}\n"
            f"Current: {actor}"
        )

    await interaction.response.send_message(text, ephemeral=True)


@turn.command(name="list")
async def list_games(interaction: discord.Interaction):
    prefix = f"{interaction.channel_id}:"
    games = [
        k.split(":", 1)[1]
        for k, v in bot.games.items()
        if v.active and k.startswith(prefix)
    ]

    if not games:
        await interaction.response.send_message("No active games.", ephemeral=True)
        return

    await interaction.response.send_message("Active games: " + ", ".join(sorted(set(games))), ephemeral=True)


@turn.command(name="end")
@app_commands.describe(game="Game name")
async def end_game(interaction: discord.Interaction, game: str):
    game_norm = normalize_game_name(game)
    key = state_key(interaction.channel_id, game_norm)
    state = bot.games.get(key)

    if not state or not state.active:
        await interaction.response.send_message("No active game.", ephemeral=True)
        return

    old_message_id = state.message_id

    state.active = False
    state.reactions = []
    state.message_id = None
    save_state(bot.games)

    cancel_reminder(bot, key)

    await interaction.response.send_message(f"Game ended: {game_norm}", ephemeral=True)

    if old_message_id:
        channel = bot.get_channel(interaction.channel_id)
        if isinstance(channel, discord.TextChannel):
            await safe_delete_message(channel, old_message_id)


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set")
    bot.run(token)


if __name__ == "__main__":
    main()

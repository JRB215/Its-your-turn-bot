# It’s Your Turn!

It’s Your Turn! is a Discord bot designed to manage turn order for games and group activities where turns follow a fixed order. The bot keeps a single live control panel per game, automatically advances turns, and supports reactions, reminders, and undo actions.

This bot is ideal for tabletop games, async play by post games, and any situation where players take turns over time.

---

## Features

- Fixed, user defined turn order
- Multiple games per channel
- Single control message per game, automatically updated
- Done button to advance turns
- React system to temporarily pause a turn for reactions
- Skip button usable by anyone
- Nudge button to manually remind the current player
- 24 hour automatic reminder system
- Remove players mid game
- End games cleanly
- Undo last action
- Persistent state across bot restarts

---

## Commands

### `/turn start`
Start a new game.

**Parameters**
- `game` – Name of the game
- `players` – Mention players in turn order

Example:

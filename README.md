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

## Required Channel Permissions

For the bot to function correctly in a channel, it must be able to update the game panel message.

Ensure the bot (or its role) has the following permissions **in the channel where games are run**:

- View Channel
- Send Messages
- Read Message History

Optional:
- Manage Messages  
  Only required if you enable features that delete old panel messages instead of editing them.

If these permissions are missing, interactions such as **React**, **Done**, or **Remove** may fail.

---

## Commands

### `/turn start`
Start a new game.

**Parameters**
- `game` – Name of the game
- `players` – Mention players in turn order

Example:
/turn start game:Combat players:@Alice @Bob @Charlie

---

### `/turn panel`
Reposts the control panel for a game if it was lost in chat.

---

### `/turn status`
Shows the current state of a game privately.

---

### `/turn list`
Lists all active games in the current channel.

---

## Buttons

- **Done** – Ends the current turn
- **React** – Pause the turn and allow another player to react
- **Skip** – Skips the current turn
- **Nudge** – Sends a reminder to the current player
- **Undo** – Reverts the last turn affecting action
- **Remove** – Permanently removes a player from the game
- **End** – Ends the game

---

## Persistence

Game state is saved to `turn_state.json` and automatically restored when the bot restarts.

---

## Installation

1. Clone this repository
2. Create a Discord bot application
3. Set your bot token as an environment variable:
    DISCORD_TOKEN=your_token_here
4. Run:
    python bot.py
---

## License

MIT


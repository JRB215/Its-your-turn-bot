# It’s Your Turn Bot

A Discord bot for managing turn order in asynchronous games.

Designed for games with a fixed player order, reactions, and long turn windows.

Turn orders are never randomized and are defined fresh for each game instance.

---

## What This Bot Does

• Tracks whose turn it is  
• Lets the active player advance the turn  
• Supports reaction turns that temporarily pause the normal turn  
• Sends reminder pings if a player takes too long  
• Keeps controls available via buttons and slash commands  

Ideal for board games, tabletop RPGs, strategy games, or any async mobile games played over Discord.

---

## Starting a Game

Use the slash command:

/turn start

Fields  
• **game** A name for this game instance  
• **players** Mention players in the exact order they will take turns  

Example  
/turn start
game: root
players: @Alice @Bob @Charlie

The bot will post a message showing the current turn as well as a set of buttons.

---

## Buttons

### Done
• If it is your normal turn, ends your turn and advances to the next player  
• If you are reacting, ends your reaction and returns control to the paused player  

Only the current active player can use this button.

---

### React
• Only the current normal turn player can press this  
• Allows that player to select another user to react  
• The reacting player is pinged and becomes the active player  
• When the reacting player clicks Done, control returns to the original player  

This supports games where actions trigger interrupts or responses.

---

### End Game
Ends the game and clears all state for that game instance.

---

## Commands

### `/turn status`
Shows the current state of the game, including  
• Turn order  
• Current normal player  
• Current reacting player, if any  

---

### `/turn list`   (Not currently working)
Lists all active games in the current channel.

---

### `/turn panel`  (Not currently working)
Reposts the current game state and buttons.

Use this if  
• You joined late  
• The buttons scrolled out of view  
• You are on mobile and cannot find the controls  

---

### `/turn end`
Ends a game by name.

---

## Reminders

If the current active player does not click Done within 24 hours, the bot sends a reminder ping.

Reminders automatically switch when  
• A reaction starts  
• A reaction ends  
• The turn advances  

Only the current active player is reminded.

---

## Troubleshooting

If slash commands do not appear  
• Re invite the bot with `applications.commands` enabled  

If the game state seems unclear  
• Use `/turn status` or `/turn panel` to view the current state  

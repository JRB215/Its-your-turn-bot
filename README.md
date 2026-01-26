**Its Your Turn Bot**

Its Your Turn is a Discord bot designed for turn based and async games. 
It tracks a fixed turn order, handles reactions, reminders, and keeps the channel clean by maintaining a single live control message per game.

The bot is ideal for tabletop style games, roleplay systems, and async strategy games where turn order is intentional and may temporarily pause for reactions.

________________________________________________________________________
**Features**
  
  • Fixed turn order defined at game start
  
  • One active control message per game
  
  • Done button to complete turns
  
  • React button to pause a turn and trigger a reaction
  
  • Skip button that anyone can use to advance the game
  
  • Automatic resume after reactions
  
  • 24 hour reminder pings for the current actor
  
  • Support for multiple games per channel
  
  • Slash command control and button driven play

______________________________________________________________
**How Turn Flow Works**

 • A game starts with a specific player order
  
 • The current player takes their turn
  
 • They click Done when finished

______________________________________________________________
**Optional reaction flow**

  • The current normal turn player may click React
  
  • They select another player to react
  
  • The normal turn pauses
  
  • The reacting player takes their turn
  
  • When done, the game resumes to the original player

At any time

  • Anyone may click Skip to move the game forward  
  
  • Skip ends reactions or advances the normal turn

______________________________________________________________
**Commands**

Start a game

/turn start game:<name> players:<mentions in order>


This posts the control panel and pings all players once at game start.

Repost the control panel

/turn panel game:<name>


Useful if the message was lost in chat.

Check game status

/turn status game:<name>


Shows the current turn state privately.

List active games

/turn list


Lists all active games in the current channel.

End a game

/turn end game:<name>

Ends the game and removes the control panel.

______________________________________________________________
**Reminders**

• Default reminder time is 24 hours

• Only the current actor is pinged

• Reminders reset whenever the active player changes

• No spam reminders are sent to the whole group

______________________________________________________________
**Permissions Required**

The bot requires the following channel permissions:

• Send Messages

• Manage Messages

• Read Message History

• Use Slash Commands

Manage Messages is required to keep only one active control message per game.

______________________________________________________________
**Installation Notes**

• This bot is intended for Guild install, not User install

• Slash commands may take a moment to sync on first install

• During development, guild scoped command sync is recommended

______________________________________________________________
**Data Persistence**
Game state is stored locally in turn_state.json.

If the bot restarts:

• Active games resume

• Control buttons remain functional

• Reminders continue correctly

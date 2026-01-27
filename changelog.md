# Changelog

All notable changes to this project are documented here.

---

## v1.4
Undo system and final feature set

	- Added Undo button to revert the last turn affecting action
	- Undo works for Done, Skip, React, Remove, and End
	- Undo history persisted across restarts
	- History capped to prevent unbounded growth
	- Finalized single message per game behavior

---

## v1.3
Turn flow safety and reminders
	
	- Added Nudge button to manually remind the current player
	- Confirmation required for Remove and End actions
	- Reduced accidental destructive actions

---

## v1.2
Quality of life and moderation controls

	- Skip button usable by anyone
	- Remove players mid game
	- Automatic game end when too few players remain
	- Improved reminder handling after skips and removals

---

## v1.1
Turn flow improvements and stability

	- Single active control message per game
	- Automatic cleanup of old bot messages
	- Reaction system to pause and resume turns
	- Panel command to repost controls
	- 24 hour reminder system
	- Improved restart recovery

---

## v1.0
Initial release

	- Fixed turn order system
	- Slash command controls
	- Persistent state storage

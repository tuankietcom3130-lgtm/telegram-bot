# Telegram Bot

A smart Telegram bot with group membership verification and file sharing based on user preferences.

## Features

✅ **Group Membership Verification** - Only group members can use the bot
✅ **User Preferences** - Users can set their preferred file types
✅ **File Type Support** - Documents, Images, Videos, Audio
✅ **Preference Management** - View and modify preferences anytime
✅ **Preference-based Sharing** - Send files matching user preferences

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Telegram Bot Token (get it from BotFather on Telegram)
- Group ID (the group where you want to verify membership)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```
   BOT_TOKEN=your_bot_token_here
   GROUP_ID=your_group_id_here
   ```

## Getting Your IDs

### Bot Token
1. Open Telegram and search for `@BotFather`
2. Create a new bot with `/newbot`
3. Copy the token provided

### Group ID
1. Add your bot to your group
2. Forward a message from the group to `@userinfobot`
3. Copy the Group ID from the response

## Running the Bot

```bash
python main.py
```

## Commands

- `/start` - Start the bot (checks group membership)
- `/help` - Show help information
- `/preferences` - Set your file type preferences
- `/mypreferences` - View your current preferences
- `/send_files` - Send files based on your preferences

### Preference Commands

- `/pref_document` - Prefer documents (PDF, DOCX, etc.)
- `/pref_image` - Prefer images (JPG, PNG, etc.)
- `/pref_video` - Prefer videos (MP4, MOV, etc.)
- `/pref_audio` - Prefer audio (MP3, WAV, etc.)

## How It Works

1. **User starts bot** → Bot checks if they're in the group
2. **If member** → User can set preferences using preference commands
3. **Multiple preferences** → Users can select multiple file types
4. **Send files** → Bot sends files matching user's preferences

## File Storage

User preferences are automatically saved to `user_preferences.json` with the following structure:

```json
{
  "user_id": {
    "username": "username",
    "file_types": ["document", "image"]
  }
}
```

## Project Structure

```
telegram-bot/
├── main.py                  # Main bot file with all handlers
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in repo)
├── .env.example             # Example environment configuration
├── .gitignore               # Git ignore rules
├── user_preferences.json    # User preferences (auto-generated)
└── README.md               # This file
```

## Error Handling

The bot includes comprehensive error handling:
- Group membership verification with error logging
- User preference persistence
- Telegram API error handling
- Graceful error messages for users

## License

MIT

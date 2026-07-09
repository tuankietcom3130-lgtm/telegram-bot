# Telegram Bot

A smart Telegram bot with group membership verification and file sharing based on user preferences.

## Features

✅ **Group Membership Verification** - Only group members can use the bot
✅ **User Preferences** - Users can set their preferred file types
✅ **File Type Support** - Documents, Images, Videos, Audio
✅ **Preference Management** - View and modify preferences anytime
✅ **Preference-based File Sharing** - Send files matching user preferences
✅ **File Organization** - Automatic directory structure for different file types
✅ **List Files** - Users can browse available files before downloading

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Telegram Bot Token (get it from BotFather on Telegram)
- Group ID (the group where you want to verify membership)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-bot.git
   cd telegram-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env and add your values
   ```

4. Create the file storage directories:
   ```bash
   mkdir -p files/{documents,images,videos,audio}
   ```

## Getting Your IDs

### Bot Token
1. Open Telegram and search for `@BotFather`
2. Create a new bot with `/newbot`
3. Copy the token provided
4. Add it to your `.env` file as `BOT_TOKEN=...`

### Group ID
1. Add your bot to your group
2. Forward a message from the group to `@userinfobot`
3. Copy the Group ID from the response (should be negative number)
4. Add it to your `.env` file as `GROUP_ID=...`

## File Storage Structure

The bot automatically creates and uses this directory structure:

```
files/
├── documents/     # Store PDF, DOCX, TXT files here
├── images/        # Store JPG, PNG, GIF files here
├── videos/        # Store MP4, MOV, AVI files here
└── audio/         # Store MP3, WAV, M4A files here
```

### How to Add Files

Simply copy your files into the appropriate directories:

```bash
# Add a PDF document
cp my_document.pdf files/documents/

# Add an image
cp photo.jpg files/images/

# Add a video
cp video.mp4 files/videos/

# Add an audio file
cp song.mp3 files/audio/
```

Users will only see files matching their selected preferences!

## Running the Bot

```bash
python main.py
```

You should see:
```
🤖 Bot is starting...
GROUP_ID configured: -1001234567890
Files directory structure created at: files
Press Ctrl+C to stop the bot
```

## Commands

### User Commands

- `/start` - Start the bot (checks group membership)
- `/help` - Show all available commands
- `/preferences` - View and set your file type preferences
- `/mypreferences` - View your current preferences
- `/list_files` - List all available files for your preferences
- `/send_files` - Download all files matching your preferences

### Preference Setting Commands

- `/pref_document` - Add documents to your preferences (PDF, DOCX, etc.)
- `/pref_image` - Add images to your preferences (JPG, PNG, etc.)
- `/pref_video` - Add videos to your preferences (MP4, MOV, etc.)
- `/pref_audio` - Add audio to your preferences (MP3, WAV, etc.)

## How It Works

```
1. User sends /start
   ↓
2. Bot checks if user is in the group
   ├─ If NO → Send error message
   └─ If YES → Send welcome message
   
3. User sets preferences with /pref_* commands
   ↓
4. Preferences saved to user_preferences.json
   ↓
5. User sends /list_files
   ├─ Bot reads files/documents/, files/images/, etc.
   └─ Shows matching files
   
6. User sends /send_files
   ├─ Bot checks preferences
   ├─ Sends all matching files
   └─ Shows summary
```

## File Storage Details

### User Preferences

Preferences are automatically saved to `user_preferences.json`:

```json
{
  "123456789": {
    "username": "john_doe",
    "file_types": ["document", "image"]
  },
  "987654321": {
    "username": "jane_smith",
    "file_types": ["video", "audio"]
  }
}
```

### Example File Organization

```
files/
├── documents/
│   ├── guide.pdf
│   ├── manual.docx
│   └── notes.txt
├── images/
│   ├── logo.png
│   ├── banner.jpg
│   └── screenshot.png
├── videos/
│   ├── tutorial.mp4
│   └── demo.mov
└── audio/
    ├── podcast.mp3
    └── music.wav
```

## Project Structure

```
telegram-bot/
├── main.py                  # Main bot file with all handlers
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (created by user)
├── .env.example             # Example environment configuration
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── user_preferences.json    # User preferences (auto-generated)
└── files/                   # File storage directory
    ├── documents/
    ├── images/
    ├── videos/
    └── audio/
```

## Error Handling

The bot includes comprehensive error handling:

- ✅ Group membership verification with error logging
- ✅ User preference persistence and validation
- ✅ Telegram API error handling
- ✅ File I/O error handling
- ✅ Graceful error messages for users
- ✅ Detailed server-side logging

## Troubleshooting

### Bot doesn't respond
- Check that BOT_TOKEN is correct in `.env`
- Make sure the bot is added to your group
- Verify GROUP_ID is correct

### Files not appearing
- Check that files are in the correct directories under `files/`
- Verify file permissions (readable)
- Check the bot's console for error messages

### "You need to be a member" error
- Verify you're in the group where the bot was added
- Check GROUP_ID is correct
- Make sure you're using the same Telegram account

## Deployment

### Using Systemd (Linux)

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/telegram-bot
ExecStart=/usr/bin/python3 /home/YOUR_USER/telegram-bot/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then run:
```bash
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot
```

### Using Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t telegram-bot .
docker run -e BOT_TOKEN=your_token -e GROUP_ID=your_id telegram-bot
```

## License

MIT

## Support

For issues or questions, please create a GitHub issue in this repository.

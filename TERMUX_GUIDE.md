# Telegram Bot - Termux Installation Guide

This guide will help you run your Telegram bot on Android using Termux.

## 📱 What is Termux?

Termux is a terminal emulator and Linux environment for Android. It allows you to run Linux commands and Python scripts directly on your Android phone.

## 🚀 Step-by-Step Installation

### **Step 1: Install Termux**

1. Go to Google Play Store or F-Droid
2. Search for "Termux"
3. Install the official Termux app
4. Open Termux

### **Step 2: Update Termux**

Run these commands in Termux:

```bash
pkg update
pkg upgrade
```

Answer "y" (yes) when prompted.

### **Step 3: Install Python and Git**

```bash
pkg install python git
```

Answer "y" when prompted. This may take a few minutes.

### **Step 4: Install Required Tools**

```bash
pkg install nano curl wget
```

### **Step 5: Clone Your Bot Repository**

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/yourusername/telegram-bot.git

# Navigate to the bot directory
cd telegram-bot
```

Replace `yourusername` with your actual GitHub username.

### **Step 6: Install Python Dependencies**

```bash
pip install -r requirements.txt
```

This installs all required libraries. It may take a few minutes.

### **Step 7: Configure Your Bot**

Create the `.env` file with your credentials:

```bash
nano .env
```

This opens the text editor. Type:

```
BOT_TOKEN=your_bot_token_here
GROUP_ID=your_group_id_here
```

To save and exit:
- Press `Ctrl + X`
- Press `Y` (yes)
- Press `Enter`

### **Step 8: Add Your Files**

Add files to the directories:

```bash
# Navigate to files directory
cd files

# List available directories
ls

# Add files
# Copy your files to: documents/, images/, videos/, or audio/
```

### **Step 9: Run Your Bot**

```bash
# Navigate back to bot directory
cd ~/telegram-bot

# Run the bot
python main.py
```

You should see:
```
🤖 Bot is starting...
GROUP_ID configured: -1001234567890
Files directory structure created at: files
Press Ctrl+C to stop the bot
```

## 🛑 Stopping the Bot

To stop the bot:
- Press `Ctrl + C`

## 🔄 Starting the Bot Again

```bash
cd ~/telegram-bot
python main.py
```

## 📋 Useful Termux Commands

```bash
# List files and folders
ls

# Change directory
cd folder_name

# Go back to home directory
cd ~

# View file contents
cat filename.txt

# Edit a file
nano filename.txt

# Create a new folder
mkdir folder_name

# Remove a file
rm filename

# Remove a folder
rm -r folder_name

# Check current directory
pwd

# Clear screen
clear
```

## ⚠️ Important Notes

### **Keeping Termux Running**

Termux sessions close when you exit the app or your phone locks. To keep your bot running:

**Option 1: Keep Phone Awake**
- Don't close the Termux app
- Keep your phone screen on
- Keep your phone plugged in

**Option 2: Use a Screen Multiplexer (Advanced)**

```bash
pkg install tmux
tmux new-session -d -s bot 'cd ~/telegram-bot && python main.py'
```

**Option 3: Run 24/7 (Recommended)**
Deploy to a cloud server like:
- Heroku (free tier)
- Replit
- Railway
- PythonAnywhere

### **Storage Access**

If you want to access files from your phone's storage:

```bash
# Get storage access
termux-setup-storage

# Your downloads folder will be at:
# ~/storage/downloads/
```

### **Network Issues**

If the bot disconnects:
- Check your internet connection
- Restart Termux: Close and reopen the app
- Run `python main.py` again

### **Update Bot Code**

If you update your bot on GitHub:

```bash
cd ~/telegram-bot
git pull
```

Then restart the bot:

```bash
python main.py
```

## 🐛 Troubleshooting

### **"Command not found" error**

Make sure you're in the correct directory:
```bash
cd ~/telegram-bot
```

### **"ModuleNotFoundError" error**

Reinstall dependencies:
```bash
pip install -r requirements.txt
```

### **Bot doesn't respond**

1. Check if the bot is still running (you should see output)
2. Verify BOT_TOKEN and GROUP_ID in `.env` are correct
3. Make sure you're in the Telegram group
4. Restart the bot with `Ctrl + C` then `python main.py`

### **Files not found**

Make sure files are in correct directories:
```bash
cd ~/telegram-bot/files
ls -R
```

You should see:
```
audio/
documents/
images/
videos/
```

### **Permission denied error**

Try:
```bash
pkg install termux-tools
```

## 📱 Phone Requirements

- **Android 5.0+**
- **Storage:** ~200MB for Termux and dependencies
- **RAM:** 1GB recommended
- **Internet:** WiFi or mobile data (WiFi recommended for stability)

## 💾 Backing Up Your Bot

To save your bot configuration:

```bash
cd ~/telegram-bot

# Copy your .env file to storage
cp .env ~/storage/downloads/.env_backup

# Copy your preferences
cp user_preferences.json ~/storage/downloads/preferences_backup.json
```

## 🔐 Security Tips

⚠️ **Important:** Never share your:
- BOT_TOKEN
- GROUP_ID
- Any credentials in `.env`

**Never commit `.env` to Git!** It's already in `.gitignore` for safety.

## 📚 Additional Resources

- [Termux Documentation](https://wiki.termux.com/)
- [Python Documentation](https://docs.python.org/3/)
- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)

## ✅ Quick Start Checklist

- [ ] Installed Termux
- [ ] Updated Termux (`pkg update && pkg upgrade`)
- [ ] Installed Python and Git (`pkg install python git`)
- [ ] Cloned repository (`git clone ...`)
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Created `.env` file with credentials
- [ ] Added files to `files/` directories
- [ ] Bot running (`python main.py`)
- [ ] Bot responding to `/start` command

## 🚀 You're All Set!

Your Telegram bot is now running on your Android phone via Termux! 🎉

For best results, use a cloud server for 24/7 operation instead of your phone.

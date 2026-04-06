# Financebot

A Telegram bot to track **expenses**, **income**, and **investments** in **NPR (Nepalese Rupee)**. Data is stored locally in a SQLite database per user.

## Features

- Track expenses by category (Food, Transport, Shopping, Health, etc.)
- Track income by source (Salary, Freelance, Business, etc.)
- Track investments by type (Stocks, Mutual Funds, Fixed Deposit, Gold, Crypto, etc.)
- View financial summaries by: Today / This Week / This Month / This Year / All Time
- View last 10 transactions
- Per-user data isolation (each Telegram user has their own records)

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and command list |
| `/add_expense` | Record an expense |
| `/add_income` | Record income |
| `/add_investment` | Record an investment |
| `/summary` | View financial summary by time period |
| `/recent` | View last 10 transactions |
| `/cancel` | Cancel current operation |
| `/skip` | Skip optional description |

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Bhuwa1/Financebot.git
cd Financebot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a Telegram Bot Token

1. Open Telegram and talk to [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the token you receive

### 4. Set the environment variable

```bash
export TELEGRAM_BOT_TOKEN=your_token_here
```

Or create a `.env` file:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

### 5. Run the bot

```bash
python bot.py
```

## Database

A SQLite database (`finance_tracker.db`) is created automatically in the project directory on first run. No setup needed.

## Tech Stack

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v20
- SQLite (built-in)

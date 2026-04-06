import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from database import init_db, add_transaction, get_summary, get_recent_transactions

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Transport",
    "Shopping",
    "Health",
    "Entertainment",
    "Education",
    "Utilities",
    "Rent",
    "Other",
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Business",
    "Investment Return",
    "Gift",
    "Other",
]

INVESTMENT_CATEGORIES = [
    "Stocks",
    "Mutual Funds",
    "Fixed Deposit",
    "Real Estate",
    "Gold",
    "Crypto",
    "Other",
]

(
    EXPENSE_CATEGORY,
    EXPENSE_AMOUNT,
    EXPENSE_DESC,
    INCOME_CATEGORY,
    INCOME_AMOUNT,
    INCOME_DESC,
    INVESTMENT_CATEGORY,
    INVESTMENT_AMOUNT,
    INVESTMENT_DESC,
    SUMMARY_PERIOD,
) = range(10)


def format_npr(amount: float) -> str:
    return f"NPR {amount:,.2f}"


def make_category_keyboard(categories: list) -> ReplyKeyboardMarkup:
    rows = [categories[i:i+3] for i in range(0, len(categories), 3)]
    rows.append(["Cancel"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"Hello, {user.first_name}! I'm your personal finance tracker.\n\n"
        "All amounts are in NPR (Nepalese Rupee).\n\n"
        "Here's what you can do:\n"
        "/add_expense — Record an expense\n"
        "/add_income — Record income\n"
        "/add_investment — Record an investment\n"
        "/summary — View financial summary\n"
        "/recent — View recent transactions\n"
        "/help — Show this message"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Finance Tracker Commands:\n\n"
        "/add_expense — Record an expense\n"
        "/add_income — Record income\n"
        "/add_investment — Record an investment\n"
        "/summary — View your financial summary\n"
        "/recent — View recent 10 transactions\n"
        "/help — Show this message"
    )
    await update.message.reply_text(text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Cancelled. Use /help to see available commands.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── ADD EXPENSE ────────────────────────────────────────────────────────────

async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "What category is this expense?",
        reply_markup=make_category_keyboard(EXPENSE_CATEGORIES),
    )
    return EXPENSE_CATEGORY


async def expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Cancel":
        return await cancel(update, context)
    context.user_data["category"] = text
    await update.message.reply_text(
        f"Category: *{text}*\n\nEnter the amount in NPR (numbers only):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please enter a valid positive number (e.g. 500 or 1500.50):")
        return EXPENSE_AMOUNT

    context.user_data["amount"] = amount
    await update.message.reply_text(
        "Add a short description (or send /skip to skip):"
    )
    return EXPENSE_DESC


async def expense_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text.strip()
    return await save_expense(update, context)


async def expense_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = None
    return await save_expense(update, context)


async def save_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    amount = context.user_data["amount"]
    category = context.user_data["category"]
    description = context.user_data.get("description")

    add_transaction(user_id, "expense", amount, category, description)

    desc_line = f"\nNote: {description}" if description else ""
    await update.message.reply_text(
        f"Expense recorded!\n\n"
        f"Amount: *{format_npr(amount)}*\n"
        f"Category: {category}{desc_line}",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─── ADD INCOME ─────────────────────────────────────────────────────────────

async def add_income_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "What is the source of this income?",
        reply_markup=make_category_keyboard(INCOME_CATEGORIES),
    )
    return INCOME_CATEGORY


async def income_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Cancel":
        return await cancel(update, context)
    context.user_data["category"] = text
    await update.message.reply_text(
        f"Category: *{text}*\n\nEnter the amount in NPR:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return INCOME_AMOUNT


async def income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please enter a valid positive number:")
        return INCOME_AMOUNT

    context.user_data["amount"] = amount
    await update.message.reply_text("Add a short description (or send /skip to skip):")
    return INCOME_DESC


async def income_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text.strip()
    return await save_income(update, context)


async def income_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = None
    return await save_income(update, context)


async def save_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    amount = context.user_data["amount"]
    category = context.user_data["category"]
    description = context.user_data.get("description")

    add_transaction(user_id, "income", amount, category, description)

    desc_line = f"\nNote: {description}" if description else ""
    await update.message.reply_text(
        f"Income recorded!\n\n"
        f"Amount: *{format_npr(amount)}*\n"
        f"Category: {category}{desc_line}",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─── ADD INVESTMENT ──────────────────────────────────────────────────────────

async def add_investment_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "What type of investment is this?",
        reply_markup=make_category_keyboard(INVESTMENT_CATEGORIES),
    )
    return INVESTMENT_CATEGORY


async def investment_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Cancel":
        return await cancel(update, context)
    context.user_data["category"] = text
    await update.message.reply_text(
        f"Category: *{text}*\n\nEnter the amount in NPR:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return INVESTMENT_AMOUNT


async def investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please enter a valid positive number:")
        return INVESTMENT_AMOUNT

    context.user_data["amount"] = amount
    await update.message.reply_text("Add a short description (or send /skip to skip):")
    return INVESTMENT_DESC


async def investment_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text.strip()
    return await save_investment(update, context)


async def investment_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = None
    return await save_investment(update, context)


async def save_investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    amount = context.user_data["amount"]
    category = context.user_data["category"]
    description = context.user_data.get("description")

    add_transaction(user_id, "investment", amount, category, description)

    desc_line = f"\nNote: {description}" if description else ""
    await update.message.reply_text(
        f"Investment recorded!\n\n"
        f"Amount: *{format_npr(amount)}*\n"
        f"Category: {category}{desc_line}",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─── SUMMARY ────────────────────────────────────────────────────────────────

async def summary_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [["Today", "This Week"], ["This Month", "This Year"], ["All Time"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Select the time period for the summary:",
        reply_markup=keyboard,
    )
    return SUMMARY_PERIOD


PERIOD_MAP = {
    "today": "today",
    "this week": "week",
    "this month": "month",
    "this year": "year",
    "all time": "all",
}


async def summary_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    period_key = PERIOD_MAP.get(text, "month")
    period_label = update.message.text.strip()

    user_id = update.effective_user.id
    data = get_summary(user_id, period=period_key)

    income_total = data["income"]["total"]
    expense_total = data["expenses"]["total"]
    investment_total = data["investments"]["total"]
    net = income_total - expense_total - investment_total
    net_sign = "+" if net >= 0 else ""

    lines = [f"Financial Summary — {period_label}\n"]

    lines.append(f"Income:      {format_npr(income_total)}")
    lines.append(f"Expenses:    {format_npr(expense_total)}")
    lines.append(f"Investments: {format_npr(investment_total)}")
    lines.append(f"Net Balance: {net_sign}{format_npr(net)}\n")

    if data["income"]["by_category"]:
        lines.append("Income by Category:")
        for row in data["income"]["by_category"]:
            lines.append(f"  • {row['category']}: {format_npr(row['total'])} ({row['count']} entries)")
        lines.append("")

    if data["expenses"]["by_category"]:
        lines.append("Expenses by Category:")
        for row in data["expenses"]["by_category"]:
            lines.append(f"  • {row['category']}: {format_npr(row['total'])} ({row['count']} entries)")
        lines.append("")

    if data["investments"]["by_category"]:
        lines.append("Investments by Category:")
        for row in data["investments"]["by_category"]:
            lines.append(f"  • {row['category']}: {format_npr(row['total'])} ({row['count']} entries)")

    if not any([
        data["income"]["by_category"],
        data["expenses"]["by_category"],
        data["investments"]["by_category"],
    ]):
        lines.append("No transactions found for this period.")

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── RECENT TRANSACTIONS ─────────────────────────────────────────────────────

async def recent_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transactions = get_recent_transactions(user_id, limit=10)

    if not transactions:
        await update.message.reply_text("No transactions recorded yet. Use /add_expense, /add_income, or /add_investment to get started.")
        return

    type_icons = {"expense": "🔴", "income": "🟢", "investment": "🔵"}
    type_labels = {"expense": "Expense", "income": "Income", "investment": "Investment"}

    lines = ["Recent Transactions (last 10):\n"]
    for tx in transactions:
        icon = type_icons.get(tx["type"], "⚪")
        label = type_labels.get(tx["type"], tx["type"].title())
        desc = f" — {tx['description']}" if tx.get("description") else ""
        lines.append(
            f"{icon} {tx['date']}  {format_npr(tx['amount'])}\n"
            f"   {label} · {tx['category']}{desc}"
        )

    await update.message.reply_text("\n".join(lines))


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    init_db()

    app = Application.builder().token(token).build()

    expense_conv = ConversationHandler(
        entry_points=[CommandHandler("add_expense", add_expense_start)],
        states={
            EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_category)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
            EXPENSE_DESC: [
                CommandHandler("skip", expense_skip_desc),
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_desc),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    income_conv = ConversationHandler(
        entry_points=[CommandHandler("add_income", add_income_start)],
        states={
            INCOME_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_category)],
            INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, income_amount)],
            INCOME_DESC: [
                CommandHandler("skip", income_skip_desc),
                MessageHandler(filters.TEXT & ~filters.COMMAND, income_desc),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    investment_conv = ConversationHandler(
        entry_points=[CommandHandler("add_investment", add_investment_start)],
        states={
            INVESTMENT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, investment_category)],
            INVESTMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, investment_amount)],
            INVESTMENT_DESC: [
                CommandHandler("skip", investment_skip_desc),
                MessageHandler(filters.TEXT & ~filters.COMMAND, investment_desc),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    summary_conv = ConversationHandler(
        entry_points=[CommandHandler("summary", summary_start)],
        states={
            SUMMARY_PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, summary_period)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("recent", recent_transactions))
    app.add_handler(expense_conv)
    app.add_handler(income_conv)
    app.add_handler(investment_conv)
    app.add_handler(summary_conv)

    logger.info("Bot started. Polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

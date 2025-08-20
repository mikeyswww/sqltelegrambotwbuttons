from telegram.ext import MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

TOKEN = "BOT_TOKEN"

# Подключение к базе данных
conn = sqlite3.connect("notes.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    note TEXT
)
""")
conn.commit()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить заметку", callback_data="add")],
        [InlineKeyboardButton("📋 Посмотреть заметки", callback_data="list")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выбери действие:", reply_markup=reply_markup)

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add":
        await query.edit_message_text("Отправь мне текст заметки прямо в чат.")
        context.user_data["adding"] = True

    elif query.data == "list":
        cursor.execute("SELECT id, note FROM notes WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        if not rows:
            await query.edit_message_text("У тебя пока нет заметок.")
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {row[1]}", callback_data=f"delete_{row[0]}")]
            for row in rows
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Твои заметки (нажми для удаления):", reply_markup=reply_markup)

    elif query.data.startswith("delete_"):
        note_id = int(query.data.split("_")[1])
        cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        conn.commit()
        await query.edit_message_text("Заметка удалена!")

# Получение текстового сообщения для добавления заметки
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("adding"):
        note_text = update.message.text
        cursor.execute("INSERT INTO notes (user_id, note) VALUES (?, ?)", (update.effective_user.id, note_text))
        conn.commit()
        context.user_data["adding"] = False
        await update.message.reply_text("✅ Заметка добавлена!")

# Основная функция
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters=None, callback=message_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

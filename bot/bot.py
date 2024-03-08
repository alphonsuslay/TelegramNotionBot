from typing import Final
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, ConversationHandler, CallbackContext
import json


import requests
from datetime import datetime, timezone



token: Final = 'TOKEN'
username: Final = '@Notion Tracker'

TOKEN = "TOKEN"
DATABASE_ID = "DATABASE ID"

headers = {
    "Authorization": "Bearer " + TOKEN,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Send a welcome message with the inline keyboard
    await update.message.reply_text("Welcome! I am here to help! If you need assistance, use the help command.")
      
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    numpages = 5 
    getAll = numpages is None
    pagesize = 100 if getAll else numpages

    payload = {"page_size": pagesize}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    import json

    results = data["results"]
    while data["has_more"] and getAll :
        payload = {"page_size": pagesize, "start_cursor": data["next_cursor"]}
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    info_text = "**Information from Budget Tracker**\n\n"
    info_data = []

    for page in results:
        props = page["properties"]
        page_id = page["id"]
        Name = props["Name"]["title"][0]["text"]["content"]
        Budget = props["Budget"]["number"]
        Spending = props["Spending"]["number"]
        published = props["Date"]["date"]["start"]
        published = datetime.fromisoformat(published)
        balance_number = props["Balance"]["formula"]["number"]

        info_text += f"Item: {Name}\n • Budget: {Budget}\n • Spending: {Spending}\n • Balance: {balance_number}\n\n\n"

        # Store the page information in a dictionary
        page_info = {
            "page_id": page_id,
            "Name": Name,
        }

        info_data.append(page_info)

    # Save the information to db.json
    with open('db.json', 'w', encoding='utf8') as info_file:
        json.dump(info_data, info_file, ensure_ascii=False, indent=4)

    # Send the information to the user with Markdown formatting
    await update.message.reply_markdown(info_text)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the command has additional parameters
    if len(context.args) < 3:
        await update.message.reply_text("Please provide input in the format: `/add Name, Budget, Spending`")
        return

    # Extract user input
    input_data = context.args[:3]
    Name, Budget, Spending = map(str.strip, input_data)

    # Remove commas from Budget and Spending to ensure they can be converted to float
    Budget = Budget.replace(',', '')
    Spending = Spending.replace(',', '')

    try:
        # Convert Budget and Spending to float
        Budget = float(Budget)
        Spending = float(Spending)
    except ValueError:
        await update.message.reply_text("Invalid input for Budget or Spending. Please provide numeric values.")
        return

    # Get the current date and time
    current_datetime = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    # Create a new item in the Notion database
    url = f"https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": Name}}]},
            "Budget": {"number": Budget},
            "Spending": {"number": Spending},
            "Date": {"date": {"start": current_datetime}}
        }
    }
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        await update.message.reply_text("Item added successfully!")
    else:
        await update.message.reply_text("Error adding item. Please try again.")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Your help command code
    commands = [
        ("/start", "Start the bot"),
        ("/help", "Display available commands"),
        ("/info", "Displays Table information"),
        ("/update [item], [Budget/Spending], [Amount]", "Modify item"), 
        ("/add [item], [Budget Amt], [Spending Amt]", "Adds item to table")
    ]

    response_text = "Available commands:\n\n"
    for command, description in commands:
        response_text += f"{command}: {description}\n\n"

    await update.message.reply_text(response_text)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")
    

def update_notion(page_id: str, data: dict):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"properties": data}

    res = requests.patch(url, json=payload, headers=headers)

async def update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the command has additional parameters
    if len(context.args) != 3:
        await update.message.reply_text("Please provide input in the format: `/update Name Property Amount`")
        return

    # Extract user input
    Name, Property, Amount = map(str.strip, context.args)

    # Load data from db.json
    with open('db.json', 'r', encoding='utf8') as info_file:
        info_data = json.load(info_file)

    # Find the entry with the matching Name
    entry = next((item for item in info_data if item["Name"] == Name), None)

    if entry:
        # Extract the page_id from the matched entry
        page_id = entry["page_id"]

        # Update the corresponding property with the new amount
        update_data = {Property: {"number": int(Amount)}}

        # Perform the update in Notion
        update_notion(page_id, update_data)

        await update.message.reply_text(f"Updated {Name}'s {Property} to {Amount}")
    else:
        await update.message.reply_text(f"No entry found for {Name}")


if __name__ == '__main__':
    print("Bot is ready.")
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('info', info))
    app.add_handler(CommandHandler('add', add))
    app.add_handler(CommandHandler('update', update))


    # Errors
    app.add_error_handler(error)

    # Polls the Bot
    print("Polling...")
    app.run_polling(poll_interval=3)
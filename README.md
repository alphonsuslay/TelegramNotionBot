# TelegramNotionBot
Made a telegram bot that can access your budget tracker in Notion.

##Commands
```/start: Start the bot

/help: Display available commands

/info: Displays Table information

/update [item], [Budget/Spending], [Amount]: Modify item

/add [item], [Budget Amt], [Spending Amt]: Adds item to table```


##How it works
Uses GET and POST request to the database in Notion. 
For retrieving information, the data is stored in db.json and parsed to retrieve the relevant information.
For sending information. it sends a POST request to the Notion

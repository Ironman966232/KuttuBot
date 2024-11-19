from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from urllib.parse import urlparse

from info import *
from database.ia_filterdb import unpack_new_file_id

mongo_client = MongoClient(DATABASE_URI)
extrabtn = mongo_client[DATABASE_NAME]
collection = extrabtn[COLLECTION_NAME]

# Function to validate URLs
def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

# Function to handle adding buttons to the MongoDB record
async def buttons_adder(file_id, buttons):
    """
    Add buttons to the MongoDB collection for a specific file.

    Args:
        file_id (str): The unique identifier of the file.
        buttons (list): A list of strings in the format "name:value".

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Generate button fields like B1_name, B1_value, etc.
    button_data = {}
    for idx, button in enumerate(buttons, start=1):
        try:
            name, value = button.split(";", 1)  # Split into name and value
            button_data[f"B{idx}_name"] = name.strip()
            button_data[f"B{idx}_value"] = value.strip()
        except ValueError:
            # Skip invalid button entries
            continue
    
    if not button_data:
        return False  # No valid buttons to add
    
    # Update the MongoDB record
    query = {"_id": file_id}
    update = {"$set": button_data}
    result = extrabtn.buttons.update_one(query, update, upsert=True)
    
    return result.matched_count > 0 or result.upserted_id is not None

# Regular expression for validating a URL
url_pattern = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

@Client.on_message(filters.command(["ab", "addbuttons"]) & filters.reply & filters.user(ADMINS))
async def add_buttons_command(client, message: Message):
    """
    Add buttons to a file in the database.
    Command usage: /ab button_name:button_value,button_name:button_value,...
    """
    # Check if the reply is to a video, document, or audio
    if message.reply_to_message and (message.reply_to_message.video or message.reply_to_message.document or message.reply_to_message.audio):
        # Get the file_id of the replied file
        media_id = (
            message.reply_to_message.video.file_id if message.reply_to_message.video else
            message.reply_to_message.document.file_id if message.reply_to_message.document else
            message.reply_to_message.audio.file_id
        )

        # Unpack file_id (optional depending on your file handling logic)
        file_id, file_ref = unpack_new_file_id(media_id)

        # Extract the command arguments (button_name:button_value pairs separated by commas)
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("Please provide button_name:button_value pairs separated by commas.")
            return

        # Parse buttons from the command arguments
        button_pairs = args[1].split(",")
        
        # Validate URLs
        invalid_buttons = []
        for pair in button_pairs:
            button_name, button_value = pair.split(":", 1)
            if not url_pattern.match(button_value.strip()):
                invalid_buttons.append(pair)

        if invalid_buttons:
            await message.reply(f"The following buttons have invalid URLs: {', '.join(invalid_buttons)}")
            return
        
        try:
            # Call the buttons_adder function
            success = await buttons_adder(file_id, button_pairs)
            if success:
                await message.reply("Buttons successfully added to the file in the database.")
            else:
                await message.reply("Failed to add buttons. Ensure the file exists in the database.")
        except Exception as e:
            await message.reply(f"Error processing buttons: {e}")
    else:
        await message.reply("Reply to a video, document, or audio with this command.")

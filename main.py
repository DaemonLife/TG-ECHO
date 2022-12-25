#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

import telegram
from telegram import Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext
import random
import yaml
import json
import ast
import os
import logging
from groupinfo import GroupInfo

# for audio
import speech_recognition as sr
from lib import get_large_audio_transcription

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_FILENAME = 'data.dat'
START_TEXT = "Hello. This is a beta version"
HELP_TEXT = 'help message'

# for all
whitelist_id = ['', '']   # my dudes

# for messages generator
groups = {}

# for voice to text generator
# creating folders
folder_names = ["audio-chunks", "audio-raw"]
for folder in folder_names:
    if not os.path.isdir(folder):
        os.mkdir(folder)

path = "audio-raw/audio.ogg"
r = sr.Recognizer()

# Standard commands
def start(update: Update, context: CallbackContext):
    if str(update.message.chat_id) in whitelist_id:
        context.bot.send_message(update.message.chat_id, text=START_TEXT, parse_mode=telegram.ParseMode.MARKDOWN)
def help(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat_id, text=HELP_TEXT, parse_mode=telegram.ParseMode.MARKDOWN)

# Case specific command
def generate(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    try:
        sentence = groups[chat_id].sentence()
        if sentence == 'null':
            context.bot.send_message(chat_id, text="_I haven't got enough information to generate a sentence for you yet!_", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            print(sentence)
            # sentence = sentence.decode('unicode-escape')
            context.bot.send_message(chat_id, text=sentence)
    except KeyError:
        context.bot.send_message(chat_id, text="_I don't have any chat information from this group yet!_", parse_mode=telegram.ParseMode.MARKDOWN)

# General message handler
def message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    message = update.message.text
    # Ignore single word replies
    if ' ' in message:
        global groups
        if chat_id not in groups:
            groups[chat_id] = GroupInfo(chat_id)
        # quote and speech marks break Markovify
        message = message.replace("\"", "").replace("\'", "")
        groups[chat_id].add_message(message)

    if random.randint(0,50) == 0:
        generate(update, context)

# General voice to text handler
def get_voice(update: Update, context: CallbackContext) -> None:
    new_file = context.bot.get_file(update.message.voice.file_id)
    new_file.download(path)
    text = str(get_large_audio_transcription(path, r))
    print("Send text message to:", update.message.chat_id)
    context.bot.send_message(str(update.message.chat_id), text)

def main():
    # Load telegram API stuff
    with open('config.yml', 'r') as settings:
        yaml_data = yaml.load(settings, Loader=yaml.Loader)
    token = yaml_data['telegram-apikey']
    updater = Updater(token)

    # Load saved data
    global groups
    if os.path.isfile(DATA_FILENAME):
        try:
            with open(DATA_FILENAME, 'r') as saved:
                data = json.loads(saved.read())
                for chat_id in data:
                    groups[ast.literal_eval(chat_id)] = GroupInfo(chat_id, data[chat_id])
        except ValueError:
            logging.info("No JSON saved data found")

    # Register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(MessageHandler(Filters.voice, get_voice))
    dispatcher.add_handler(CommandHandler("generate", generate))
    dispatcher.add_handler(MessageHandler(Filters.text, message))

    updater.start_polling(timeout=10)
    logging.info("Bot started!")

    # CLI
    while True:
        try:
            text = raw_input()
        except NameError:
            text = input()
    
        if text == 'stop':
            logging.info("Saving all data...")
            save_data = {}
            for chat_id in groups:
                save_data[chat_id] = groups[chat_id].get_data()
    
            with open(DATA_FILENAME, 'w') as save_file:
                json.dump(save_data, save_file)
    
            logging.info("Saved, stopping.")
    
            updater.stop()
            break
    
        elif text == 'numchans':
            logging.info("The bot has data for %d channels" % len(groups))
    
        else:
            logging.info("Unknown command")
    

if __name__ == '__main__':
    main()

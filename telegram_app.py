from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
import logging
import re

from testing import CustomizableTest, db
from settings import get_media_path


def start(update, context):
    db.cursor.execute("SELECT DISTINCT type FROM Questions")
    types = [e[0] for e in db.fetchall()]

    db.cursor.execute("SELECT DISTINCT difficulty FROM Questions WHERE difficulty > 0")
    difficulty = [e[0] for e in db.fetchall()]

    context.user_data['test'] = CustomizableTest(3, type=types, difficulty=difficulty)
    print(context.user_data['test'].question_ids)

    update.message.reply_text('Hi there, this is Emoveo! To answer the questions '
                              'choose either anger, contempt, sadness, surprise, fear or disgust.')

    give_question(update, context)

    return CHECK_ANS


def check_answer(update, context):
    update.message.reply_text('Answer\'s checked')

    give_question(update, context)

    return CHECK_ANS


def give_question(update, context):
    # update.message.reply_text('Here\'s your message')
    quest = context.user_data['test'].question
    context.bot.send_video(update.effective_chat.id, open(get_media_path(quest.media['path']), 'rb'))


def quit_dialog(update, context):
    update.message.reply_text('Bye bye!')


def main():
    updater = Updater(token='1211631725:AAELMhYKQFr0Ughho30o8k_X2FooemTcmOc', use_context=True)
    dp = updater.dispatcher

    con_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHECK_ANS: [MessageHandler(Filters.regex('anger|contempt|sadness|surprise|fear|disgust'), check_answer)]
        },

        fallbacks=[
            MessageHandler(Filters.regex(re.compile('stop|quit', re.IGNORECASE)), quit_dialog),
            CommandHandler('stop', quit_dialog)
        ]
    )

    dp.add_handler(con_handler)

    updater.start_polling()
    updater.idle()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
CHECK_ANS = 1

if __name__ == '__main__':
    main()

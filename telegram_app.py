from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
import logging
import re

from testing import CustomizableTest, db


def start(update, context):
    db.cursor.execute("SELECT DISTINCT type FROM Questions")
    types = [e[0] for e in db.fetchall()]

    db.cursor.execute("SELECT DISTINCT difficulty FROM Questions WHERE difficulty > 0")
    difficulty = [e[0] for e in db.fetchall()]

    test = CustomizableTest(3, type=types, difficulty=difficulty)
    print(test.question_ids)

    update.message.reply_text('Hi there, this is Emoveo! To answer the questions '
                              'choose either anger, contempt, sadness, surprise, fear or disgust.')

    give_question(update, context)

    return CHECK_ANS


def check_answer(update, context):
    update.message.reply_text('Answer\'s checked')

    give_question(update, context)

    return GIVE_QUEST


def give_question(update, context):
    update.message.reply_text('Here\'s your message')


def quit_dial(update, context):
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
            MessageHandler(Filters.regex(re.compile('stop|quit', re.IGNORECASE)), quit_dial),
            CommandHandler('stop', quit_dial)
        ]
    )

    dp.add_handler(con_handler)

    updater.start_polling()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
CHECK_ANS, GIVE_QUEST = range(2)

if __name__ == '__main__':
    main()

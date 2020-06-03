from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
import logging
import re

from testing import CustomizableTest
from settings import get_media_path


def start(update, context):
    context.user_data['num_of_quests'] = 3
    context.user_data['test'] = CustomizableTest(context.user_data['num_of_quests'])

    update.message.reply_text('Hi there, this is Emoveo! I can help you improve your emotional intelligence '
                              'and ability to predict people\'s behavior. Let\'s go!')

    give_question(update, context)

    return CHECK_ANS


def check_answer(update, context):
    test = context.user_data['test']
    quest = test.question

    variant_num = None
    req_text = update.message.text.lower()
    for variant in quest.variants:
        if variant in req_text:
            if variant_num is None:
                variant_num = quest.variants.index(variant)
            else:
                return misunderstanding(update, context, CHECK_ANS)
    if variant_num is None:
        return misunderstanding(update, context, CHECK_ANS)

    if test.answer(variant_num):
        update.message.reply_text('You\'ve got it right! Good for you.')
    else:
        update.message.reply_text('Unfortunately, it\'s not an expression of {}. The right answer is {}.'.format(
            quest.variants[variant_num], quest.variants[quest.correct]
        ))

    test.next()

    if test.completed:
        stats = test.stats['total'], test.stats['correct'], test.stats['incorrect'], test.stats['skipped']
        update.message.reply_text('Here\'s your stats:\n'
                                  'Total: {}\nCorrect: {}\nIncorrect: {}\nSkipped: {}\n'
                                  'Do you want to try again?'.format(*stats))

        return RESTART
    else:
        give_question(update, context)

        return CHECK_ANS


def give_question(update, context):
    quest = context.user_data['test'].question
    update.message.reply_text('Question {}/{}\nTo answer this question choose either {}.'.format(
        context.user_data['test'].stats['total'] + 1, context.user_data['num_of_quests'], ', '.join(quest.variants)))

    context.bot.send_video(update.effective_chat.id, open(get_media_path(quest.media['path']), 'rb'))


def restart(update, context):
    update.message.reply_text('Let\'s begin then!\n')
    context.user_data['test'] = CustomizableTest(context.user_data['num_of_quests'])
    give_question(update, context)

    return CHECK_ANS


def quit_dialog(update, context):
    update.message.reply_text('I hope you had a great time. Bye!')

    return ConversationHandler.END


def misunderstanding(update, context, state):
    update.message.reply_text('Sorry, I don\'t understand you. Could you repeat that in other words?')

    return state


def main():
    updater = Updater(token='1211631725:AAELMhYKQFr0Ughho30o8k_X2FooemTcmOc', use_context=True)
    dp = updater.dispatcher

    con_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHECK_ANS: [
                MessageHandler(FILTERS['all_variants'], check_answer),
                MessageHandler(FILTERS['stopping'], quit_dialog),
                CommandHandler('stop', quit_dialog),
                MessageHandler(Filters.text, lambda update, context: misunderstanding(update, context, CHECK_ANS)),
            ],
            RESTART: [
                MessageHandler(FILTERS['declined_restart'], quit_dialog),
                MessageHandler(FILTERS['agreed_restart'], restart),
                MessageHandler(FILTERS['stopping'], quit_dialog),
                CommandHandler('stop', quit_dialog),
                MessageHandler(Filters.text, lambda update, context: misunderstanding(update, context, RESTART))
            ]
        },

        fallbacks=[
            MessageHandler(FILTERS['stopping'], quit_dialog),
            CommandHandler('stop', quit_dialog)
        ]
    )

    dp.add_handler(con_handler)

    updater.start_polling()
    updater.idle()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
CHECK_ANS, RESTART = range(2)
FILTERS = {
    'all_variants': Filters.regex(re.compile('anger|contempt|sadness|surprise|fear|disgust', re.IGNORECASE)),
    'declined_restart': Filters.regex(re.compile('no', re.IGNORECASE)),
    'agreed_restart': Filters.regex(re.compile('ok|yes|', re.IGNORECASE)),
    'stopping': Filters.regex(re.compile('stop|quit|bye|goodbye', re.IGNORECASE))
}

if __name__ == '__main__':
    main()

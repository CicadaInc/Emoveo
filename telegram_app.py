from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
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

    variant = set(re.findall('|'.join(quest.variants), update.message.text, re.IGNORECASE))
    if len(variant) != 1:
        return misunderstanding(update, context, CHECK_ANS)
    variant_num = quest.variants.index(variant.pop())

    if test.answer(variant_num):
        update.message.reply_text('You\'ve got it right! Good for you.')
    else:
        update.message.reply_text('Unfortunately, it\'s not an expression of {}. The right answer is {}.'.format(
            quest.variants[variant_num], quest.variants[quest.correct]
        ))

    test.next()

    return proceed(update, context)


def skip_question(update, context):
    update.message.reply_text('The question\'s been skipped')
    context.user_data['test'].skip()

    return proceed(update, context)


def give_question(update, context):
    quest = context.user_data['test'].question
    print(quest.id)

    vars_len = len(quest.variants)
    ind = vars_len // 2 + vars_len % 2
    markup = ReplyKeyboardMarkup([quest.variants[:ind], quest.variants[ind:], ['skip']])

    update.message.reply_text('Question {}/{}:\nTo answer this question choose either {}.'.format(
        context.user_data['test'].stats['total'] + 1, context.user_data['num_of_quests'], ', '.join(quest.variants)),
        reply_markup=markup)

    context.bot.send_video(update.effective_chat.id, open(get_media_path(quest.media['path']), 'rb'))


def proceed(update, context):
    test = context.user_data['test']

    if test.completed:
        stats = test.stats['total'], test.stats['correct'], test.stats['incorrect'], test.stats['skipped']
        update.message.reply_text('Here\'s your stats:\n'
                                  'Total: {}\nCorrect: {}\nIncorrect: {}\nSkipped: {}\n'
                                  'Do you want to try again?'.format(*stats),
                                  reply_markup=try_again_markup)

        return RESTART
    else:
        give_question(update, context)

        return CHECK_ANS


def restart(update, context):
    update.message.reply_text('Let\'s begin then!\n')
    context.user_data['test'] = CustomizableTest(context.user_data['num_of_quests'])
    give_question(update, context)

    return CHECK_ANS


def quit_dialog(update, context):
    update.message.reply_text('I hope you had a great time. Bye!', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

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
            # CHOOSE_QUEST_NUM: [
            #     MessageHandler()
            # ],
            CHECK_ANS: [
                MessageHandler(FILTERS['all_variants'], check_answer),
                MessageHandler(FILTERS['skipping'], skip_question),
                MessageHandler(FILTERS['misunderstanding'],
                               lambda update, context: misunderstanding(update, context, CHECK_ANS)),
            ],
            RESTART: [
                MessageHandler(FILTERS['declined_restart'], quit_dialog),
                MessageHandler(FILTERS['agreed_restart'], restart),
                MessageHandler(FILTERS['misunderstanding'],
                               lambda update, context: misunderstanding(update, context, RESTART))
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
CHECK_ANS, RESTART, CHOOSE_QUEST_NUM = range(3)
FILTERS = {
    'all_variants': Filters.regex(re.compile('anger|contempt|sadness|surprise|fear|disgust', re.IGNORECASE)),
    'declined_restart': Filters.regex(re.compile('no', re.IGNORECASE)),
    'agreed_restart': Filters.regex(re.compile('ok|yes', re.IGNORECASE)),
    'skipping': Filters.regex(re.compile('skip|pass', re.IGNORECASE)),
    'stopping': Filters.regex(re.compile('stop|quit|bye|goodbye', re.IGNORECASE)),
    'misunderstanding': Filters.regex(re.compile('^((?!stop|quit|bye|goodbye).)*$', re.IGNORECASE)),
}
try_again_markup = ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)

if __name__ == '__main__':
    main()

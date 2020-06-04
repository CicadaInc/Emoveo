from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import re

from testing import CustomizableTest, db
from settings import get_media_path


def start(update, context):
    update.message.reply_text('Hi there, this is Emoveo! I can help you improve your emotional intelligence '
                              'and ability to predict people\'s behavior.\n'
                              'how many questions would you like to play (from 1 to {})?'.format(MAX_QUEST_NUM),
                              reply_markup=quest_num_markup)

    return CHOOSE_QUEST_NUM


def choose_quest_num(update, context):
    quest_num = set(re.findall(find_template, update.message.text))
    if len(quest_num) > 1:
        return misunderstanding(update, context, CHOOSE_QUEST_NUM)

    context.user_data['num_of_quests'] = int(quest_num.pop())
    context.user_data['test'] = CustomizableTest(context.user_data['num_of_quests'])

    update.message.reply_text('Alright, we\'re gonna start now.')

    give_question(update, context)

    return CHECK_ANS


def check_answer(update, context):
    test = context.user_data['test']
    quest = test.question

    variant = set(re.findall('|'.join(quest.variants), update.message.text.lower()))
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

    if quest.type == 'video':
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
    context.user_data.clear()

    return start(update, context)


def quit_dialog(update, context):
    update.message.reply_text('I hope you had a great time. Bye!', reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

    return ConversationHandler.END


def misunderstanding(update, context, state):
    update.message.reply_text('Sorry, I don\'t understand you. Could you repeat that in other words?')

    return state


def show_help(update, context, state):
    update.message.reply_text('Sorry, hints aren\'t translated in english yet.')

    return state


def main():
    updater = Updater(token='1211631725:AAELMhYKQFr0Ughho30o8k_X2FooemTcmOc', use_context=True)
    dp = updater.dispatcher

    con_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSE_QUEST_NUM: [
                MessageHandler(FILTERS['quest_num_choice'], choose_quest_num),
                MessageHandler(FILTERS['help'], lambda update, context: show_help(update, context, CHOOSE_QUEST_NUM)),
                CommandHandler('help', lambda update, context: show_help(update, context, CHOOSE_QUEST_NUM)),
                MessageHandler(FILTERS['misunderstanding'],
                               lambda update, context: misunderstanding(update, context, CHOOSE_QUEST_NUM))
            ],
            CHECK_ANS: [
                MessageHandler(FILTERS['all_variants'], check_answer),
                MessageHandler(FILTERS['skipping'], skip_question),
                MessageHandler(FILTERS['help'], lambda update, context: show_help(update, context, CHECK_ANS)),
                CommandHandler('help', lambda update, context: show_help(update, context, CHECK_ANS)),
                MessageHandler(FILTERS['misunderstanding'],
                               lambda update, context: misunderstanding(update, context, CHECK_ANS))
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

# Amount of questions in the db must be a double figure
db.cursor.execute('SELECT COUNT(*) FROM Questions')
MAX_QUEST_NUM = db.fetchone()[0]
find_template = '[1-{}][0-{}]|[1-{}]'.format(
    str(MAX_QUEST_NUM)[0], str(MAX_QUEST_NUM)[1], str(min(9, MAX_QUEST_NUM)))
filter_template = r'^\D*[1-{}]\D*$|^\D*[1-{}][0-{}]\D*$'.format(
    str(min(9, MAX_QUEST_NUM)), str(MAX_QUEST_NUM)[0], str(MAX_QUEST_NUM)[1])

CHECK_ANS, RESTART, CHOOSE_QUEST_NUM = range(3)
FILTERS = {
    'all_variants': Filters.regex(re.compile('anger|contempt|sadness|surprise|fear|disgust', re.IGNORECASE)),
    'declined_restart': Filters.regex(re.compile(r'\bno\b', re.IGNORECASE)),
    'agreed_restart': Filters.regex(re.compile('ok|yes', re.IGNORECASE)),
    'quest_num_choice': Filters.regex(filter_template),
    'skipping': Filters.regex(re.compile('skip|pass', re.IGNORECASE)),
    'stopping': Filters.regex(re.compile('stop|quit|bye|goodbye', re.IGNORECASE)),
    'misunderstanding': Filters.regex(re.compile('^((?!stop|quit|bye).)*$', re.IGNORECASE)),
    'help': Filters.regex(re.compile('help|hint', re.IGNORECASE))
}

try_again_markup = ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
quest_num_markup = ReplyKeyboardMarkup([['3', '4'], ['5', '6']], one_time_keyboard=True)

if __name__ == '__main__':
    main()

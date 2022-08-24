from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup
import config
from db import *

bot = Bot(token=config.token)
dp = Dispatcher(bot)


def qiwi(number, comment, currency=643):
    link = 'https://qiwi.com/payment/form/99?'
    data = {
        'currency': currency,
        'extra[\'account\']': number,
        'extra[\'comment\']': comment,
        'blocked[1]': 'comment',
        'blocked[2]': 'account'
    }
    for key, value in data.items():
        link += f'{key}={value}&'
    return link


class CategoriesMarkup(InlineKeyboardMarkup):
    def __init__(self):
        buttons = []
        for category in Category.select():
            buttons.append([InlineKeyboardButton(text=f'💭{category.name}: {category.comment}', callback_data=f'category {category.id}')])
        self.inline_keyboard = buttons


class ProductsMarkup(InlineKeyboardMarkup):
    def __init__(self, id, is_promo):
        buttons = []
        for product in Product.select().where(Product.category_id == id):
            buttons.append([InlineKeyboardButton(text=f'🔺{product.name}: {int(product.price - product.price * config.discount * is_promo)}₽', callback_data=f'buy')])
        buttons.append([InlineKeyboardButton(text=f'Назад', callback_data='back')])
        self.inline_keyboard = buttons


class ProfileMarkup(InlineKeyboardMarkup):
    def __init__(self, id):
        pay_url = qiwi(config.qiwi, id)
        buttons = [
            [InlineKeyboardButton(text=config.buttons['pay'], url=pay_url)],
            [InlineKeyboardButton(text=config.buttons['check'], callback_data='check')]
        ]
        self.inline_keyboard = buttons


class MenuMarkup(ReplyKeyboardMarkup):
    def __init__(self):
        self.keyboard = [
            [config.buttons['categories'], config.buttons['about']],
            [config.buttons['profile']],
            [config.buttons['promo'], config.buttons['terms']]
        ]
        self.one_time_keyboard = False
        self.resize_keyboard = True


# Message handlers


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    _ = User.get_or_create(id=message.from_user.id, defaults={'username': message.from_user.username, 'is_promo': False})
    await message.reply(config.messages['welcome'](message.from_user.first_name), reply_markup=menu_markup, parse_mode='HTML')


@dp.message_handler(commands=['categories'])
@dp.message_handler(regexp=config.buttons['categories'])
async def categories(message: types.Message):
    await message.answer('Выберите категорию', reply_markup=categories_markup)


@dp.message_handler(commands=['about'])
@dp.message_handler(regexp=config.buttons['about'])
async def about(message: types.Message):
    await message.answer(config.messages['about'])


@dp.message_handler(commands=['promo'])
@dp.message_handler(regexp=config.buttons['promo'])
async def promo(message: types.Message):
    match message.get_args():
        case config.promocode:
            user = User.get(User.id == message.from_user.id)
            user.is_promo = True
            user.save()
            await message.answer(config.messages['on_promo_activate'])
        case None:
            await message.answer(config.messages['activate_promo'])
        case _:
            await message.answer(config.messages['wrong_promo'])


@dp.message_handler(commands=['profile'])
@dp.message_handler(regexp=config.buttons['profile'])
async def profile(message: types.Message):
    user = User.get(User.id == message.from_user.id)
    await message.answer(config.messages['attention'])
    await message.answer(config.messages['profile'](user.id, user.username, user.is_promo), reply_markup=ProfileMarkup(user.id))

# Callback handler


@dp.callback_query_handler()
async def callback(call: types.CallbackQuery):
    match call.data.split():
        case 'category', id:
            user = User.get(User.id == call.from_user.id)
            await call.message.edit_text(text='Выберите товар', reply_markup=ProductsMarkup(id, user.is_promo))
        case 'buy', :
            await call.answer(config.messages['dont_enough_money'], show_alert=True)
        case 'check', :
            await call.answer(config.messages['payment_dont_accepted'], show_alert=True)
        case 'back', :
            await call.message.edit_text('Выберите категорию', reply_markup=categories_markup)
    await call.answer('Успешно!', show_alert=False)


if __name__ == '__main__':
    menu_markup = MenuMarkup()
    categories_markup = CategoriesMarkup()
    executor.start_polling(dp, skip_updates=True)

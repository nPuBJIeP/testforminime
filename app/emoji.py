import re

emoji = {
    'hamburger': "\U0001F354",
    'fries': "\U0001F35F",
    'curry': "\U0001F35B",
    'poultry_leg': "\U0001F357",
    'lollipop': "\U0001F36D",
    'coffee': "\u2615\uFE0F",
    'egg': "\U0001F373",
    'burrito': "\U0001F32F",
    'oncoming_taxi': "\U0001F696",
    'inbox_tray': "\U0001F4E5",
    'arrow_left': "\u2B05",
    'arrow_right': "\u27A1",
    'arrow_double_down': "\u23EC",
    'arrows_counterclockwise': "\U0001F504",
    'round_pushpin': "\U0001F4CD",
    'star': "\u2B50\uFE0F",
    'iphone': "\U0001F4F1",
    'x': "\u274C",
    'white_check_mark': "\u2705",
    'snowflake': "\u2744\uFE0F",
    'tv': "\U0001F4FA",
    'radio': "\U0001F4FB",
    'new': "\U0001F308",
    'pizza': "\U0001F355",
    'bento': "\U0001F371",
    'sushi': "\U0001F363",
    'fried_shrimp': "\U0001F364",
    'runner': "\U0001F3C3",
    'rice': "\U0001F35A",
    'cake': "\U0001F370",
    'bread': "\U0001F35E",
    'oden': "\U0001F362",
    'stew': "\U0001F372",
    'fork_and_knife': "\U0001F374",
    'japan': "\U0001F1EF\U0001F1F5",
    'fire': "\U0001F525",
    'ramen': "\U0001F35C",
    'pointer': "\u27A1\uFE0F",
    'tropical_drink': "\U000FE988",
    'dollar': "\U0001F4B5",
    'credit_card': "\U0001F4B3",
    'building': '🏢',
    'news': '📢'
}

pattern = ('['
           '\U00002B05-\U00002B07'
           '\U00002300-\U000023F3'
           '\U00002600-\U000027BF'
           '\U0000FE00-\U0000FEFF'
           '\U0001F300-\U0001F64F'
           '\U0001F1EF\U0001F1F5'
           '\U0001F680-\U0001F6FF'
           '\u2B50\uFE0F'
           ']+')

emoji_pattern = re.compile(pattern, re.UNICODE)


def remove_emoji(string):
    return emoji_pattern.sub('', string) if string else string


def clean_up(string):
    return remove_emoji(string).strip() if string else string

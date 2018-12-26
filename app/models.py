from datetime import datetime

from .database import db


class Branch(db.Model):
    __tablename__ = 'branches'
    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    image = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.Text, nullable=True)
    location_id = db.Column(
        db.Integer, db.ForeignKey('locations.id_'), nullable=True)
    location = db.relationship('Location')

    def __init__(self,
                 address,
                 phone_number=None,
                 image=None,
                 description=None,
                 location=None):
        self.address = address
        self.image = image
        self.description = description
        self.location = location
        self.phone_number = phone_number

    def __repr__(self):
        return "<Branch(id_={0}, address='{1}', description='{2}', location_id='{3}', photo='{4}')>".format(
            self.id_, self.address, self.description, self.location_id,
            self.photo)

    def __str__(self):
        string = '\n<b>Адрес</b>: {}'.format(self.address)

        if self.phone_number:
            string += '\n<b>Телефон</b>: {}'.format(self.phone_number)
        if self.description:
            string += '\n\n{}'.format(self.description)
        return string


class Location(db.Model):
    __tablename__ = 'locations'
    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    latitude = db.Column(db.DECIMAL, nullable=False)
    longitude = db.Column(db.DECIMAL, nullable=False)

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


class Manager(db.Model):
    __tablename__ = 'managers'
    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, unique=True, nullable=False)

    def __init__(self, user_id):
        self.user_id = user_id


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    text = db.Column(db.Text, nullable=True)
    photo = db.Column(db.Text)

    def __init__(self, text, photo):
        self.text = text
        self.photo = photo


class Anonymous(db.Model):
    __tablename__ = 'anonymous_users'
    chat_id = db.Column(db.Text, primary_key=True, nullable=False)

    def __init__(self, chat_id):
        self.chat_id = chat_id


class SyncTime(db.Model):
    __tablename__ = 'sync_times'

    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __str__(self):
        return '<b>Дата последней синхронизации</b>: {}\n'.format(
            self.date.strftime('%d-%m-%y %H:%M'))


class User(db.Model):
    __tablename__ = 'users'
    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    barcode = db.Column(db.Text, unique=True, nullable=True)
    name = db.Column(db.Text, nullable=False)
    balance = db.Column(db.Text, nullable=True, default='0')
    discount = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.Text, nullable=True)  # should really be unique

    def __init__(self, name, phone_number, barcode, balance, discount):
        self.phone_number = phone_number
        self.barcode = barcode
        self.name = name
        self.balance = balance
        self.discount = discount

    def __repr__(self):
        return "<User(id_={0}, user_id='{1}', barcode='{2}' phone_number='{3}' discount='{4}')>".format(
            self.id_, self.user_id, self.barcode, self.phone_number,
            self.discount)

    def __str__(self):
        string = '<b>Ваш баланс</b>: {} сум\n'.format(self.balance)
        string += '<b>Процент скидки</b>: {}%\n'.format(self.discount)
        return string


class Feedback(db.Model):
    __tablename__ = 'feedback_messages'

    id_ = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=True)
    nickname = db.Column(db.String, nullable=True)
    text = db.Column(db.Text, nullable=False)

    def __init__(self, user_id, first_name, text, last_name=None, nickname=None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.nickname = nickname
        self.text = text


    def __str__(self):
        string = '<a href="tg://user?id={}">{}</a>\n'.format(
            self.user_id, self.first_name)
        string += '<b>Отзыв:</b>\n'
        string += self.text
        return string

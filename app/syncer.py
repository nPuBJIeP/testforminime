import os
import errno
import threading
import time
import csv
import schedule

from datetime import datetime
from pytz import utc, timezone

from .database import db
from .models import User, SyncTime

tashkent = timezone('Asia/Tashkent')


class Syncer:
    def __init__(self, app, path, cache_path):
        """
        :param app
        :param path
        :param cache_path
        """

        self.app = app
        self.path = path  # anticipated to sync csv data
        self.cache_path = cache_path  # previously sync'ed csv data

    @staticmethod
    def _conv(v):
        try:
            return str(int(v))
        except:
            return '"{}"'.format(v)

    def _stringify(self, file):
        with open(file, 'r') as content:
            return sorted(
                csv.reader(content, delimiter=';'),
                key=lambda row: row[5],
            )

    def __sync(self):
        print('{}: syncing...'.format(tashkent.localize(datetime.utcnow())))

        app = self.app
        cur = self._stringify(self.cache_path)
        est = self._stringify(self.path)
        flag = False

        with app.app_context():
            syncTime = SyncTime.query.first()
            if syncTime is None:
                syncTime = SyncTime()
                db.session.add(syncTime)
            syncTime.date = tashkent.localize(datetime.utcnow())

            if len(est) >= len(cur):
                flag = True
                for row in est:
                    try:
                        if row[5] == "":
                            continue

                        user = User.query.filter_by(barcode=row[5]).first()
                        if row[2] == "":
                            phone_number = None
                        else:
                            phone_number = row[2]
                            if phone_number[0] == '+':
                                phone_number = phone_number.replace('+', '')

                        if user is None:
                            if phone_number:
                                check_user = User.query.filter_by(
                                    phone_number=phone_number).first()
                                if check_user:
                                    print(
                                        'possible phone number collision detected {}',
                                        phone_number)

                            db.session.add(
                                User(
                                    name=row[0],
                                    phone_number=phone_number,
                                    discount=row[3],
                                    barcode=row[5],
                                    balance=int(round(float(row[13].replace(',', '.'))))))
                        else:
                            if phone_number:
                                check_user = User.query.filter_by(
                                    phone_number=phone_number).first()
                                if check_user and check_user.barcode != user.barcode:
                                    print(
                                        'possible phone number collision detected, {}',
                                        phone_number)

                            if user.phone_number != phone_number:
                                user.user_id = None

                            user.name = row[0]
                            user.phone_number = phone_number
                            user.discount = row[3]
                            user.barcode = row[5]
                            user.balance = int(round(float(row[13].replace(',', '.'))))
                    except:
                        pass

            db.session.commit()

            if flag:
                with open(self.path, 'r') as input, open(self.cache_path,
                                                         'w') as output:
                    output.write(input.read())

    def _sync(self):
        try:
            self.__sync()
        except:
            try:
                os.remove(self.cache_path)
                with open(self.cache_path, 'w'):
                    pass
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            self.__sync()

    def sync(self):
        thread = threading.Thread(target=self._sync)
        thread.start()

    def _schedule(self, interval):
        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while True:
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()

    def schedule(self):
        schedule.every(5).minutes.do(self.sync)
        self._schedule(150)

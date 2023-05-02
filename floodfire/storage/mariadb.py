#!/usr/bin/env python3

import pprint

import MySQLdb


class FloodfireStorage:
    def __init__(self, config):
        try:
            self.conn = MySQLdb.connect(
                host=config["RDB"]["DB_HOST"],
                port=int(config["RDB"]["DB_PORT"]),
                user=config["RDB"]["DB_USER"],
                passwd=config["RDB"]["DB_PASSWORD"],
                db=config["RDB"]["DB_DATABASE"],
                charset="utf8mb4",
            )
            self.cur = self.conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        except MySQLdb._exceptions.OperationalError:
            print("Database connection fail!")

        self.pp = pprint.PrettyPrinter(indent=2)

    def get_ct_singleday_posts(self, project_id: int, data_time: str):
        try:
            sql = "SELECT `message`, `description` FROM `p{}_posts` \
                WHERE (`message` IS NOT NULL OR `description` IS NOT NULL) \
                AND date(CONVERT_TZ(`date`,'+00:00','+08:00')) BETWEEN '{} 00:00:00' AND '{} 23:59:59'".format(
                project_id, data_time, data_time
            )
            self.cur.execute(sql)
            data = self.cur.fetchall()
        except MySQLdb._exceptions.OperationalError as e:
            print("Error! Insert weatherbox error!")
            print(e.args[0], e.args[1])
            return False
        except Exception as err:
            print("Error! Insert weatherbox error! {}".format(err))
            return False
        return data

    def get_ct_period_posts(
        self, project_id: int, start_date: str, end_date: str
    ):
        try:
            sql = "SELECT `message`, `description` FROM `p{}_posts` \
                WHERE (`message` IS NOT NULL OR `description` IS NOT NULL) \
                AND date(CONVERT_TZ(`date`,'+00:00','+08:00')) BETWEEN '{} 00:00:00' AND '{} 23:59:59'".format(
                project_id, start_date, end_date
            )
            self.cur.execute(sql)
            data = self.cur.fetchall()
        except MySQLdb._exceptions.OperationalError as e:
            print("Error! Insert weatherbox error!")
            print(e.args[0], e.args[1])
            return False
        except Exception as err:
            print("Error! Insert weatherbox error! {}".format(err))
            return False
        return data

    def __del__(self):
        self.cur.close()
        self.conn.close()

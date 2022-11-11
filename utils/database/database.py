import sqlite3

class Database(object):
    def __init__(self, db_name='database.db') -> None:
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def __user_table(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS user (
            username TEXT PRIMARY KEY,
            password TEXT,
            first_name TEXT,
            middle_initial TEXT,
            last_name TEXT
        )""")
        self.connection.commit()

    def __chats_table(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT
        )""")
        self.connection.commit()

    def __status_table(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            is_online INTEGER,
            new_message INTEGER
        )""")
        self.connection.commit()

    def create_table(self):
        self.__user_table()
        self.__chats_table()
        self.__status_table()

    def __dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_all(self, table): 
        self.cursor.execute("SELECT * FROM {}".format(table))
        self.cursor.row_factory = self.__dict_factory
        result = self.cursor.fetchall()
        self.connection.commit() 
        return result

    def get_by_key(self, table, key):
        self.cursor.execute("SELECT * FROM {} WHERE {}=?".format(table), ('{}'.format(key),))
        self.cursor.row_factory = self.__dict_factory
        result = self.cursor.fetchall()
        self.connection.commit() 
        return result

    def insert(self, table, columns, data):
        if table == 'user':
            self.cursor.execute("SELECT EXISTS (SELECT 1 FROM user where username = :username)", data)
            result = self.cursor.fetchone()
            if result[0]:
                return

        print("INSERT INTO {} VALUES ({})".format(table, columns),)
        self.cursor.execute("INSERT into {} VALUES ({})".format(table, columns), data)
        self.connection.commit()

    def update(self, table, set, value, key, data):
        self.cursor.execute("UPDATE {} SET {} = :{} where {} = :{}".format(table, set, value, key, key), data)
        self.connection.commit()

    def remove(self, table, key, data):
        self.cursor.execute("DELETE FROM {} WHERE key = :{}".format(table, key), data)
        self.connection.commit()

    def close(self):
        self.connection.close()
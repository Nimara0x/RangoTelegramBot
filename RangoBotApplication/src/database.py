import sqlite3
from sqlite3 import Error
from utils import Singleton


class RangoBotDatabase(Singleton):
    def __init__(self):
        super().__init__()
        self.db_file = "rango.db"
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            print(e)
        return conn

    def create_table(self):
        try:
            sql_create_wallet_address_table = """CREATE TABLE IF NOT EXISTS user_wallets (
                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    user_id TEXT NOT NULL,
                                                    blockchain TEXT NOT NULL,
                                                    wallet_address TEXT NOT NULL,
                                                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                                                );"""
            cursor = self.conn.cursor()
            cursor.execute(sql_create_wallet_address_table)
        except Error as e:
            print(e)

    def insert_wallet_address(self, user_id, blockchain, wallet_address):
        try:
            self.conn.execute('''INSERT OR IGNORE INTO user_wallets(user_id, blockchain, wallet_address)
                                          VALUES(?, ?, ?)''', (user_id, blockchain, wallet_address))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print("Address already exists in the database.")

    def get_all_wallets(self):
        self.cursor.execute("SELECT * FROM user_wallets")
        return self.cursor.fetchall()

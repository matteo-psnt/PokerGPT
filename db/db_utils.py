import mysql.connector
from config.config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

class DatabaseManager:
    def __init__(self, discord_id, username, host_id, server_name):
        self.discord_id = discord_id
        self.username = username
        self.host_id = host_id
        self.server_name = server_name
        self.cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        self.cursor = self.cnx.cursor()
        self.check_for_user()
        self.check_for_server()
        self.check_for_server_user()
        self.update_nickname()
    
    def __enter__(self):
        return self
    
    def check_for_user(self):
        check_user_stmt = (
            "SELECT discord_id FROM users "
            "WHERE discord_id = %s"
        )
        self.cursor.execute(check_user_stmt, (self.discord_id,))
        result = self.cursor.fetchone()
        if result is None:
            add_user_stmt = (
                "INSERT INTO users (discord_id, username) "
                "VALUES (%s, %s)"
            )
            data = (self.discord_id, self.username)
            self.cursor.execute(add_user_stmt, data)
            self.cnx.commit()

    def check_for_server(self):
        check_server_stmt = (
            "SELECT host_id FROM servers "
            "WHERE host_id = %s"
        )
        self.cursor.execute(check_server_stmt, (self.host_id,))
        result = self.cursor.fetchone()
        if result is None:
            add_server_stmt = (
                "INSERT INTO servers (host_id, server_name) "
                "VALUES (%s, %s)"
            )
            data = (self.host_id, self.server_name)
            self.cursor.execute(add_server_stmt, data)
            self.cnx.commit()
    
    def check_for_server_user(self):
        get_server_id_stmt = (
            "SELECT id FROM servers "
            "WHERE host_id = %s"
        )
        self.cursor.execute(get_server_id_stmt, (self.host_id,))
        self.server_id = self.cursor.fetchone()[0]

        get_user_id_stmt = (
            "SELECT id FROM users "
            "WHERE discord_id = %s"
        )
        self.cursor.execute(get_user_id_stmt, (self.discord_id,))
        self.user_id = self.cursor.fetchone()[0]

        check_server_user_stmt = (
            "SELECT server_id, user_id FROM server_users "
            "WHERE server_id = %s AND user_id = %s"
        )
        data = (self.server_id, self.user_id)
        self.cursor.execute(check_server_user_stmt, data)
        result = self.cursor.fetchone()

        if result is None:
            add_user_server_stmt = (
                "INSERT INTO server_users (server_id, user_id) "
                "VALUES (%s, %s)"
            )
            data = (self.server_id, self.user_id)
            self.cursor.execute(add_user_server_stmt, data)
            self.cnx.commit()
    
    def update_nickname(self):
        update_stmt = (
            "UPDATE users SET username = %s "
            "WHERE id = %s"
        )
        data = (self.username, self.user_id)
        self.cursor.execute(update_stmt, data)
        self.cnx.commit()

    def update_net_wins(self, net_wins):
        update_stmt = (
            "UPDATE users SET net_wins = %s "
            "WHERE id = %s"
        )
        data = (net_wins, self.user_id)
        self.cursor.execute(update_stmt, data)
        self.cnx.commit()
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.cnx.close()

if __name__ == "__main__":
    with DatabaseManager(1, "matteo", 1, "fake_server") as db:
        db.update_net_wins(100)
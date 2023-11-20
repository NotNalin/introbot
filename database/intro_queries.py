from uuid import uuid4
from datetime import datetime

class IntroQueries:

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def format_time(self,date_time):
        formated_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
        return datetime.strptime(formated_time, "%Y-%m-%d %H:%M:%S")

    def get_current_utc_time(self):
        return self.format_time(datetime.utcnow())

    def is_intro_done(self, discord_id: int) -> bool:
        query = """
            SELECT TRUE FROM karma_activity_log WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id) 
            AND task_id = (SELECT id FROM task_list WHERE hashtag = :hashtag) AND appraiser_approved = 1;
        """
        params = {
            'discord_id': str(discord_id),
            'hashtag': '#ge-intro-to-discord'
        }
        return self.db_connection.fetch_single_data(query, params)

    def is_intro_started(self, discord_id: int) -> bool:
        query = """
            SELECT TRUE FROM intro_task_log WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id);
        """
        params = {
            'discord_id': str(discord_id)
        }
        return self.db_connection.fetch_single_data(query, params)

    def insert_user(self, discord_id: int, channel_id: int) -> None:
        query = """
            INSERT INTO intro_task_log (id, user_id, progress, channel_id, updated_by, updated_at, created_by, created_at) 
            VALUES (:id,(SELECT id FROM user WHERE discord_id = :discord_id), :progress, :channel_id, (SELECT id FROM user WHERE discord_id = :discord_id),
            :updated_at, (SELECT id FROM user WHERE discord_id = :discord_id), :created_at);
        """
        params = {
            'id': str(uuid4()),
            'discord_id': str(discord_id),
            'channel_id': str(channel_id),
            'progress': 1,
            'updated_at': self.get_current_utc_time(),
            'created_at': self.get_current_utc_time()
        }
        self.db_connection.execute(query, params)

    def fetch_user_id_from_discord_id(self, discord_id):
        query = """
            SELECT id FROM user WHERE discord_id = :discord_id;
        """
        params = {
            'discord_id': str(discord_id)
        }
        return self.db_connection.fetch_single_data(query, params)

    def is_valid_channel(self, channel_id, discord_id):
        query = """
            SELECT channel_id
            FROM intro_task_log
            WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id);
        """
        params = {
            'discord_id': str(discord_id)
        }
        return str(channel_id) == self.db_connection.fetch_single_data(query, params)

    def check_step_order(self, discord_id):
        query = """
            SELECT progress
            FROM intro_task_log
            WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id);
        """
        params = {
            'discord_id': str(discord_id)
        }
        return self.db_connection.fetch_single_data(query, params)

    def fetch_task_message_id(self, discord_id) -> int:
        query = """
            SELECT task_message_id 
            FROM karma_activity_log 
            WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id) 
            AND task_id = (SELECT id FROM task_list WHERE hashtag = :hashtag)
            AND peer_approved = TRUE;
        """
        params = {
            'discord_id': str(discord_id),
            'hashtag': '#my-muid'
        }
        return self.db_connection.fetch_single_data(query, params)

    def check_muid(self, discord_id: int,muid) -> bool:
        query = """
            SELECT TRUE FROM user WHERE discord_id = :discord_id AND muid = :muid;
        """
        params = {
            'discord_id': str(discord_id),
            'muid': str(muid)
        }
        return self.db_connection.fetch_single_data(query, params)

    def update_progress(self,user_id: int, progress: int) -> None:
        query = """
            UPDATE intro_task_log 
            SET progress = :progress, updated_by = (SELECT id FROM user WHERE discord_id = :discord_id), updated_at = :updated_at
            WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id);
        """
        params = {
            'discord_id': str(user_id),
            'progress': progress,
            'updated_at': self.get_current_utc_time()
        }
        self.db_connection.execute(query, params)

    def delete_log(self, discord_id: int) -> None:
        query = """
            DELETE FROM intro_task_log WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id);
        """
        params = {
            'discord_id': str(discord_id)
        }
        self.db_connection.execute(query, params)

    def is_muidtask_done(self, discord_id):
        query = """
            SELECT TRUE 
            FROM karma_activity_log 
            WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id) and task_id = (SELECT id FROM task_list WHERE hashtag = :hashtag) and appraiser_approved = TRUE;
        """
        params = {
            'discord_id': str(discord_id),
            'hashtag': '#my-muid'
        }
        return self.db_connection.fetch_single_data(query, params)

    def fetch_lobby_message_id(self, discord_id):
        query = """
            SELECT lobby_message_id 
            FROM karma_activity_log 
            WHERE user_id = (SELECT id FROM user WHERE discord_id = :discord_id) 
            AND task_id = (SELECT id FROM task_list WHERE hashtag = :hashtag)
            AND peer_approved = TRUE;
        """
        params = {
            'discord_id': str(discord_id),
            'hashtag': '#my-muid'
        }
        return self.db_connection.fetch_single_data(query, params)
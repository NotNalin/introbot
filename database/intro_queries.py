class IntroQueries:

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def fetch_user_id_from_discord_id(self, discord_id):
        query = """
            SELECT id FROM user WHERE discord_id = :discord_id;
        """
        params = {
            'discord_id': str(discord_id)
        }
        return self.db_connection.fetch_single_data(query, params)

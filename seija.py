#!/usr/bin/env python3

import os
from discord.ext import commands

from modules import db

from modules.connections import database_file as database_file
from modules.connections import bot_token as bot_token

command_prefix = "\'"

if not os.path.exists(database_file):
    db.query("CREATE TABLE users "
             "(user_id, osu_id, osu_username, osu_join_date, pp, country, ranked_maps_amount, no_sync)")
    db.query("CREATE TABLE user_event_history (osu_id, event_id, channel_id, timestamp)")
    db.query("CREATE TABLE config (setting, parent, value, flag)")

    db.query("CREATE TABLE channels (setting, guild_id, channel_id)")
    db.query("CREATE TABLE categories (setting, guild_id, category_id)")
    db.query("CREATE TABLE roles (setting, guild_id, role_id)")

    db.query("CREATE TABLE admins (user_id, permissions)")
    db.query("CREATE TABLE mod_posts (post_id, mapset_id, channel_id)")
    db.query("CREATE TABLE mapset_events (event_id, mapset_id, channel_id)")
    db.query("CREATE TABLE mod_tracking (mapset_id, channel_id, mode)")
    db.query("CREATE TABLE mod_tracking_pauselist (mapset_id, channel_id, mode)")
    db.query("CREATE TABLE mapset_notification_status (mapset_id, map_id, channel_id, status)")
    db.query("CREATE TABLE map_owners (map_id, user_id)")
    db.query("CREATE TABLE notices (timestamp, notice)")
    db.query("CREATE TABLE restricted_users (guild_id, osu_id)")
    db.query("CREATE TABLE queues (channel_id, user_id, guild_id)")
    db.query("CREATE TABLE mapset_channels (channel_id, role_id, user_id, mapset_id, guild_id)")
    db.query("CREATE TABLE name_backups (id, name)")
    db.query("CREATE TABLE member_goodbye_messages (message)")
    db.query(["INSERT INTO member_goodbye_messages VALUES (?)", ["%s is going for loved"]])
    db.query(["INSERT INTO member_goodbye_messages VALUES (?)", ["%s was told to remap one too many times"]])

initial_extensions = [
    "cogs.BotManagement",
    "cogs.Docs",
    "cogs.MapsetChannel",
    "cogs.MemberManagement",
    "cogs.MemberNameSyncing",
    "cogs.MemberStatistics",
    "cogs.MemberVerification",
    "cogs.ModChecker",
    "cogs.Osu",
    "cogs.Queue",
]


class Seija(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_tasks = []
        self.app_version = (open(".version", "r+").read()).rstrip()
        self.description = f"Seija {self.app_version}"

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(e)

    async def close(self):
        # Cancel all Task object generated by cogs.
        # This prevents any task still running due to having long sleep time.
        for task in self.background_tasks:
            task.cancel()
        
        # Run actual discord.py close.
        await super().close()

    async def on_ready(self):
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("------")
        if not db.query("SELECT * FROM admins"):
            app_info = await self.application_info()
            db.query(["INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"]])
            print(f"Added {app_info.owner.name} to admin list")


client = Seija(command_prefix=command_prefix)
client.run(bot_token)

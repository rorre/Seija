import discord
import os
from discord.ext import commands
from modules import permissions
from modules import wrappers
from modules.connections import database_file as database_file


class BotManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="admin_list", brief="Show bot admin list", description="")
    @commands.check(permissions.is_not_ignored)
    async def admin_list(self, ctx):
        await ctx.send(embed=permissions.get_admin_list())

    @commands.command(name="make_admin", brief="Add a user to bot admin list", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def make_admin(self, ctx, user_id: str, perms=str("0")):
        await self.bot.db.execute("INSERT INTO admins VALUES (?, ?)", [str(user_id), str(perms)])
        await self.bot.db.commit()
        await ctx.send(":ok_hand:")

    @commands.command(name="ignored_users", brief="If you only see this command, you are blacklisted")
    async def ignored_users(self, ctx):
        """
        If this is the only command you see, you are blacklisted from using the bot.
        """
        async with self.bot.db.execute("SELECT * FROM ignored_users") as cursor:
            db_ignored_users = await cursor.fetchall()

        buffer = ":hammer: **Users who are blacklisted from using the bot.**\n\n"
        for one_ignored_user in db_ignored_users:
            buffer += f"<@{one_ignored_user[0]}> | reason: {one_ignored_user[1]}\n"
        embed = discord.Embed(color=0xf76a8c)
        embed.set_footer(text="If a BN has rights to deny service to an individual, so do I.")
        await wrappers.send_large_embed(ctx.channel, embed, buffer)

    @commands.command(name="ignore_user", brief="Blacklist a user from using the bot", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def ignore_user(self, ctx, user_id, *, reason=""):
        await self.bot.db.execute("INSERT INTO ignored_users VALUES (?, ?)", [str(user_id), str(reason)])
        await self.bot.db.commit()
        await ctx.send(":ok_hand:")

    @commands.command(name="restart", brief="Restart the bot", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def restart(self, ctx):
        await ctx.send("Restarting")
        await self.bot.close()
        quit()

    @commands.command(name="update", brief="Update the bot", description="it just does git pull")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def update(self, ctx):
        await ctx.send("Updating.")
        os.system("git pull")
        await self.bot.close()
        quit()

    @commands.command(name="sql", brief="Execute an SQL query", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def sql(self, ctx, *, query):
        if len(query) > 0:
            try:
                async with await self.bot.db.execute(query) as cursor:
                    response = await cursor.fetchall()
                await self.bot.db.commit()
                if not response:
                    embed = discord.Embed(description="query executed successfully", color=0xadff2f)
                    await ctx.send(embed=embed)
                else:
                    buffer = ""
                    for entry in response:
                        buffer += f"{str(entry)}\n"

                    embed = discord.Embed(color=0xadff2f)
                    embed.set_author(name="query results")
                    await wrappers.send_large_embed(ctx.channel, embed, buffer)
            except Exception as e:
                embed = discord.Embed(description=e, color=0xbd3661)
                embed.set_author(name="error occurred while executing the query")
                await ctx.send(embed=embed)

    @commands.command(name="leave_guild", brief="Leave the current guild", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    @commands.guild_only()
    async def leave_guild(self, ctx):
        await ctx.guild.leave()

    @commands.command(name="echo", brief="Echo a string", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def echo(self, ctx, *, string):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(string)

    @commands.command(name="set_activity", brief="Set an activity", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def set_activity(self, ctx, *, string):
        activity = discord.Game(string)
        await self.bot.change_presence(activity=activity)
        await ctx.send(":ok_hand:")

    @commands.command(name="config", brief="Insert a config in db", description="")
    @commands.check(permissions.is_owner)
    @commands.check(permissions.is_not_ignored)
    async def config(self, ctx, setting, parent, value, flag="0"):
        await self.bot.db.execute("INSERT INTO config VALUES (?, ?, ?, ?)",
                                  [str(setting), str(parent), str(value), str(flag)])
        await self.bot.db.commit()
        await ctx.send(":ok_hand:")

    @commands.command(name="db_dump", brief="Perform a database dump", description="")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    @commands.guild_only()
    async def db_dump(self, ctx):
        async with self.bot.db.execute("SELECT * FROM config WHERE setting = ? and value = ?",
                                     ["db_dump_channel", str(ctx.channel.id)]) as cursor:
            db_dump_channel = await cursor.fetchall()
        if db_dump_channel:
            await ctx.send(file=discord.File(database_file))


def setup(bot):
    bot.add_cog(BotManagement(bot))

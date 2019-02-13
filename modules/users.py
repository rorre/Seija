from modules import osuapi
from modules import osuembed
from modules import dbhandler
from modules import utils
import discord
import time
import datetime
import asyncio
import upsidedown


async def verify(channel, member, role, osulookup, response):
    # Defaults
    osuusername = None
    osujoindate = ""
    pp = "0"
    country = ""
    rankedmaps = "0"
    args = "[]"

    if "/" in osulookup:
        osulookup = osulookup.split('/')
        verificationtype = str(osulookup[0])
        lookupstr = str(osulookup[1])
    else:
        verificationtype == None

    if verificationtype == "u":
        osuprofile = await osuapi.get_user(lookupstr)
        if osuprofile:
            osuusername = str(osuprofile['username'])
            osuaccountid = str(osuprofile['user_id'])
            osujoindate = str(osuprofile['join_date'])
            pp = str(osuprofile['pp_raw'])
            country = str(osuprofile['country'])
            embed = await osuembed.osuprofile(osuprofile)
    elif verificationtype == "s":
        authorsmapset = await osuapi.get_beatmap(lookupstr)
        if authorsmapset:
            osuusername = str(authorsmapset['creator'])
            osuaccountid = str(authorsmapset['creator_id'])
            embed = await osuembed.mapset(authorsmapset)

    if osuusername:
        if type(member) is str:
            discordid = member
        else:
            discordid = str(member.id)
            try:
                await member.add_roles(role)
                await member.edit(nick=osuusername)
            except Exception as e:
                print(time.strftime('%X %x %Z'))
                print("in users.verify")
                print(e)

        if await dbhandler.query(["SELECT discordid FROM users WHERE discordid = ?", [discordid, ]]):
            print("user %s already in database" % (discordid,))
            # possibly force update the entry in future
        else:
            print("adding user %s in database" % (discordid,))
            await dbhandler.query(["INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", [discordid, osuaccountid, osuusername, osujoindate, pp, country, rankedmaps, args]])

        if not response:
            response = "verified <@%s>" % (discordid)

        await channel.send(content=response, embed=embed)
        return True
    else:
        return None


async def guildnamesync(ctx):
    now = datetime.datetime.now()
    for member in ctx.guild.members:
        if not member.bot:
            query = await dbhandler.query(["SELECT * FROM users WHERE discordid = ?", [str(member.id)]])
            if query:
                osuprofile = await osuapi.get_user(query[0][1])
                if osuprofile:
                    if "04-01T" in str(now.isoformat()):
                        osuusername = upsidedown.transform(
                            osuprofile['username'])
                    else:
                        osuusername = osuprofile['username']
                    if member.display_name != osuusername:
                        if "nosync" in str(query[0][7]):
                            await ctx.send("%s | `%s` | `%s` | username not updated as `nosync` was set for this user" % (member.mention, osuusername, str(query[0][1])))
                        else:
                            try:
                                await member.edit(nick=osuusername)
                            except Exception as e:
                                await ctx.send(e)
                                await ctx.send("%s | `%s` | `%s` | no perms to update" % (member.mention, osuusername, str(query[0][1])))
                            await ctx.send("%s | `%s` | `%s` | nickname updated" % (member.mention, osuusername, str(query[0][1])))
                    await dbhandler.query(
                        [
                            "UPDATE users SET country = ?, pp = ?, osujoindate = ?, username = ? WHERE discordid = ?;",
                            [
                                str(osuprofile['country']),
                                str(osuprofile['pp_raw']),
                                str(osuprofile['join_date']),
                                str(osuprofile['username']),
                                str(member.id)
                            ]
                        ]
                    )
                else:
                    await ctx.send("%s | `%s` | `%s` | restricted" % (member.mention, str(query[0][2]), str(query[0][1])))
            else:
                await ctx.send("%s | not in db" % (member.mention))


async def on_member_join(client, member):
    try:
        guildverifychannel = await dbhandler.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["verifychannelid", str(member.guild.id)]])
        if guildverifychannel:
            join_channel_object = await utils.get_channel(client.get_all_channels(), int((guildverifychannel)[0][0]))
            lookupuser = await dbhandler.query(["SELECT osuid FROM users WHERE discordid = ?", [str(member.id), ]])
            if lookupuser:
                print("user %s joined with osuid %s" %
                      (str(member.id), str(lookupuser[0][0])))
                role = discord.utils.get(member.guild.roles, id=int((await dbhandler.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["verifyroleid", str(member.guild.id)]]))[0][0]))
                osulookup = "u/%s" % (lookupuser[0][0])
                verifyattempt = await verify(join_channel_object, member, role, osulookup, "Welcome aboard %s! Since we know who you are, I have automatically verified you. Enjoy your stay!" % (member.mention))

                if not verifyattempt:
                    await join_channel_object.send("Hello %s. It seems like you are in my database but the profile I know of you is restricted. If this is correct, please link any of your uploaded maps (new website only) and I'll verify you instantly. If this is not correct, tag Kyuunex." % (member.mention))
            else:
                await join_channel_object.send("Welcome %s! We have a verification system in this server so we know who you are, give you appropriate roles and keep raids/spam out." % (member.mention))
                osuprofile = await osuapi.get_user(member.name)
                if osuprofile:
                    await join_channel_object.send(content='Is this your osu profile? If yes, type `yes`, if not, link your profile.', embed=await osuembed.osuprofile(osuprofile))
                else:
                    await join_channel_object.send('Please post a link to your osu profile and I will verify you instantly.')
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in on_member_join")
        print(e)


async def on_member_remove(client, member):
    try:
        guildverifychannel = await dbhandler.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["verifychannelid", str(member.guild.id)]])
        if guildverifychannel:
            join_channel_object = await utils.get_channel(client.get_all_channels(), int((guildverifychannel)[0][0]))
            osuid = await dbhandler.query(["SELECT username FROM users WHERE discordid = ?", [str(member.id)]])
            if osuid:
                embed = await osuembed.osuprofile(await osuapi.get_user(osuid[0][0]))
            else:
                embed = None
            await join_channel_object.send("%s left this server. Godspeed!" % (str(member.name)), embed=embed)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in on_member_join")
        print(e)


async def on_message(client, message):
    if message.author.id != client.user.id:
        try:
            verifychannelid = await dbhandler.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["verifychannelid", str(message.guild.id)]])
            if verifychannelid:
                if message.channel.id == int(verifychannelid[0][0]):
                    split_message = []
                    if '/' in message.content:
                        split_message = message.content.split('/')
                    role = discord.utils.get(message.guild.roles, id=int((await dbhandler.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["verifyroleid", str(message.guild.id)]]))[0][0]))

                    if 'https://osu.ppy.sh/u' in message.content:
                        osulookup = "u/%s" % (split_message[4].split(' ')[0])
                        verifyattempt = await verify(message.channel, message.author, role, osulookup, "Verified: %s" % (message.author.name))
                        if not verifyattempt:
                            await message.channel.send('verification failure, I can\'t find any profile from that link. If you are restricted, link any of your recently uploaded maps (new website only).')
                    elif 'https://osu.ppy.sh/beatmapsets/' in message.content:
                        osulookup = "s/%s" % (split_message[4].split('#')[0])
                        verifyattempt = await verify(message.channel, message.author, role, osulookup, "Verified through mapset: %s" % (message.author.name))
                        if not verifyattempt:
                            await message.channel.send('verification failure, I can\'t find any map with that link')
                    elif message.content.lower() == 'yes':
                        osulookup = "u/%s" % (message.author.name)
                        verifyattempt = await verify(message.channel, message.author, role, osulookup, "Verified: %s" % (message.author.name))
                        if not verifyattempt:
                            await message.channel.send('verification failure, your discord username does not match a username of any osu account. possible reason can be that you changed your discord username before typing `yes`. In this case, link your profile.')
                    elif 'https://ripple.moe/u' in message.content:
                        await message.channel.send('ugh, this bot does not do automatic verification from ripple, please ping Kyuunex')
                    elif 'https://osu.gatari.pw/u' in message.content:
                        await message.channel.send('ugh, this bot does not do automatic verification from gatari, please ping Kyuunex')
        except Exception as e:
            print(time.strftime('%X %x %Z'))
            print("in on_message")
            print(e)


async def userdb(ctx, command, mention):
    try:
        if command == "printall":
            if mention == "m":
                tag = "<@%s> / %s"
            else:
                tag = "%s / %s"
            for oneuser in await dbhandler.query("SELECT * FROM users"):
                embed = await osuembed.osuprofile(await osuapi.get_user(oneuser[1]))
                if embed:
                    await ctx.send(content=tag % (oneuser[0], oneuser[2]), embed=embed)
        elif command == "massverify":
            userarray = open("data/users.csv",
                             encoding="utf8").read().splitlines()
            if mention == "m":
                tag = "Preverified: <@%s>"
            else:
                tag = "Preverified: %s"
            for oneuser in userarray:
                uzer = oneuser.split(',')
                await verify(ctx.message.channel, str(uzer[1]), None, "u/%s" % (uzer[0]), tag % (str(uzer[1])))
                await asyncio.sleep(1)
        elif command == "servercheck":
            responce = "These users are not in my database:\n"
            count = 0
            for member in ctx.guild.members:
                if not member.bot:
                    if not await dbhandler.query(["SELECT osuid FROM users WHERE discordid = ?", [str(member.id), ]]):
                        count += 1
                        if mention == "m":
                            responce += ("<@%s>\n" % (str(member.id)))
                        else:
                            responce += ("\"%s\" %s\n" %
                                         (str(member.display_name), str(member.id)))
                        if count > 40:
                            count = 0
                            responce += ""
                            await ctx.send(responce)
                            responce = "\n"
            responce += ""
            await ctx.send(responce)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in userdb")
        print(e)


async def mverify(ctx, osuid, discordid, preverify):
    try:
        if preverify == "preverify":
            await verify(ctx.message.channel, str(discordid), None, osuid, "Preverified: %s" % (str(discordid)))
        else:
            role = discord.utils.get(ctx.message.guild.roles, id=int((await dbhandler.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["verifyroleid", str(ctx.guild.id)]]))[0][0]))
            await verify(ctx.message.channel, ctx.guild.get_member(discordid), role, osuid, "Manually Verified: %s" % (ctx.guild.get_member(discordid).name))
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in verify")
        print(e)

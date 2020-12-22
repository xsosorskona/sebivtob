import math
import random
from typing import Union, Optional
import discord
from discord.ext import commands
from .utils import db
from .utils import checks


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # Set an alias for the bot prefix
    @commands.command(
        name='prefixx',
        description="Sets an alias for the default command prefix.",
        brief="Set command prefix alias.",
        aliases=['prefixalias', 'prefix', 'pre'])
    @commands.guild_only()
    @commands.is_owner()
    async def change_prefix(self, ctx, prefix):
        await db.set_cfg(ctx.guild.id, 'bot_alias', prefix)
        await ctx.channel.send(f"command prefix is now \"{prefix}\".")


    # Set the channel for join messa




    # Toggle guild stat tracking
    @commands.command(
        name='Stats',
        description="Toggles guild stats.",
        aliases=['stats'])
    @commands.guild_only()
    @commands.is_owner()
    async def stats(self, ctx):
        stats = await db.get_cfg(ctx.guild.id, 'guild_stats')
        if stats:
            reply = "Guild stats have been disabled!"
            await db.set_cfg(ctx.guild.id, 'guild_stats', None)
        else:
            reply = "Guild stats have been enabled!"
            await db.set_cfg(ctx.guild.id, 'guild_stats', 'enabled')
        await ctx.channel.send(reply)


    # Manage starboard settings
    @commands.group(
        name='Starboard',
        description="Sets the configuration for starred messages.",
        brief="Modify starboard settings.",
        aliases=['starboard', 'star'])
    @commands.guild_only()
    @commands.is_owner()
    async def starboard(self, ctx, channel: discord.TextChannel=None):
        starboard = await db.get_cfg(ctx.guild.id, 'star_channel')
        if starboard is None:
            await db.set_cfg(ctx.guild.id, 'star_channel', channel.id)
            await ctx.channel.send(f"Set \"{channel.name}\" as the star board.")
        else:
            await db.set_cfg(ctx.guild.id, 'star_channel', None)
            await ctx.channel.send(f"Starboard disabled.")


    # Change starboard threshold
    @starboard.command(
        name='Threshold',
        description="Sets the configuration for starred messages.",
        brief="Modify starboard settings.",
        aliases=['threshold', 't'])
    @commands.guild_only()
    @commands.is_owner()
    async def star_threshold(self, ctx, threshold):
        await db.set_cfg(ctx.guild.id, 'star_threshold', threshold)
        await ctx.channel.send(f"Starboard threshold set to {threshold}")


    # Event hook for reactions being added to messages
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        elif payload.guild_id:
            await self.star_check(payload, 'add')


    # Event hook for reactions being removed from messages
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        elif payload.guild_id:
            await self.star_check(payload, 'rem')


    # Do stuff when a message is sent
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and message.guild:
            dbcfg = await db.get_cfg(message.guild.id)
            if dbcfg['guild_stats'] == 'enabled':
                guildID = message.guild.id
                member = message.author
                profile = await db.get_member(guildID, member.id)
                cashaward = random.randrange(
                    dbcfg['min_cash'],
                    dbcfg['max_cash'])
                await db.add_currency(message.guild.id, member.id, cashaward)
                curxp = profile['xp'] + 1
                await db.set_member(guildID, member.id, 'xp', curxp)
                nextlevel = profile['lvl'] + 1
                levelup = math.floor(curxp / ((2 * nextlevel) ** 2))
                if levelup == 1:
                    channel = message.channel
                    await channel.send(f"**{member.name}** has leveled up to "
                                       f"**level {nextlevel}!**")
                    print("{nextlevel}")
                    await db.set_member(guildID, member.id, 'lvl', nextlevel)
                    role= discord.utils.get(member.guild.roles, name='Bronze')
                    await member.add_roles(role)
                    if nextlevel == 10:
                        role= discord.utils.get(member.guild.roles, name='Silver')
                        await member.add_roles(role)
                        embed = discord.Embed(title="Achievment unlocked!!!", description=f"{member.mention}Silver Role Unlocked", color=0x000000)
                        embed.add_field(name= "You can now", value= "use command -fuck", inline = False)
                    if nextlevel == 20:
                        role= discord.utils.get(member.guild.roles, name='Gold')
                        await member.add_roles(role)
                    if nextlevel == 30:
                        role= discord.utils.get(member.guild.roles, name='Diamond')
                        await member.add_roles(role)
                    if nextlevel == 40:
                        role= discord.utils.get(member.guild.roles, name='Platinum')
                        await member.add_roles(role)
                    if nextlevel == 50:
                        role= discord.utils.get(member.guild.roles, name='Ruby')
                        await member.add_roles(role)
    # Handler for guild reaction events
    async def star_check(self, payload, event):
        dbcfg = await db.get_cfg(payload.guild_id)
        if not dbcfg['star_channel']:
            return
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        if channel.is_nsfw() and not dbcfg['star_nsfw']:
            return
        message = await channel.fetch_message(payload.message_id)
        if message.author.bot:
            return
        prevstar = await db.get_starred(message.id)
        starchannel = guild.get_channel(dbcfg['star_channel'])
        if not prevstar:
            for react in message.reactions:
                if react.count >= dbcfg['star_threshold']:                    
                    await self.star_add(message, starchannel)
                    break
        else:
            if len(message.reactions) < 2:
                await self.star_remove(starchannel, prevstar)
            else:
                for react in message.reactions:
                    if react.count < dbcfg['star_threshold']:
                        await self.star_remove(starchannel, prevstar)
                        break


    # Add star to starboard
    async def star_add(self, message, starchannel):
        star = discord.Embed(description=message.content,
                              color=0xf1c40f)
        star.set_author(name=message.author.display_name,
                         icon_url=message.author.avatar_url)
        if message.attachments:
            images = []
            files = []
            filetypes = ('png', 'jpeg', 'jpg', 'gif', 'webp')
            for attachment in message.attachments:
                if attachment.url.lower().endswith(filetypes):
                    images.append(attachment)
                else:
                    files.append(attachment)
            for i, file in enumerate(files):
                star.add_field(name=f"Attachment {i + 1}",
                               value=f"[{file.filename}]({file.url})",
                               inline=True)
            star.set_thumbnail(url=files[0].url)
        star.add_field(name="--",
                       value=f"[Jump to original...]({message.jump_url})",
                       inline=False)
        star.set_footer(text="Originally sent")
        star.timestamp = message.created_at
        newstar = await starchannel.send(embed=star)
        await db.add_starred(message.guild.id, message.id, newstar.id)


    # Remove star from starboard
    async def star_remove(self, starchannel, starred):
        oldstar = await starchannel.fetch_message(starred['starred_id'])
        await oldstar.delete()
        await db.del_starred(starred['original_id'])

import datetime
import re

import discord
from discord import Spotify
from discord.ext import commands
from discord_buttons_plugin import ButtonsClient, ActionRow, Button, ButtonType

from cog.util import thread_webhook as webhook
from cog.util.DbModule import DbModule as db


class Convenience(commands.Cog):
   def __init__(self, bot):
      self.bot = bot
      self.tweet_wait = False
      self.db = db()
      self.buttons = ButtonsClient(bot)

   @commands.is_owner()
   @commands.slash_command(name="書き込みを削除")
   async def delete_bomb(self, ctx, num: int):
      await ctx.respond("削除を開始します", ephemeral=True)
      await ctx.channel.purge(limit=num)
      await ctx.respond("削除が完了しました", ephemeral=True)

   @commands.slash_command()
   async def spotify(self, ctx, user: discord.Member = None):
      user = user or ctx.author
      if not user.activities:
         await ctx.respond("Spotifyを利用していません")
         return

      for activity in user.activities:
         if isinstance(activity, Spotify):
            embed = discord.Embed(
               title=f"{user.name}'s Spotify",
               description=f"今「{activity.title}」を聴いています",
               color=0xC902FF,
            )
            embed.set_thumbnail(url=activity.album_cover_url)
            embed.add_field(name="アーティスト", value=activity.artist)
            embed.add_field(name="アルバム", value=activity.album)
            embed.add_field(
               name="URL",
               value=f"https://open.spotify.com/track/{activity.track_id}",
               inline=False,
            )
            start_time = activity.created_at + datetime.timedelta(hours=9)
            embed.set_footer(text=f"開始時刻{start_time.strftime('%H:%M')}")
            await ctx.respond(embed=embed)

   @commands.slash_command()
   async def status(self, ctx, user: discord.Member = None):
      """ユーザーのステータスを確認します"""
      user = user or ctx.author
      embed = discord.Embed(title=user.name, color=0xC902FF)
      embed.set_thumbnail(url=user.avatar.url)
      embed.add_field(name="ユーザーID", value=user.id, inline=False)
      embed.add_field(name="ニックネーム", value=user.display_name, inline=False)
      joined_time = user.joined_at + datetime.timedelta(hours=9)
      embed.add_field(
         name="幽霊になった日",
         value=joined_time.strftime("%Y-%m-%d %H:%M:%S"),
         inline=False,
      )
      joined_time = user.created_at + datetime.timedelta(hours=9)
      embed.add_field(
         name="ユーザー作成日",
         value=joined_time.strftime("%Y-%m-%d %H:%M:%S"),
         inline=False,
      )
      roles = [x.name.replace("@", "") for x in user.roles]
      text = ",".join(roles)
      embed.add_field(name="ロール", value=text, inline=False)
      await ctx.respond(embed=embed)

   @commands.Cog.listener()
   async def on_message(self, message):
      try:
         if message.author.bot or message.guild.id == 501071734620028938:
            return
      except AttributeError:
         return

      # 絵文字が送信されたら拡大して送信
      if message.content.startswith("<") and message.content.endswith(">"):
         name = message.content.split(":")[1]
         emoji = discord.utils.get(message.guild.emojis, name=name)
         await message.delete()
         wh = discord.utils.get(await message.channel.webhooks(), name="久川颯")
         await wh.send(
            content=emoji.url,
            username=message.author.display_name,
            avatar_url=message.author.avatar.url,
         )

      if "https://x.com" in message.content or "https://twitter.com" in message.content:
         if "https://x.com" in message.content:
            text = message.content.replace("https://x.com", "https://vxtwitter.com")
         pattern = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
         urls = re.findall(pattern, text)
         Ch_webhook = await webhook.get_webhook(message.channel)
         payload = webhook.payload_edit(message.author.display_name, message.author.avatar.url, text)
         webhook.custom_send(payload, Ch_webhook.url, message.channel)
         for url in urls:
            url = url.replace("https://vxtwitter.com", "https://x.com")
            await self.buttons.send(
               channel=message.channel.id,
               components=[
                  ActionRow(
                     [
                        Button(
                           label="POSTに飛ぶ",
                           style=ButtonType().Link,
                           url=url,
                           disabled=False,
                        )
                     ]
                  )
               ],
            )
         await message.delete()


def setup(bot):
   bot.add_cog(Convenience(bot))

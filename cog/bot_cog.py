import os

from discord.ext import commands  # Bot Commands Frameworkのインポート

from cog.util.DbModule import DbModule as db


class Bot(commands.Cog):
   def __init__(self, bot):
      self.bot = bot
      self.tweet_wait = False
      self.stone = False
      self.db = db()

   @commands.command("goodbye")
   async def disconnect(self, ctx):
      """botを切ります"""
      await ctx.send("また会いましょう")
      await self.bot.logout()

   @commands.is_owner()
   @commands.slash_command()
   async def reload(self, ctx):
      """コグをリロードします"""
      for filename in os.listdir("cog"):
         if filename.endswith(".py"):
            self.bot.reload_extension(f"cog.{filename[:-3]}")
      await ctx.respond("リロードが完了しました")

   @commands.Cog.listener()
   async def on_member_remove(self, member):
      channel = self.bot.get_channel(os.getenv("NOTIFY_ROOM"))
      if member.guild.id != os.getenv("Ghost_House"):
         return
      await channel.send(f"{member.display_name}は消えました")


def setup(bot):
   bot.add_cog(Bot(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。

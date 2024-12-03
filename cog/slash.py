from discord.ext import commands

from cog.util import thread_webhook as webhook
from cog.util.DbModule import DbModule as db


class Slash(commands.Cog):
   def __init__(self, bot):
      self.bot = bot
      self.db = db()

   @commands.slash_command(name="繰り返し")
   async def repeat(self, ctx, word: str, num: int):
      """同じ言葉を繰り返すコマンドです。引数は(単語,回数)"""
      send_word = ""
      if len(word) * num > 2000:
         await ctx.respond("文字数が多いぞ、バランスがすべてだ")
      for i in range(num):
         send_word += word
      Ch_webhook = await webhook.get_webhook(ctx)
      payload = webhook.payload_edit(ctx.author.display_name, ctx.author.avatar.url, send_word)
      webhook.send(payload, Ch_webhook.url, ctx)

   @commands.slash_command(name="絵文字の合成")
   async def emoji_compose(self, ctx, emoji1: str, emoji2: str):
      url = f"https://emojik.vercel.app/s/{emoji1}_{emoji2}?size=128"
      await ctx.respond(url)

   @commands.slash_command(name="vitsのオンオフ")
   async def vits_switcher(self, ctx):
      if self.db.select("select * from flag_control where flag_name='vits_use'")[0]["flag"] == 1:
         self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "vits_use"})
         await ctx.respond("VITSをオフにしました")
      else:
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "vits_use"})
         await ctx.respond("VITSをオンにしました")

   @commands.Cog.listener()
   async def on_application_command_error(self, ctx, error):
      if isinstance(error, (commands.MissingRole, commands.MissingAnyRole, commands.CheckFailure)):
         await ctx.reply("権限がありません")
      else:
         print(error)


def setup(bot):
   bot.add_cog(Slash(bot))

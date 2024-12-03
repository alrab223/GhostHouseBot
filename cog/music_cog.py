import asyncio
import glob
import json
import os
import re

import discord
import ffmpeg
import gspread
import requests
from discord.ext import commands

from cog.util.DbModule import DbModule as db
from cog.util.tts import make_gtts, make_vits2


class Tts:
   async def sound_play(self, path, volume):
      self.voich.play(discord.FFmpegPCMAudio(path))
      self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
      self.voich.source.volume = volume
      while self.voich.is_playing() is True:  # 再生が終わるまで待機
         await asyncio.sleep(0.5)

   # 読み上げるデータの前処理

   def se_preprocessing(self, text, sounds):
      create_text = ""  # SEを混ぜるための一時変数
      voice_data = {}  # テキストとSEの情報を入れる変数
      counter = 1  # 分割数の管理

      for i in list(text):  # テキストをリスト化
         create_text += i
         for se_data in sounds:
            if se_data["word"] == create_text and se_data["short"] == 1:
               voice_data[str(counter)] = {
                  "type": "se",
                  "volume": se_data["volume"],
                  "path": se_data["sound_path"],
               }
               create_text = ""
               counter += 1
            elif se_data["word"] in create_text and se_data["short"] == 1:
               word = create_text.replace(se_data["word"], "")
               voice_data[str(counter)] = {"type": "text", "word": word}
               counter += 1
               voice_data[str(counter)] = {
                  "type": "se",
                  "volume": se_data["volume"],
                  "path": se_data["sound_path"],
               }
               create_text = ""
               counter += 1

      if create_text != "":  # 残りの文字の処理
         voice_data[str(counter)] = {"type": "text", "word": create_text}

      if voice_data == {}:  # SEが無かった場合
         voice_data[str(counter)] = {"type": "text", "word": text}
      return voice_data

   # 読み上げ処理
   async def Voice_Read(self, text, user_id):
      while self.voich.is_playing() is True:
         await asyncio.sleep(0.5)
      if self.db.select("select * from flag_control where flag_name='vits_use'")[0]["flag"] == 1:
         try:
            status = requests.get(
               f'http://{os.getenv("VITS2_SERVER")}:{os.getenv("VITS2_PORT")}/status',
               timeout=2,
            ).status_code
         except requests.exceptions.RequestException:
            self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "vits_use"})
            status = 404
      else:
         status = 404

      def get_user_data(user_id):
         with open("user_vcmodel.json") as f:
            user_data = json.load(f)
         try:
            user_data = user_data[str(user_id)]
         except KeyError:
            user_data = 404
         return user_data

      if status == 200:
         user_data = get_user_data(user_id)
         path = make_vits2(
            text,
            user_data["speaker_id"],
            user_data["model_id"],
            user_data["language"],
            user_data["style"],
         )
         try:
            await self.sound_play(path, 0.5)
         except AssertionError:
            await asyncio.sleep(0.5)
         return
      else:
         se_sounds = self.db.select("select *from read_text_se order by priority asc")  # SE一覧
         voice_data = self.se_preprocessing(text, se_sounds)

      # SEか読み上げのみの場合
      if len(voice_data) == 1:
         for voice in voice_data.values():
            if voice["type"] == "se":  # SEのみ
               await self.sound_play(voice["path"], voice["volume"])
            else:  # 読み上げのみ
               try:
                  path = make_gtts(voice, self.convert_list)
                  await self.sound_play(path, 0.5)
               except AssertionError:
                  await asyncio.sleep(0.5)

      # SEと読み上げ混合の場合
      else:
         sounds = []
         for voice in voice_data.values():
            if voice["type"] == "se":
               sounds.append(voice["path"])
            else:
               try:
                  path = make_gtts(voice, self.convert_list)
                  sounds.append(path)
               except AssertionError:
                  await asyncio.sleep(0.5)
         ffmpeg.input("concat:" + "|".join(sounds)).output("output.mp3").run(overwrite_output=True)

         await self.sound_play("output.mp3", 0.5)
         os.remove("output.mp3")

   def read_censorship(self, message):
      pattern = "https?://[\\w/:%#\\$&\\?\\(\\)~\\.=\\+\\-]+"
      text = message.content
      text = re.sub(pattern, "URL省略", message.content)
      if text.startswith("<"):
         return ""
      elif text.startswith("!"):
         return ""
      elif text.count(os.linesep) > 4:
         text = "改行が多数検出されたため、省略します"
      elif len(text) > 100:
         text = "文字数が多いか、怪文書が検出されましたので省略します"
      elif message.attachments and text == "":
         text = "画像が添付されました"
      return text


class Music(commands.Cog, Tts):
   def __init__(self, bot):
      self.bot = bot
      self.voich = None
      self.volume = 0.1
      self.db = db()
      self.read = self.db.select("select * from flag_control where flag_name='read_text'")[0]["flag"]
      gc = gspread.service_account(filename="json/service_account.json")
      sh = gc.open("読み上げ").sheet1
      self.convert_list = sh.get_all_values()

   @commands.slash_command(name="botをボイスチャンネルに召喚")
   async def voice_connect(self, ctx):
      """botをボイチャに召喚します"""
      self.voich = await discord.VoiceChannel.connect(ctx.author.voice.channel)
      self.voich.play(discord.FFmpegPCMAudio("music/se/oberon_enter.mp3"))
      self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
      self.voich.source.volume = 0.3
      await ctx.respond("ばばーん")
      await asyncio.sleep(2)

   @commands.is_owner()
   @commands.slash_command(name="botをボイスチャンネルから追い出す")
   async def voice_disconnect(self, ctx):
      """botをボイチャから退出させます"""
      if self.voich.is_playing():
         self.voich.stop()

      await self.voich.disconnect()
      self.voich = None
      await ctx.respond("さよなら")

   @commands.slash_command(name="読み上げ辞書更新")
   async def dic_update(self, ctx):
      """読み上げ辞書の更新を行います"""
      await ctx.response("辞書を更新しました")
      gc = gspread.service_account(filename="json/service_account.json")
      sh = gc.open("読み上げ").sheet1
      self.convert_list = sh.get_all_values()

   @commands.slash_command(name="読み上げ停止")
   async def read_stop(self, ctx):
      """今読み上げているテキストを停止"""
      if self.voich.is_playing():
         self.voich.stop()

   @commands.slash_command(name="読み上げ機能のオンオフ")
   async def reads(self, ctx):
      if self.read == 1:
         self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "read_text"})
         self.read = 0
         await ctx.respond("読み上げをオフにしました")
         self.db.auto_delete("channel_flag_control", {"flag_name": "read_text"})
      else:
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "read_text"})
         self.read = 1
         await ctx.respond("読み上げをオンにしました")
         self.db.allinsert("channel_flag_control", [ctx.channel.id, "read_text"])
         self.db.update("delete from read_text")

   @commands.slash_command(name="朗読")
   async def free_read(self, ctx, text: str):
      await ctx.respond("読み上げます")
      await self.Voice_Read(text, ctx.author.id)

   # メッセージが書き込まれた時の読み上げ処理

   @commands.Cog.listener()
   async def on_message(self, message):
      # botの発言や、読み上げがオフの場合は無視
      if self.read == 1 and message.author.bot is False and self.voich is not None:
         channel_id = self.db.select("select *from channel_flag_control where flag_name='read_text'")[0]["channel_id"]
         if message.channel.id == channel_id:
            text = self.read_censorship(message)
            if text != "":
               await self.Voice_Read(text, message.author.id)

   @commands.Cog.listener()
   async def on_voice_state_update(self, member, before, after):
      if member.bot:
         return

      # 誰かがVCに入った場合、再接続
      if self.voich is None:
         vc_channel = self.bot.get_channel(int(os.getenv("VC_CH")))
         self.voich = await discord.VoiceChannel.connect(vc_channel)

      # VC入退室の通知
      channel = self.bot.get_channel(int(os.getenv("VC_NOTIFY_CH")))
      if before.channel is None and after.channel.id == int(os.getenv("VC_CH")):
         await channel.send(f"{member.display_name}が{after.channel.name}に参加した")
      elif after.channel is None and before.channel.id == int(os.getenv("VC_CH")):
         await channel.send(f"{member.display_name}が{before.channel.name}から消え去った")

      # 入室SEを流す
      if before.channel is None and self.voich is not None:
         row = self.db.select(f"select * from enter_se where id={member.id}")
         if row[0]["se"] != "":
            self.voich.play(discord.FFmpegPCMAudio(row[0]["se"]))
         if row[0]["volume"] is not None:
            self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
            self.voich.source.volume = row[0]["volume"]

   @commands.Cog.listener()
   async def on_ready(self):
      vc_channel = self.bot.get_channel(int(os.getenv("VC_CH")))
      self.voich = await discord.VoiceChannel.connect(vc_channel)
      files = glob.glob("music/mp3/*.mp3")
      for f in files:
         os.remove(f)


def setup(bot):
   bot.add_cog(Music(bot))

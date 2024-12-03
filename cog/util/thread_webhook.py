import requests
import discord


async def get_webhook(channel):
   if str(channel.type) == "public_thread":
      channel = channel.parent
   else:
      channel = channel
   ch_webhooks = await channel.webhooks()
   webhook = discord.utils.get(ch_webhooks, name="久川颯")
   if webhook is None:
      webhook = await channel.create_webhook(name="久川颯")
   return webhook


def payload_edit(username: str, avatar_url: str, content: str = None, attachment: list = None, components: list = None):
   payload = {}
   payload["username"] = username
   payload["avatar_url"] = avatar_url
   payload["content"] = content
   payload["embeds"] = []
   if attachment is None or attachment == []:
      pass
   else:
      payload["embeds"].append(
         {
            "url": "https://www.pixiv.net/fanbox",
            "author": {"url": "https://www.pixiv.net/fanbox"},
            "image": {"url": attachment.pop(0)},
         }
      )
      for url in attachment:
         payload["embeds"].append({"url": "https://www.pixiv.net/fanbox", "image": {"url": url}})

   if components is not None:
      payload["components"] = components
   return payload


async def send(content: str, ctx, file=None):
   ch_webhooks = await get_webhook(ctx.channel)
   # 添付ファイルの有無で分岐
   if file is None:
      if str(ctx.channel.type) == "public_thread":
         await ch_webhooks.send(
            content=content, username=ctx.author.display_name, avatar_url=ctx.author.avatar.url, thread=ctx.channel
         )
      else:
         await ch_webhooks.send(content=content, username=ctx.author.display_name, avatar_url=ctx.author.avatar.url)
   else:
      if str(ctx.channel.type) == "public_thread":
         await ch_webhooks.send(
            file=file, username=ctx.author.display_name, avatar_url=ctx.author.avatar.url, thread=ctx.channel
         )
      else:
         await ch_webhooks.send(file=file, username=ctx.author.display_name, avatar_url=ctx.author.avatar.url)


def custom_send(payload: dict, url, channel):
   if str(channel.type) == "public_thread":
      WEBHOOK_URL = f"{url}?thread_id={channel.id}&wait=True"
   else:
      WEBHOOK_URL = url
   res = requests.post(WEBHOOK_URL, json=payload)
   return res.status_code

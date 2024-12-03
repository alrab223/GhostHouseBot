import datetime
import json
import os

import requests
from gtts import gTTS


def make_path(text):
   if len(text) > 20:
      text = text[:20]
   file_name = datetime.datetime.now().strftime(f"%Y%m%d_%H%M%S_{text}")
   path = f"music/mp3/{file_name}.mp3"
   return path


def read_convert(text, convert_list):
   read_list = [word for word in convert_list[1::] if word[0] in text]
   read_list.sort(key=lambda x: x[2])  # 優先度でソート
   for word in read_list:
      text = text.replace(word[0], word[1])
   return text


def make_gtts(voice, convert_list):
   text = read_convert(voice["word"], convert_list)
   tts = gTTS(text=text, lang="ja")
   path = make_path(text)
   tts.save(path)
   return path


def make_vits2(text, speaker_id, model_id, language, style):
   params = {
      "text": text,  # 変換するテキスト
      "speaker_id": speaker_id,  # 話者のID
      "model_id": model_id,  # モデルのID
      "sdp_ratio": 0.2,  # SDP（Stochastic Duration Predictor）とDP（Duration Predictor）の混合比率
      "noise": 0.6,  # サンプルノイズの割合（ランダム性を増加させる）
      "noisew": 0.8,  # SDPノイズの割合（発音の間隔のばらつきを増加させる）
      "length": 1,  # 話速（1が標準）
      "language": language,  # テキストの言語
      "auto_split": "true",  # 自動でテキストを分割するかどうか
      "split_interval": 1,  # 分割した際の無音区間の長さ（秒）
      "assist_text": None,  # 補助テキスト（読み上げと似た声音・感情になりやすい）
      "assist_text_weight": 1.0,  # 補助テキストの影響の強さ
      "style": style,  # 音声のスタイル
      "style_weight": 5.0,  # スタイルの強さ
      "reference_audio_path": None,  # 参照オーディオパス（スタイルを音声ファイルで指定）
   }
   data = requests.get(f'http://{os.getenv("VITS2_SERVER")}:{os.getenv("VITS2_PORT")}/voice', params=params)

   path = make_path(text)
   with open(path, "wb") as f:
      f.write(data.content)
   return path

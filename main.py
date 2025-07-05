import argparse
import json
import math
import os
import time
from itertools import batched
from pathlib import Path

from google import genai
from pycountry import languages
from tqdm import tqdm
from utils import parse_srt, write_srt


def get_chat_client(api_key, model, system_instruction=None, thinking=False):
  client = genai.Client(api_key=api_key)
  
  try:
    models = [m.name.removeprefix("models/") for m in client.models.list()]
  except genai.errors.ClientError as e:
    print(e.message)
    return

  if model not in models:
    print(f"Invalid model name: {model}")
    return

  return client.chats.create(
    model=model,
    config=genai.types.GenerateContentConfig(
      system_instruction=system_instruction,
      thinking_config=genai.types.ThinkingConfig(thinking_budget=-int(thinking)),
    )
  )


def parse_language(language):
  lang = languages.get(name=language)
  if lang is None:
    raise ValueError("Invalid language")
  return lang


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("srt_path", type=Path)
  parser.add_argument("-b", "--batch", type=int, default=50)
  parser.add_argument("-c", "--cooldown", type=int, default=20)
  parser.add_argument("-l", "--language", type=parse_language, required=True)
  parser.add_argument("-m", "--model", type=str, default='gemini-2.5-flash')
  parser.add_argument("-e", "--example", action="store_true")
  parser.add_argument("-t", "--thinking", action="store_true")
  return parser.parse_args()


def parse_response(response):
  text: str = response.text
  text = text.removeprefix('```json').removesuffix('```')
  try:
    return json.loads(text)
  except json.JSONDecodeError:
    return


def parse_instruction(language, example=True):
  instruction_path = Path("system_instruction.md")
  assert instruction_path.is_file()
  with instruction_path.open("r") as f:
    instruction = f.read().format(lang=language.name)

  if example:
    example_dir = Path("examples")
    example_path = example_dir / f"example_{language.alpha_2}.md"
    assert example_path.is_file()
    with example_path.open("r") as f:
      instruction += f.read()

  return instruction


def main():
  args = parse_args()
  api_key = os.environ.get("GOOGLE_API_KEY", None)
  if api_key is None:
    api_key = input("API key: ")

  system_instruction = parse_instruction(args.language, args.example)
  chat = get_chat_client(api_key, args.model, system_instruction, args.thinking)
  if chat is None:
    return

  srt = parse_srt(args.srt_path)
  texts = [{'n': s['n'], 'text': s['text']} for s in srt]
  timestamps = [s['timestamp'] for s in srt]

  translated = []
  while True:
    for batch in tqdm(batched(texts, args.batch), total=math.ceil(len(texts)/args.batch)):
      batch_text = json.dumps(list(batch), indent=2)
      while True:
        try:
          response = chat.send_message(batch_text)
          res = parse_response(response)
          if res is not None:
            translated += res
            break
        except Exception as e:
          print(e.message)
        finally:
          time.sleep(args.cooldown)

    if len(translated) == len(srt):
      print("Translation finished.")
      results = [{**tr, 'timestamp': ts, 'original_text': s['text']} for tr, ts, s in zip(translated, timestamps, srt)]
      write_srt(results, args.srt_path.with_suffix(f".{args.language.alpha_2}.srt"))
      break

    print("Translation failed.")
    retry = input("Retry? (y/n)")
    if retry.casefold in ['n', 'no']:
      break


if __name__ == "__main__":
  main()
  
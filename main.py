import argparse
import json
import math
import os
import time
from pathlib import Path

from google import genai
from pycountry import languages
from tqdm import tqdm
from utils import batched, parse_json, parse_srt, write_srt


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
  if lang:
    return lang

  lang = languages.get(alpha_2=language)
  if lang:
    return lang

  lang = languages.get(alpha_3=language)
  if lang:
    return lang

  raise ValueError(f"Invalid language: {language}")


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("srt_path", type=Path)
  parser.add_argument("-b", "--batch", type=int, default=50)
  parser.add_argument("-c", "--cooldown", type=int, default=20)
  parser.add_argument("-l", "--language", type=parse_language, required=True)
  parser.add_argument("-m", "--model", type=str, default='gemini-2.5-flash')
  parser.add_argument("-e", "--example", action="store_true")
  parser.add_argument("-t", "--thinking", action="store_true")
  parser.add_argument("--save-json", action="store_true")
  parser.add_argument("--start-index", type=int, default=1)
  parser.add_argument("--end-index", type=int, default=None)
  return parser.parse_args()


def parse_response(response, original):
  text: str = response.text
  text = text.removeprefix('```json').removesuffix('```')
  try:
    results = json.loads(text)
  except json.JSONDecodeError:
    return

  ns = {item['n'] for item in original}
  return [item for item in results if item['n'] in ns]


def parse_instruction(language, example=True):
  instruction_path = Path("system_instruction.md")
  assert instruction_path.is_file()
  with instruction_path.open("r") as f:
    instruction = f.read().format(lang=language.name)

  if not example:
    return instruction
  
  example_dir = Path("examples")
  example_path = example_dir / f"example_{language.alpha_2}.md"
  if not example_path.is_file():
    print(f"Warning: No example file for the target language: {language.alpha_2}")
    print("Proceed without the example")
    return instruction

  with example_path.open("r") as f:
    instruction += f.read()

  return instruction


def parse_input(input_path: Path):
  if not input_path.is_file():
    raise FileNotFoundError(f"No such file exists: {str(input_path)}")

  suffix = input_path.suffix.casefold()
  if suffix not in [".json", ".srt"]:
    raise ValueError(f"Unsupported file type: {suffix}")

  if suffix == ".srt":
    return parse_srt(input_path)

  return parse_json(input_path)


def is_valid(results, original):
  if results is None or len(results) != len(original):
    return False

  for r, o in zip(results, original):
    if r['n'] != o['n']:
      return False

  return True


def translate(client, texts, nbatch, cooldown):
  success = []
  failed = []
  for batch in tqdm(batched(texts, nbatch), total=math.ceil(len(texts)/nbatch)):
    batch_text = json.dumps(list(batch), indent=2)
    try:
      response = client.send_message(batch_text)
      res = parse_response(response, batch)
      if is_valid(res, batch):
        success.append(res)
      else:
        failed.append(batch)
    except Exception as e:
      print(repr(e))
    finally:
      time.sleep(cooldown)
  return success, failed


def main():
  args = parse_args()
  api_key = os.environ.get("GOOGLE_API_KEY", None)
  if api_key is None:
    api_key = input("API key: ")

  system_instruction = parse_instruction(args.language, args.example)
  chat = get_chat_client(api_key, args.model, system_instruction, args.thinking)
  if chat is None:
    print("Failed to get the client.")
    return

  srt = parse_input(args.srt_path)
  if args.start_index > srt[-1]['n']:
    print("Start index must not exceed the highest index:")
    print(f"max index: {srt[-1]['n']}")
    return

  end_index = args.end_index or srt[-1]['n']
  if end_index < args.start_index:
    print("Start index must be less than end index.")
    return

  srt = srt[args.start_index-1:end_index]

  texts = [{'n': s['n'], 'text': s['text']} for s in srt]
  timestamps = [s['timestamp'] for s in srt]

  success, failed = translate(chat, texts, args.batch, args.cooldown)
  while len(failed) > 0:
    chat = get_chat_client(api_key, args.model, system_instruction, args.thinking)
    failed_texts = [item for batch in failed for item in batch]
    s, failed = translate(chat, failed_texts, args.batch, args.cooldown)
    success += s

  print("Translation finished.")
  translated = sorted([item for batch in success for item in batch], key=lambda x: x['n'])
  assert len(translated) == len(srt)

  results = [
    {**tr, 'timestamp': ts, 'original_text': s['text']}
    for tr, ts, s in zip(translated, timestamps, srt)
  ]
  write_srt(results, args.srt_path.with_suffix(f".{args.language.alpha_2}.srt"))
  if args.save_json:
    with args.srt_path.with_suffix(f".{args.language.alpha_2}.json").open("w") as f:
      json.dump(results, f, indent=2)


if __name__ == "__main__":
  main()

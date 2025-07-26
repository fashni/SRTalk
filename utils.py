import itertools
import json
from pathlib import Path


try:
  batched = itertools.batched
except:
  def batched(iterable, n, *, strict=False):
    if n < 1:
      raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
      if strict and len(batch) != n:
        raise ValueError('batched(): incomplete batch')
      yield batch


def parse_srt(file_path):
  subtitles = []
  subtitle = {'n': None, 'timestamp': None, 'text': None}

  with Path(file_path).open('r', encoding='utf-8-sig') as file:
    for line in file:
      line = line.strip()

      if line.isdigit() and subtitle['n'] is None:
        subtitle['n'] = int(line)

      elif '-->' in line and subtitle['timestamp'] is None:
        subtitle['timestamp'] = line

      elif line == "":
        if subtitle['n'] is not None and subtitle['timestamp'] is not None:
          subtitles.append(subtitle)
          subtitle = {'n': None, 'timestamp': None, 'text': None}

      else:
        if subtitle['text'] is not None:
          subtitle['text'] += "<br>" + line
        else:
          subtitle['text'] = line

    if subtitle['n'] is not None and subtitle['timestamp'] is not None:
      subtitles.append(subtitle)

  return subtitles


def write_srt(subtitles, output_path):
  with Path(output_path).open('w', encoding='utf-8') as file:
    for subtitle in subtitles:
      file.write(f"{subtitle['n']}\n")
      file.write(f"{subtitle['timestamp']}\n")

      if subtitle['text'] is None:
        print(subtitle['n'])
        text = ""
      else:
        text = subtitle['text'].replace('<br>', '\n')
      file.write(f"{text}\n")

      file.write("\n")


def parse_json(json_path):
  required_keys = {"n", "timestamp", "text"}
  with Path(json_path).open("r") as f:
    data = json.load(f)

  if not isinstance(data, list):
    raise ValueError("JSON must be an array")

  valid_data = []
  for idx, item in enumerate(data):
    if not isinstance(item, dict):
      raise ValueError(f"Item at index {idx} is not a JSON object")

    missing_keys = required_keys - item.keys()
    if missing_keys:
      raise ValueError(f"Item at index {idx} is missing required keys: {', '.join(missing_keys)}")

    text = item.get("original_text", item["text"])
    valid_data.append({
      "n": item["n"],
      "timestamp": item["timestamp"],
      "text": text,
    })

  return valid_data

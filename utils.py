from itertools import islice
from pathlib import Path

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

def batched(iterable, n, *, strict=False):
  if n < 1:
    raise ValueError('n must be at least one')
  iterator = iter(iterable)
  while batch := tuple(islice(iterator, n)):
    if strict and len(batch) != n:
      raise ValueError('batched(): incomplete batch')
    yield batch

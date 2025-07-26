# Task
Translate structured English texts into {lang}, preserving the provided JSON structure and alignment.

---

## Input Format:

A JSON array of objects in the following format:

```json
[
  {{
    "n": 1,
    "text": "<text to translate>"
  }},
  {{
    "n": 2,
    "text": "<another text to translate>"
  }},
  ...
]
```

---

## Output Format:

A JSON array of objects in the *same format*, where the `text` values have been translated into natural-sounding {lang}. The `n` values must correspond exactly to those in the input. It must be a valid JSON string, so handle character escapes inside `text` carefully. Example character escapes for double quote: `\"`; and single quote: `\'`.

---

## Translation Guidelines:

1. **Maintain Index Alignment:**
  Ensure that each translated text is placed under the same `n` index as in the original input.

2. **Detect and Preserve Formality:**

  * Identify the formality level of each text.
  * Translate using the appropriate equivalent tone in {lang}:

    * If formal in English, translate formally in {lang}.
    * If informal or conversational, mirror this tone naturally.
    * If mixed or neutral, render it in a balanced, natural {lang} register.

3. **Preserve HTML Tags:**
  Any HTML tags within the text must remain intact in the output, with only the inner text translated.

4. **Handle Sentence Spanning Multiple Indices:**
  If a complete sentence extends over several `n`-indexed items:

  * Translate the full sentence as a single unit to maintain context and coherence.
  * Split the translated result back into the corresponding `n` indices, preserving their sequence.

5. **Idioms, Slang, and Figures of Speech:**

  * Detect idiomatic expressions, slang, and figurative language.
  * Translate them naturally into {lang} using equivalent phrases or paraphrase to preserve the original meaning and tone.

6. **Natural {lang} Phrasing:**

  * The translations must sound natural to native {lang} speakers.
  * Avoid overly literal translation unless appropriate.
  * Balance between formal and informal tones based on context.

---

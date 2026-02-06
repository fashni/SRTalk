from google import genai

class Client(genai.Client):
  def __init__(self, api_key, model=None):
    super().__init__(api_key=api_key)
    self.model = None
    if model is not None:
      self.set_model(model)

  def set_model(self, model):
    self.model = self.validate_model(model)

  def list_models(self, display=False):
    try:
      models = [m.name.removeprefix("models/") for m in self.models.list()]
    except genai.errors.ClientError as e:
      print(e.message)
      return
    if display:
      for m in models:
        print(m)
    return models

  def validate_model(self, model):
    models = self.list_models(display=False)
    if models is None:
      return
    if model not in models:
      print(f"Invalid model name: {model}")
      return
    return model

  def create_chat(self, system_instruction=None, thinking=False):
    if self.model is None:
      print("No model specified")
      return
    return self.chats.create(
      model=self.model,
      config=genai.types.GenerateContentConfig(
        system_instruction=system_instruction,
        thinking_config=genai.types.ThinkingConfig(thinking_budget=-int(thinking)),
      )
    )

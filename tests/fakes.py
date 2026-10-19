from types import SimpleNamespace


class FakeGemini:
    """Stands in for genai.Client: records each call, returns canned text.

    Pass several responses to answer successive calls in order. A response
    that is an Exception is raised instead of returned.
    """

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
        self.models = self

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(text=response)

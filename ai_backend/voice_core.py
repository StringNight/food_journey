import whisper

model = whisper.load_model("turbo", device="cuda")


def transcribe(audio):
    result = model.transcribe(audio)
    return result["text"]

import json
from time import sleep
from typing import Generator
import gradio as gr

from chat_core import ChatInput, chat_llm, chat_llm_stream
from image_core import image_recognition
from voice_core import transcribe


def chat(messages: list, model: str, max_tokens: int) -> json:
    input = ChatInput(
        messages=messages,
        max_tokens=max_tokens,
        model=model,
    )

    output = chat_llm(input)
    return output.response.content


def chat_stream(messages: list, model: str, max_tokens: int) -> Generator:
    input = ChatInput(
        messages=messages,
        max_tokens=max_tokens,
        model=model,
    )

    output = chat_llm_stream(input)
    partial_message = ""
    for chunk in output:
        partial_message = partial_message + chunk["message"]["content"]
        yield partial_message


def voice_transcribe(audio) -> str:
    return transcribe(audio)


def food_recognition(file) -> str:
    return image_recognition(file)


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            messages_component = gr.JSON(
                label="Messages",
                value=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. You will talk like a pirate.",
                    },
                ],
            )
            model_component = gr.Dropdown(
                label="Model",
                choices=["qwen2.5:14b"],
                value="qwen2.5:14b",
            )
            max_tokens_component = gr.Slider(label="Max Tokens", minimum=1000, maximum=2000, value=2000, step=100)
            voice_input_component = gr.Audio(label="Voice Input", sources=["upload", "microphone"], type="filepath")
            image_input_component = gr.Textbox(label="Image Input")
            # image_input_component = gr.Image(
            #     label="Image Input", type="filepath", sources="upload"
            # )
            submit_button_component = gr.Button(value="Chat", variant="primary")
            stream_button_component = gr.Button(value="Stream", variant="primary")
            audio_button_component = gr.Button(value="Audio", variant="primary")
            image_button_component = gr.Button(value="Image", variant="primary")
        with gr.Column():
            text_output_component = gr.Textbox(label="Model Output", placeholder="Text Output")
            stream_output_component = gr.Textbox(label="Model Output", placeholder="Text Output")
            audio_output_component = gr.Textbox(label="Audio Output", placeholder="Audio Output")
            image_output_component = gr.Textbox(label="Image Output", placeholder="Image Output")

    submit_button_component.click(
        fn=chat,
        inputs=[
            messages_component,
            model_component,
            max_tokens_component,
        ],
        outputs=[text_output_component],
    )

    stream_button_component.click(
        fn=chat_stream,
        inputs=[
            messages_component,
            model_component,
            max_tokens_component,
        ],
        outputs=[stream_output_component],
    )

    audio_button_component.click(
        fn=voice_transcribe,
        inputs=[voice_input_component],
        outputs=[audio_output_component],
    )

    image_button_component.click(
        fn=food_recognition,
        inputs=[image_input_component],
        outputs=[image_output_component],
    )


demo.launch(server_name="0.0.0.0", share=True, server_port=7860)

# import base64


# def img_to_base64(img_path):
#     f = open(img_path, "rb")
#     img = base64.b64encode(f.read())
#     print(img)


# def send_img(img_path):
#     from gradio_client import Client

#     f = open(img_path, "rb")
#     img = base64.b64encode(f.read())
#     print(img)

#     client = Client("https://97c0a4fd9fb39fb02d.gradio.live")
#     result = client.predict(
#         file=img.decode("utf-8"),
#         api_name="/food_recognition",
#     )
#     print(result)


# # img_to_base64("res.png")
# send_img("res.png")
from gradio_client import Client

client = Client("https://1ba902d825722a9416.gradio.live/")
result = client.submit(
    messages=[
        {
            "role": "system",
            "content": "",
        },
        {"role": "user", "content": "今天晚上健身练背，给一个新手锻炼方案"},
    ],
    model="qwen2.5:14b",
    max_tokens=2000,
    api_name="/chat_stream",
)

import time

current = ""
while result is not None:
    time.sleep(0.005)
    outputs = result.outputs()
    if outputs:
        new_text = outputs[-1]
        # 只打印新增的部分
        new_part = new_text[len(current) :]
        print(new_part, end="")
        current = new_text

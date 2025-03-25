import base64
from ollama import Client, Message


def base64_to_img(bstr):
    imgdata = base64.b64decode(bstr)
    file = open("res.png", "wb")
    file.write(imgdata)
    file.close()

    return imgdata


# file = open("res.png", "wb")
# file.write(imgdata)
# file.close()
# file = open(file_path, "wb")
# file.write(imgdata)
# file.close()


def image_recognition(file):
    # img_data = base64_to_img(file)

    client = Client(host="http://localhost:11434", headers={"Content-Type": "application/json"})

    response = client.chat(
        model="llama3.2-vision:11b",
        messages=[
            {
                "role": "user",
                "content": "What is in this image?",
                "images": [f"{file}"],
            }
        ],
    )

    return response["message"]["content"]

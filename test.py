import base64


def img_to_base64(img_path):
    f = open(img_path, "rb")
    img = base64.b64encode(f.read())
    print(img)


def send_img(img_path):
    from gradio_client import Client

    f = open(img_path, "rb")
    img = base64.b64encode(f.read())
    print(img)

    client = Client("https://63e9cf37a8d05f9e2b.gradio.live/")
    result = client.predict(
        file=img.decode("utf-8"),
        api_name="/food_recognition",
    )
    print(result)


# img_to_base64("res.png")
send_img("test1.jpg")

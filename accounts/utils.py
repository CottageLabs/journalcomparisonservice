import qrcode.image.svg
from io import BytesIO


def totp_qrcode(text: str) -> str:
    """
    Creates an SVG qrcode from a string and returns the SVG source code as a decoded string.
    There is no file generated.
    https://www.sproutqr.com/blog/qr-code-types
    :param text:
    :return:
    """
    qr = qrcode.QRCode(version=13, error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathFillImage,
                        fill_color="black", back_color="white")

    stream = BytesIO()
    img.save(stream)
    return stream.getvalue().decode()


def debug(request):
    print(request.POST)
    for key, value in request.session.items():
        print('{} => {}'.format(key, value))

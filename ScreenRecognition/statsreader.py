import pytesseract.pytesseract
import cv2
from PIL import Image


def read_all_data():
    players = ['knus', 'puad', 'sticker']
    written_data = []

    for player in players:
        written_data.append(read_image(player))

    return written_data


def read_image(player):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Jokim\AppData\Local\Programs\Tesseract-OCR\tesseract"
    img = cv2.imread('img/' + player + '_out.jpg')
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # invert picture
    # img = cv2.bitwise_not(img)

    config = r'--oem 1 --psm 6 -c tessedit_char_whitelist=Ø language=dan'
    return pytesseract.image_to_string(img, config=config)


def read_big_ass_image():
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Jokim\AppData\Local\Programs\Tesseract-OCR\tesseract"
    img = cv2.imread('img/stats.jpg')
    config = r'--oem 1 --psm 6 outputbase digits -c tessedit_char_whitelist=0123456789'
    return pytesseract.image_to_string(img,
                                       config=r'--oem 1 --psm 4 -c tessedit_char_whitelist=8 language=dan')


if __name__ == '__main__':
    data = read_all_data()
    # data = read_big_ass_image()
    print(data)

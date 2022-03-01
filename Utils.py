import socket

#trasformazione messaggio in byte
def encodeMessage(protocol:int, uuid:str, message):
    from pickle import dumps
    from base64 import b64encode
    return b64encode(dumps((protocol, uuid, message)))

#decodificazione del messaggio nella struttura tupla(protocollo, id, messaggio)
def decodeMessage(message:bytes):
    from pickle import loads
    from base64 import b64decode
    return loads(b64decode(message))

#generazione id
def generate_uuid():
    from uuid import uuid4
    return str(uuid4())

#conversione array numpy in immagine tkinter
def toImage(arr):
    from PIL import ImageTk, Image
    return ImageTk.PhotoImage(image=Image.fromarray(arr))

#encode in jpg per ridurre la dimensione
def ndarrayToJPG(ndarray, extension:str=".jpg"):
    from cv2 import imencode
    return imencode(extension, ndarray)[1]

#decodificazione da jpg
def JPGToNdarray(img):
    from cv2 import imdecode, IMREAD_COLOR
    return imdecode(img, IMREAD_COLOR)

#creazione socket tcp generica
def createTcpSocket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

#creazione socket udp generica
def createUdpSocket(buffer_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
    return sock

#creazione videocamera
def createLabel(frame, width, height, x=0, y=0, bg="black"):
    from tkinter import Label
    label = Label(
        frame,
        bg = bg
    )
    label.place(
        width=width,
        height=height,
        x=x,
        y=y
    )
    return label

#aggiornamento dell'immagine con il frame in arrivo
def updateLabelImage(label, image):
    image = toImage(image)
    label.configure(image=image)
    label.image = image

#aggiornameto posizione e dimensione della webcam
def updateLabelPosition(label, width, height, x=0, y=0):
    label.place(
        width = width,
        height = height,
        x = x,
        y = y
    )
    label.width = width
    label.height = height
    label.x = x
    label.y = y

#rimozione della webcam dallo schermo
def removeLabel(label):
    label.destroy()
    
from Utils import *
from threading import Thread
import cv2
from pygame.time import Clock
from os import environ
import pyaudio

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

class Server(object):
    def __init__(self, config_file):
        self.config_file = config_file
        #caricamento file di configurazione
        self.config = self.load_config(config_file)
        #creazione id per il server
        self.uuid = generate_uuid()
        self.hasStarted = False
        #creazione risorsa condivisa (dizionario) che conterra i client
        self.clients = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, trace):
        self.stop()
        if exc_type is not None:
            from traceback import print_exception
            print_exception(exc_type, exc_value, trace)
            
    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            from munch import munchify
            from json import load
            #caricamento configurazione e sara' accessibile con self.config.nome_config
            return munchify(load(file))
        
    #funzione di inizio servizio
    def start(self):
        if not self.hasStarted:
            print("Server starting...")
            #ricarico la configurazione nel caso sia cambiata
            self.config = self.load_config(self.config_file)
            self.hasStarted = True
            #svuoto i client
            self.clients = {}
            #creo una socket tcp per ricevere richieste di connessione
            self.sock = createTcpSocket()
            self.sock.bind((self.config.ip, self.config.port))
            self.sock.listen()
            temp_port = (self.config.port + 1) % self.config.max_port
            self.config.port = temp_port if temp_port > self.config.min_port else self.config.min_port
            self.tcp_port = self.config.port
            #creo una socket tcp per la chat testuale
            self.tcp_sock = createTcpSocket()
            self.tcp_sock.bind((self.config.ip, self.config.port))
            self.tcp_sock.listen()
            
            #faccio partire un thread per la gestione delle connessioni
            Thread(target=self.incomingHandler).start()
            print("Server started.")
    
    #funzione di chiusura del server
    def stop(self):
        if self.hasStarted:
            print("Server stopping...")
            
            if len(self.clients) > 0:
                print("Sending disconnect messages to the clients")
            
            #messaggio di disconnessione ai client
            for client_uuid, values in self.clients.items():
                connection_sock, text_sock, udp_sock, client_addr, _ = values
                print(f"Disconnecting client: {client_addr}")
                connection_sock.send(encodeMessage(self.config.transmission_protocol.disconnect, client_uuid, self.config.server_closed_message))
                print(f"Sent disconnect message to client: {client_addr}")
                connection_sock.close()
                #chiusura delle socket udp (video) e tcp (testo)
                text_sock.close()
                udp_sock.close()
                
            #svuoto client gia' presenti
            self.clients = {}
            #chiusura socket per il testo
            self.tcp_sock.close()
            #chiusura socket per le connessioni
            self.sock.close()
            self.hasStarted = False
            print("Server stopped.")
            
    def incomingHandler(self):
        while True:
            #ascolto per connessioni
            connection_sock, client_addr = self.sock.accept()
            client_uuid = generate_uuid()
            print(f"Connection from {client_addr}")
            #invio al client del suo id
            connection_sock.send(encodeMessage(self.config.transmission_protocol.update_uuid, self.uuid, client_uuid))
            print("Sent uuid")
            #invio al client dei client gia' connessi
            connection_sock.send(encodeMessage(self.config.transmission_protocol.clients, client_uuid, list(self.clients.keys())))
            print("sent other clients")
            #ricevo il nickname scelto dal client
            _, _, nickname = decodeMessage(connection_sock.recv(self.config.buffer_size))
            #invio ai client gia' connessi la richiesta di aggiungere un client
            for _, values in self.clients.items():
                c_sock, _, _, addr, _ = values
                c_sock.send(encodeMessage(self.config.transmission_protocol.add_client, client_uuid, nickname))
                print(f"Sent add-client request to client:{addr}")
            
            temp_port = (self.config.port + 1) % self.config.max_port
            self.config.port = temp_port if temp_port > self.config.min_port else self.config.min_port
            udp_port = self.config.port
            udp_sock = createUdpSocket(self.config.buffer_size)
            #creazione socket udp per il video
            udp_sock.bind((self.config.ip, udp_port))
            
            #invio specifiche (porta tcp e udp) per connettersi
            connection_sock.send(encodeMessage(self.config.transmission_protocol.tcp_udp_socket, self.uuid, (self.tcp_port, udp_port)))
            
            print(f"Connection via text with {client_addr}, nickname: {nickname}")
            text_sock, _ = self.tcp_sock.accept()
            
            message, udp_addr = udp_sock.recvfrom(self.config.buffer_size)
            print(f"UDP Connection message from {udp_addr}: {decodeMessage(message)[2]}")
                        
            #aggiunta del client e delle socket al dizionario
            self.clients[client_uuid] = (connection_sock, text_sock, udp_sock, client_addr, udp_addr)
            
            print(f"Client added: ({nickname}: {client_addr}, {udp_addr})")
            #thread che gestisce i messaggi ricevuti dal client
            Thread(target=self.clientHandler, args=(client_uuid,)).start()
    
    def clientHandler(self, client_uuid):
        connection_sock, text_sock, udp_sock, _, _ = self.clients[client_uuid]

        #processo che gestisce il testo
        Thread(target=self.tcp_text_handler, args=(text_sock,)).start()
        
        #processo che gestisce il video
        Thread(target=self.udp_handler, args=(udp_sock,)).start()
        
        #gestione della disonnessione
        while True:
            try:
                _, uuid, message = decodeMessage(connection_sock.recv(self.config.buffer_size))
                if uuid == client_uuid:
                    print("Deleting client")
                    del self.clients[client_uuid]
                    print(f"Client: {client_uuid} disconnected: {message}")
                    connection_sock.send(encodeMessage(self.config.transmission_protocol.disconnect, uuid, self.config.disconnect_message))
                    #invio ai client gia' presenti di rimuovere un client
                    for client_uuid, values in self.clients.items():
                        connection_sock, _, _, _, _ = values
                        connection_sock.send(encodeMessage(self.config.transmission_protocol.remove_client, uuid, message))
                    break
            except:
                print("Connection with client closed")
                break
        print(f"Clients: {len(self.clients)}")
    
    def tcp_text_handler(self, text_sock):
        while True:
            #ricevo il messaggio da mostrare in chat
            try:
                _, uuid, message = decodeMessage(text_sock.recv(self.config.buffer_size))
                for client_uuid, values in self.clients.items():
                    if uuid == client_uuid:
                        continue
                    _, client_text_sock, _, _, _ = values
                    #invio messaggio ai client gia' presenti
                    client_text_sock.send(encodeMessage(self.config.transmission_protocol.default, uuid, message))
            except ConnectionResetError:
                print("text closed")
                break
    
    def udp_handler(self, udp_sock):
        print("Udp handler has started")
        while True:
            #ricevo frame udp
            try:
                message, _ = udp_sock.recvfrom(self.config.buffer_size)
                protocol, uuid, frame = decodeMessage(message)
                options = {
                    self.config.transmission_protocol.normal_video: lambda: self.normal_video(uuid, frame),
                    self.config.transmission_protocol.normal_audio: lambda: self.normal_audio(uuid, frame)
                }
                if protocol == self.config.transmission_protocol.disconnect:
                    break
                #in base al protocollo esegue la funzione associata con i parametri indicati (una lambda ritorna la funzione che verra' poi chiamata)
                options[protocol]()
            except ConnectionResetError:
                print("Unable to send and receive frame")
        print("Udp handler has finished")

    def normal_video(self, uuid, frame):
        #invio del frame video ai client eccetto a quello che lo ha inviato
        try:
            for client_uuid, values in self.clients.items():
                if uuid == client_uuid:
                    continue
                _, _, udp_sock, _, addr = values
                udp_sock.sendto(encodeMessage(self.config.transmission_protocol.normal_video, uuid, frame), addr)
        except:
            print("Tried to send video frame with connection closed")
                
    def normal_audio(self, uuid, frame):
        #invio del frame audio ai client eccetto a quello che lo ha inviato
        try:
            for client_uuid, values in self.clients.items():
                if uuid == client_uuid:
                    continue
                _, _, udp_sock, _, addr = values
                udp_sock.sendto(encodeMessage(self.config.transmission_protocol.normal_audio, uuid, frame), addr)
        except:
            print("Tried to send audio frame with connection closed")

#classe client
class Client(object):
    def __init__(self, config_file):
        self.config_file = config_file
        #caricamento configurazione
        self.config = self.load_config(config_file)
        self.hasStarted = False
        #lista che contiene gli id del client 
        self.clients = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, trace):
        self.stop()
        if exc_type is not None:
            from traceback import print_exception
            print_exception(exc_type, exc_value, trace)
            
    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            from munch import munchify
            from json import load
            return munchify(load(file))
    
    def start(self, nickname):
        if not self.hasStarted:
            self.hasStarted = True
            self.client_disconnected = False
            print("Client Starting...")
            #ricaricamento configurazione
            self.config = self.load_config(self.config_file)
            #imposto il nickname
            self.nickname = nickname
            #filtri
            self.blur = False
            self.black_white = False
            self.video = True
            self.audio = True
            #richiesta di connessione al server
            self.sock = createTcpSocket()
            self.sock.connect((self.config.ip, self.config.port))
            #ricevo il mio id
            _, _, self.uuid = decodeMessage(self.sock.recv(self.config.buffer_size))
            print(f"My uuid: {self.uuid}")
            #ricevo i client gia' presenti e li aggiungo alla lista
            _, _, c = decodeMessage(self.sock.recv(self.config.buffer_size))
            self.clients = c
            #svuoto le videocamere
            self.cameras = {}
            self.position = 1
            #invio al server del nickname
            self.sock.send(encodeMessage(self.config.transmission_protocol.default, self.uuid, nickname))
            print(f"My nickname: {self.nickname}")
            _, _, ip_tuple = decodeMessage(self.sock.recv(self.config.buffer_size))
            tcp_port, udp_port = ip_tuple
            self.text_sock = createTcpSocket()
            #connessione via testo
            self.text_sock.connect((self.config.ip, tcp_port))
            self.udp_sock = createUdpSocket(self.config.buffer_size)
            # self.udp_sock.bind((self.config.ip, udp_port+len(self.clients)))
            self.udp_sock.sendto(encodeMessage(self.config.transmission_protocol.default,self.uuid, self.config.connect_message), (self.config.ip, udp_port))
            #connessione via video
            print("Client connected")
            Thread(target=self.initializeThreads, args=(udp_port,)).start()
            #aggiunga a schermo dei client gia' presenti in chiamata
            for client in self.clients:
                self.add_client(client)
            
    def stop(self):
        if self.hasStarted:
            print("Client stopping")
            #rilascio la cattura video
            self.capture.release()
            #invio al server della richiesta di disconnessione
            self.sock.send(encodeMessage(self.config.transmission_protocol.disconnect, self.uuid, self.config.disconnect_message))
            #svuoto la lista dei client
            self.clients = []
            #svuoto la lista delle videocamere
            self.cameras = {}
            #ritorno alla posizione iniziale
            self.position = 1
            #reset dei filtri
            self.blur = False
            self.black_white = False
            self.hasStarted = False
            self.video = False
            self.audio = False
            #chiusura stream audio
            self.stream.stop_stream()
            self.stream.close()
            #chiusura socket testo
            self.text_sock.close()
            #chiusura socket video
            self.udp_sock.close()
            #chiusura socket per la connessione
            self.sock.close()
            print("Client Stopped.")

    def close(self):
        if self.hasStarted:
            print("Client is being closed by the server")
            #rilascio della cattura video
            self.capture.release()
            #svuoto i client gia' presenti
            self.clients = []
            #svuoto la lista delle videocamere
            self.cameras = {}
            #ritorno alla posizione iniziale
            self.position = 1
            self.hasStarted = False
            #reset dei filtri
            self.blur = False
            self.black_white = False
            self.video = False
            self.audio = False
            #chiusura stream audio
            self.stream.stop_stream()
            self.stream.close()
            #chiusura socket testo
            self.text_sock.close()
            #chiusura sock video
            self.udp_sock.close()
            #chiusura socket per la connessione
            self.sock.close()
            print("Client stopped.")

    def initializeThreads(self, udp_port):
        print("Initializing threads")
        #thread che gestisce la connessione con il server
        self.connection_thread = Thread(target=self.connectionHandler)
        self.connection_thread.start()
        #thread per ricevere frame video
        self.recvframe_thread = Thread(target=self.recvframeHandler)
        self.recvframe_thread.start()
        #thread per inviare frame video
        self.video_thread = Thread(target=self.udp_thread, args=(udp_port,))
        self.video_thread.start()
        #thread per l'audio
        self.audio_thread = Thread(target=self.audioHandler, args=(udp_port,))
        self.audio_thread.start()
        #thread che gestisce il testo
        self.tcp_text_thread = Thread(target=self.text_thread)
        self.tcp_text_thread.start()
        print("Threads initialized")
    
    def audioHandler(self, udp_port):
        #lista che conterrà i frame audio (miei -> non leggere) (altri -> da leggere)
        self.my_audio_frames = []
        self.other_audio_frames = []
        
        #creazione stream per l'audio
        self.PyAudio = pyaudio.PyAudio()
        self.stream = self.PyAudio.open(
            format = pyaudio.paInt16,
            channels = self.config.audio_channels,
            rate = self.config.audio_rate,
            frames_per_buffer=self.config.audio_chunk,
            input = True,
            output = True
        )
        
        #thread per invio frame propri al server
        Thread(target=self.send_audio, args=(udp_port,)).start()
        #thread per la registrazione dei frame
        Thread(target=self.record_audio).start()
        #thread per l'ascolto dei frame audio
        Thread(target=self.play_audio).start()
    
    #lettura audio dalla lista dei frame a chunk
    def play_audio(self):
        while True:
            if len(self.other_audio_frames) == self.config.audio_buffer:
                while self.other_audio_frames:
                    try:
                        self.stream.write(self.other_audio_frames.pop(0), self.config.audio_chunk)
                    except:
                        print("Could not write to audio stream")
                        self.stream.close()
                        self.stream = self.PyAudio.open(
                            format = pyaudio.paInt16,
                            channels = self.config.audio_channels,
                            rate = self.config.audio_rate,
                            frames_per_buffer=self.config.audio_chunk,
                            input = True,
                            output = True
                        )
    
    #invio audio al server
    def send_audio(self, udp_port):
        while True:
            if len(self.my_audio_frames) > 0:
                try:
                    self.udp_sock.sendto(encodeMessage(self.config.transmission_protocol.normal_audio, self.uuid, self.my_audio_frames.pop(0)), (self.config.ip, udp_port))
                except:
                    print("Could not send audio")
    
    #registrazione audio e aggiunta ai frame da inviare al server
    def record_audio(self):
        while True:
            if self.audio:
                try:
                    self.my_audio_frames.append(self.stream.read(self.config.audio_chunk))
                except:
                    print("Could not read audio frame")
                    self.stream.close()
                    self.stream = self.PyAudio.open(
                        format = pyaudio.paInt16,
                        channels = self.config.audio_channels,
                        rate = self.config.audio_rate,
                        frames_per_buffer=self.config.audio_chunk,
                        input = True,
                        output = True
                    )
                
    #funzione che gestisce i frame udp in arrivo dal server
    def recvframeHandler(self):
        while True:
            #se non sono da solo non è necessario ascoltare per messaggi
            if len(self.cameras) > 1:
                try:
                    message, _ = self.udp_sock.recvfrom(self.config.buffer_size)
                    protocol, uuid, frame = decodeMessage(message)
                    #nel caso di frame audio lo giro alla funzione apposita
                    if protocol == self.config.transmission_protocol.normal_audio:
                        self.other_audio_frames.append(frame)
                        continue
                    
                    #nel caso di frame immagine aggiorno la videocamera corrispondente
                    frame = cv2.imdecode(frame, 1)
                    updateLabelImage(self.cameras[uuid], frame)
                except:
                    print("Error while receiving and updating a frame")
                    continue
    
    def connectionHandler(self):
        while True:
            try:
                print("Waiting for connection message")
                #aggiunta / rimozione client dallo schermo 
                protocol, uuid, message = decodeMessage(self.sock.recv(self.config.buffer_size))
                options = {
                    self.config.transmission_protocol.add_client : lambda: self.add_client(uuid),
                    self.config.transmission_protocol.remove_client : lambda: self.remove_client(uuid)
                }
                #nel caso di disconnessione invio un messaggio di conferma a terminale
                if protocol == self.config.transmission_protocol.disconnect:
                    print(f"Connection closed, {message}")
                    break
                else:
                    options[protocol]()
            except:
                break
    
    #funzione di aggiunta videocamera alla interfaccia grafica
    def add_client(self, client_uuid):
        print(f"adding client {client_uuid}")
        
        #ridimensionamento e calcolo posizione (andare a capo finita la riga di webcam)
        
        x = (self.position * self.config.frame_resolution.width) % self.config.label_frame.width
        y = (self.position * self.config.frame_resolution.height + self.config.frame_resolution.height) % self.config.label_frame.height
        
        if not self.position % 3:
            y = self.config.frame_resolution.height
        
        #aggiunta di un client allo schermo
        self.cameras[client_uuid] = createLabel(
            self.graphics.label_frame,
            width=self.config.frame_resolution.width,
            height=self.config.frame_resolution.height,
            x = x,
            y = y
        )
        #aggiornamento n camere e posizione ultima camera aggiunta (per il ridimensionamento)
        self.position += 1
    
    def remove_client(self, client_uuid):
        print(f"Removing client {client_uuid}")
        #rimozione dallo schermo del client
        removeLabel(self.cameras[client_uuid])
        print(f"Camera destroyed successfully")
        #rimozione dal dizionario della webcam
        del self.cameras[client_uuid]
        print(f"Client deleted successfully")
        self.client_disconnected = True
        self.position -= 1
            
    def udp_thread(self, udp_port):
        print("Hello from udp_thread")
        
        clock = Clock()
        #utilizzo di un clock per impostare gli FPS

        #acquisizione cattura video
        from platform import system
        if system() == "Windows":
            self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            self.capture = cv2.VideoCapture(0)
        
        #se non ha una webcam verra' impostato un video nero
        if not self.capture.isOpened():
            self.handle_camera_error()
        
        #finche' non riesce ad aprire una webcam
        while not self.capture.isOpened():
            clock.tick(self.config.fps)
            #cero di aprire la webcam
            if system() == "Windows":
                self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            else:
                self.capture = cv2.VideoCapture(0)
            from numpy import zeros
            #se ci sono altri client gli invio la schermata nera e ricevo i frame degli altri client
            if len(self.cameras) > 0:
                frame = zeros((self.config.frame_resolution.height, self.config.frame_resolution.width, 3))
                frame = cv2.imencode(self.config.format, frame, (cv2.IMWRITE_JPEG_QUALITY, self.config.quality))[1]
                self.udp_sock.sendto(encodeMessage(self.config.transmission_protocol.normal_video, self.uuid, frame), (self.config.ip, udp_port))
        
        while self.capture.isOpened():
            clock.tick(self.config.fps)
            #lettura del frame
            _, frame = self.capture.read()
            #ridimensionamento
            frame = cv2.resize(frame, (self.config.label_frame.width, self.config.label_frame.height))
            #trasformazione a RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            #applico i filtri
            if self.blur:
                frame = cv2.GaussianBlur(frame, (self.config.blur_ksize[0], self.config.blur_ksize[1]), cv2.BORDER_DEFAULT)
            
            if self.black_white:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            if not self.video:
                from numpy import zeros_like
                frame = zeros_like(frame)
            
            # se non ci sono altri client la webcam rimane full screen
            if len(self.cameras) <= 1:
                #se non e' gia' presente aggiungo la webcam allo schermo
                if not self.uuid in self.cameras.keys():
                    self.cameras[self.uuid] = createLabel(
                        frame=self.graphics.label_frame,
                        width=self.config.label_frame.width,
                        height=self.config.label_frame.height
                    )
                #se un client si a' disconnesso ritorno full screen
                if self.client_disconnected:
                    updateLabelPosition(
                        self.cameras[self.uuid],
                        width=self.config.label_frame.width,
                        height=self.config.label_frame.height
                    )
                    self.client_disconnected = False
                updateLabelImage(self.cameras[self.uuid], frame)
            else:
                #ridimensionamento webcam per far stare gli altri client
                frame = cv2.resize(frame, (self.config.frame_resolution.width, self.config.frame_resolution.height))
                updateLabelImage(self.cameras[self.uuid], frame)
                updateLabelPosition(
                    self.cameras[self.uuid],
                    width=self.config.frame_resolution.width,
                    height=self.config.frame_resolution.height,
                )
                
            #invio frame al server sendto
            frame = cv2.imencode(self.config.format, frame, (cv2.IMWRITE_JPEG_QUALITY, self.config.quality))[1]
            try:
                self.udp_sock.sendto(encodeMessage(self.config.transmission_protocol.normal_video, self.uuid, frame), (self.config.ip, udp_port))
            except OSError:
                print("Unable to send frame")

        try:
            #invio al server il messaggio di disconnessione
            self.udp_sock.sendto(encodeMessage(self.config.transmission_protocol.disconnect, self.uuid, self.config.disconnect_message), (self.config.ip, udp_port))
        except OSError:
            pass
        self.capture.release()

    def send_text(self, text):
        #invio testo al server e aggiunta alla chat
        try:
            self.text_sock.send(encodeMessage(self.config.transmission_protocol.default, self.uuid, text))
        except:
            print("Unable to send text")
        self.graphics.add_to_chat(text)
    
    def text_thread(self):
        while True:
            try:
                #ricevo il testo dal server e lo aggiungo alla chat
                _, _, message = decodeMessage(self.text_sock.recv(self.config.buffer_size))
                self.graphics.add_to_chat(message)
            except:
                break
    
    def addGraphics(self, graphics):
        #carimamento interfaccia grafica
        self.graphics = graphics
    
    #se la webcam non si carica allora sara' un video nero
    def handle_camera_error(self):
        if len(self.cameras) == 0:
            self.cameras[self.uuid] = createLabel(
                frame=self.graphics.label_frame,
                width=self.config.label_frame.width,
                height=self.config.label_frame.height
            )
        else:
            self.cameras[self.uuid] = createLabel(
                frame=self.graphics.label_frame,
                width=self.config.frame_resolution.width,
                height=self.config.frame_resolution.height
            )
    
    #funzioni per l'applicazione degli effetti alla webcam
    def switch_video(self):
        self.video = not self.video
    
    def switch_blur(self):
        self.blur = not self.blur
    
    def switch_black_white(self):
        self.black_white = not self.black_white
    
    #abilitazione o meno dell'acquisizione audio
    def switch_audio(self):
        self.audio = not self.audio
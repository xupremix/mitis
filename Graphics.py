from Utils import *
import tkinter as tk

#classe per l'interfaccia grafica
class Graphics():
    def __init__(self):
        self.uuid = generate_uuid()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, trace):
        if exc_type is not None:
            from traceback import print_exception
            print_exception(exc_type, exc_value, trace)
    
    #interfaccia server
    def server_window(self, server):
        self.window = tk.Tk()
        self.__generate_server_widgets(server)
        self.window.mainloop()
    
    #interfaccia client
    def client_window(self, client):
        self.window = tk.Tk()
        self.__generate_client_widgets(client)
        self.window.mainloop()
    
    def __generate_server_widgets(self, server):
        #window specifics
        self.window.title(server.config.window_title)
        self.window.eval(
            server.config.center_window
        )
        self.window.geometry(f"{server.config.server_resolution.width}x{server.config.server_resolution.height}")
        self.window.resizable(False, False)
        self.window.iconphoto(False, tk.PhotoImage(file=server.config.window_icon))
        #start button (per far partire il server)
        start_button = tk.Button(
            self.window,
            width=server.config.start_button.width,
            height=server.config.start_button.height,
            text=server.config.start_button.text,
            command = server.start
        )
        start_button.grid(
            row=server.config.start_button.row,
            column=server.config.start_button.column
        )
        #stop button (per chiudere il server)
        stop_button = tk.Button(
            self.window,
            width=server.config.stop_button.width,
            height=server.config.stop_button.height,
            text=server.config.stop_button.text,
            command = server.stop
        )
        stop_button.grid(
            row=server.config.stop_button.row,
            column=server.config.stop_button.column
        ) 
    
    def __generate_client_widgets(self, client):
        #window specifics
        self.window.title(client.config.window_title)
        self.window.eval(
            client.config.center_window
        )
        self.window.geometry(f"{client.config.connection_frame.width}x{client.config.connection_frame.height}")
        self.window.resizable(False, False)
        self.window.iconphoto(False, tk.PhotoImage(file=client.config.window_icon))
        #frame per la visione delle webcam (con testo e filtri)
        self.video_frame = self.__create_video_frame(client)
        #frame per connettersi al server (ed inserire il nickname)
        self.connection_frame = self.__create_connection_frame(client)
        #frame che conterrra' le webcam
        self.label_frame = self.__create_label_frame(client)
        #chat testuale
        self.chat_area = self.__create_chat_area(client)
        #inserimento testo nella chat
        self.text_entry = self.__create_text_entry(client)
        #pulsanti per i filtri
        self.blur_button = self.__create_blur_button(client)
        self.black_white_button = self.__create_black_white_button(client)
        self.video_button = self.__create_video_button(client)
        self.audio_button = self.__create_audio_button(client)
        #aggiunta interfaccia grafica al client
        client.addGraphics(self)
    
    def __create_audio_button(self, client):
        icon = tk.PhotoImage(file = client.config.audio_button.icon)
        audio_button = tk.Button(
            self.video_frame,
            image = icon,
            command=client.switch_audio
        )
        audio_button.image = icon
        audio_button.place(
            width=client.config.audio_button.width,
            height=client.config.audio_button.height,
            x=int(client.config.label_frame.width / 2 +  2 * client.config.black_white_button.width + 3 * client.config.spacing),
            y=client.config.label_frame.height
        )
        audio_button["border"] = "0"
        return audio_button
    
    def __create_video_button(self, client):
        icon = tk.PhotoImage(file = client.config.video_button.icon)
        video_button = tk.Button(
            self.video_frame,
            image = icon,
            command=client.switch_video
        )
        video_button.image = icon
        video_button.place(
            width=client.config.video_button.width,
            height=client.config.video_button.height,
            x=int(client.config.label_frame.width / 2 + client.config.black_white_button.width + 2 * client.config.spacing),
            y=client.config.label_frame.height
        )
        video_button["border"] = "0"
        return video_button
    
    def __create_black_white_button(self, client):
        icon = tk.PhotoImage(file = client.config.black_white_button.icon)
        black_white_button = tk.Button(
            self.video_frame,
            image = icon,
            command=client.switch_black_white
        )
        black_white_button.image = icon
        black_white_button.place(
            width=client.config.black_white_button.width,
            height=client.config.black_white_button.height,
            x=client.config.label_frame.width / 2 + client.config.spacing,
            y=client.config.label_frame.height
        )
        black_white_button["border"] = "0"
        return black_white_button
    
    def __create_blur_button(self, client):
        icon = tk.PhotoImage(file = client.config.blur_button.icon)
        blur_button = tk.Button(
            self.video_frame,
            image = icon,
            command=client.switch_blur
        )
        blur_button.image = icon
        blur_button.place(
            width=client.config.blur_button.width,
            height=client.config.blur_button.height,
            x=client.config.label_frame.width / 2 - client.config.blur_button.width,
            y=client.config.label_frame.height
        )
        blur_button["border"] = "0"
        return blur_button
    
    def __create_text_entry(self, client):
        text_entry = tk.Entry(
            self.video_frame,
            font = client.config.nickname_entry.font
        )
        text_entry.insert(
            0, client.config.text_entry.placeholder_text
        )
        text_entry.place(
            width = client.config.video_frame.width - client.config.label_frame.width,
            height = client.config.exit_button.height,
            x = client.config.label_frame.width,
            y = client.config.label_frame.height
        )
        text_entry.bind(
            "<Button-1>", lambda _: self.__add_placeholder_text(text_entry)
        )
        text_entry.bind(
            "<FocusOut>", lambda _: self.__remove_placeholder_text(text_entry, client.config.text_entry.placeholder_text)
        )
        text_entry.bind(
            "<KeyPress-Return>", lambda _: self.__send_text(client, text_entry)
        )
        return text_entry
    
    def __send_text(self, client, text_entry):
        text:str = text_entry.get().strip()
        if not text or text_entry.get().strip() == client.config.text_entry.placeholder_text:
            return
        self.window.update_idletasks()
        client.send_text(client.nickname + ": " + text)
        self.__add_placeholder_text(text_entry)
    
    def __create_chat_area(self, client):
        import tkinter.scrolledtext as scrolledtext
        chat_area = scrolledtext.ScrolledText(
            self.video_frame,
            wrap = tk.WORD
        )
        chat_area.config(
            state="disabled"
        )
        chat_area.place(
            width = client.config.video_frame.width - client.config.label_frame.width,
            height = client.config.label_frame.height,
            x = client.config.label_frame.width,
            y = 0
        )
        return chat_area
    
    def __create_label_frame(self, client):
        label_frame = tk.Frame(
            self.video_frame,
            bg="cyan"
        )
        label_frame.place(
            width=client.config.label_frame.width,
            height=client.config.label_frame.height,
        )
        return label_frame
    
    def __add_placeholder_text(self, entry):
        entry.delete(0, "end")
    
    def __remove_placeholder_text(self, entry, text):
        entry.delete(0, "end")
        entry.insert(
            0, text
        )
    
    def __connect(self, client, nickname_entry):
        if not nickname_entry.get().strip() or nickname_entry.get().strip() == client.config.placeholder_text:
            return
        self.window.update_idletasks()
        self.window.geometry(
            f"{client.config.video_frame.width}x{client.config.video_frame.height}"
        )
        self.window.eval(
            client.config.center_window
        )
        self.video_frame.tkraise()
        client.start(nickname_entry.get())
    
    def __disconnect(self, client):
        self.window.update_idletasks()
        self.window.geometry(
            f"{client.config.connection_frame.width}x{client.config.connection_frame.height}"
        )
        self.window.eval(
            client.config.center_window
        )
        self.connection_frame.tkraise()
        client.stop()
    
    def __create_video_frame(self, client):
        video_frame = tk.Frame(
            self.window,
            width=client.config.video_frame.width,
            height=client.config.video_frame.height
        )
        video_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        
        exit_button = tk.Button(
            video_frame,
            text=client.config.exit_button.text,
            font=client.config.exit_button.font,
            justify=client.config.exit_button.justify,
            command = lambda: self.__disconnect(client)
        )
        exit_button.place(
            width=client.config.exit_button.width,
            height=client.config.exit_button.height,
            x = 0,
            y=client.config.video_frame.height - client.config.exit_button.height
        )
        return video_frame
    
    def __create_connection_frame(self, client):
        connection_frame = tk.Frame(
            self.window,
            width=client.config.connection_frame.width,
            height=client.config.connection_frame.height
        )
        connection_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        
        #nickname entry
        nickname_entry = tk.Entry(
            connection_frame,
            font=client.config.nickname_entry.font,
            justify=client.config.nickname_entry.justify
        )
        nickname_entry.insert(
            0, client.config.placeholder_text
        )
        nickname_entry.place(
            width=client.config.nickname_entry.width,
            height=client.config.nickname_entry.height,
            x=client.config.nickname_entry.padding_left,
            y=int(client.config.connection_frame.height / 2 - client.config.nickname_entry.height)
        )
        nickname_entry.bind(
            "<Button-1>", lambda _: self.__add_placeholder_text(nickname_entry)
        )
        nickname_entry.bind(
            "<FocusOut>", lambda _: self.__remove_placeholder_text(nickname_entry, client.config.placeholder_text)
        )
        nickname_entry.bind(
            "<KeyPress-Return>", lambda _: self.__connect(client, nickname_entry)
        )
        #connect button
        connect_button = tk.Button(
            connection_frame,
            text=client.config.connect_button.text,
            font=client.config.connect_button.font,
            command=lambda: self.__connect(client, nickname_entry)
        )
        connect_button.place(
            width=client.config.connect_button.width,
            height=client.config.connect_button.height,
            x=client.config.nickname_entry.padding_left + client.config.nickname_entry.width + client.config.connect_button.padding_right,
            y=int(client.config.connection_frame.height / 2 - client.config.nickname_entry.height)
        )
        return connection_frame
    
    def add_to_chat(self, text):
        self.chat_area.config(
            state="normal"
        )
        self.chat_area.insert(
            "end", text + "\n"
        )
        self.chat_area.yview(
            "end"
        )
        self.chat_area.config(
            state="disabled"
        )
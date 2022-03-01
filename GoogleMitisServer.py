from Graphics import Graphics
from Network import Server

config_file = "server_config.json"

def main():
    global config_file
    with Server(config_file=config_file) as server:
        with Graphics() as graphics:
            graphics.server_window(server)

if __name__ == '__main__':
    main()
    
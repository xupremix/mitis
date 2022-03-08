from Graphics import Graphics
from Network import Client

config_file = "client_config.json"

def main():
    global config_file
    with Client(config_file=config_file) as client:
        with Graphics() as graphics:
            graphics.client_window(client)

if __name__ == '__main__':
    main()

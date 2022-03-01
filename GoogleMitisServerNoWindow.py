from Network import Server

config_file = "server_config.json"

def main():
    global config_file
    with Server(config_file=config_file) as server:
        server.start()
        while server.hasStarted:
            pass

if __name__ == '__main__':
    main()
    
import PySimpleGUI as sg
import socket
import threading
import warnings

warnings.filterwarnings("ignore")
sg.theme("DarkTeal5")
sg.set_options(font=("Helvetica", 13))
layout = [[sg.Button("Connect", key="-CONNECT-", size=(30, 1)),
           sg.Button("Stop", key="-STOP-", disabled=True, size=(30, 1))],
          [sg.Text("Host: X.X.X.X", key="-HOST-", size=(30, 1)),
           sg.Text("Port: X.X.X.X", key="-PORT-", size=(30, 1))],
          [sg.Text("Client List")], [sg.Multiline(size=(60, 15),
                                                  key="-CLIENTS-",
                                                  disabled=True)]]

window = sg.Window("Server", layout, size=(400, 275))

server = None
HOST_ADDR = "127.0.0.1"
HOST_PORT = 8080
client_name = " "
clients = []
clients_names = []


def start_server():
    global server, HOST_ADDR, HOST_PORT, window
    window["-CONNECT-"].update(disabled=True)
    window["-STOP-"].update(disabled=False)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST_ADDR, HOST_PORT))
    server.listen(5)

    thread = threading.Thread(target=accept_clients, args=(server, ))
    thread.start()

    window["-HOST-"].update("Host: " + HOST_ADDR)
    window["-PORT-"].update("Port: " + str(HOST_PORT))


def stop_server():
    global server, clients, clients_names, window
    window["-CONNECT-"].update(disabled=False)
    window["-STOP-"].update(disabled=True)

    for c in clients:
        c.close()

    clients.clear()
    clients_names.clear()

    if server:
        server.close()
        server = None
    exit()


def accept_clients(the_server):
    global clients, window
    try:
        while True:
            client, addr = the_server.accept()
            clients.append(client)

            thread = threading.Thread(target=send_receive_client_message,
                                      args=(client, ))
            thread.start()
    except ConnectionAbortedError:
        exit()


def send_receive_client_message(client_connection):
    global server, client_name, clients, clients_names, window

    client_name = client_connection.recv(4096).decode()
    welcome_msg = "Welcome " + client_name + "! Press stop to quit." + ('\n' if len(clients_names) == 0 else '')
    client_connection.send(welcome_msg.encode())

    if len(clients_names) != 0:
        if len(clients_names) == 1:
            allclients_msg = '\n'+clients_names[0] + ' is in this chat.\n'
        elif len(clients_names) == 2:
            allclients_msg = '\n'+' & '.join(clients_names)
            allclients_msg = allclients_msg + ' are in this chat.\n'
        else:
            allclients_msg = '\n' + ', '.join(
                clients_names[:len(clients_names) - 1])
            allclients_msg = allclients_msg + ' & ' + \
                             clients_names[len(clients_names) - 1] + \
                             ' are in this chat.\n'

        client_connection.send(allclients_msg.encode())

    clients_names.append(client_name)

    update_client_names_display(clients_names)

    for client in clients:
        if client != client_connection:
            server_msg = client_name + ' has joined the chat!'
            client.send(server_msg.encode())

    try:
        while True:
            data = client_connection.recv(4096).decode()

            if not data:
                break

            client_msg = data

            idx = get_client_index(clients, client_connection)
            sending_client_name = clients_names[idx]

            for c in clients:
                if c != client_connection:
                    server_msg = str(sending_client_name + "->" + client_msg)
                    c.send(server_msg.encode())
    except OSError:
        exit()

    idx = get_client_index(clients, client_connection)

    leaving_msg = clients_names[idx] + ' has left the chat!'

    del clients_names[idx]
    del clients[idx]

    for client in clients:
        server_msg = leaving_msg
        client.send(server_msg.encode())

    client_connection.close()

    update_client_names_display(clients_names)


def get_client_index(client_list, curr_client):
    idx = 0
    for conn in client_list:
        if conn == curr_client:
            break
        idx = idx + 1

    return idx


def update_client_names_display(name_list):
    window["-CLIENTS-"].update("\n".join(name_list))


while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    if event == "-CONNECT-":
        start_server()
    elif event == "-STOP-":
        stop_server()

window.close()

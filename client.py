import PySimpleGUI as sg
import socket
import threading
import warnings

warnings.filterwarnings("ignore")

sg.theme("DarkTeal5")
sg.set_options(font=("Helvetica", 13))

HOST_ADDR = "127.0.0.1"
HOST_PORT = 8080
MAX_BUFFER_SIZE = 4096

msgs = []

layout = [
    [sg.Text("Name:"), sg.InputText(key="-NAME-", size=(30, 1)),
     sg.Button("Connect", key="-CONNECT-", size=(15, 1)),
     sg.Button("Stop", key="-STOP1-", size=(15, 1))],
    [sg.Multiline(key="-DISPLAY-", size=(70, 23), disabled=True,
                  autoscroll=True)],
    [sg.InputText(key="-MESSAGE-", size=(55, 1)),
     sg.Button("Send", key="-SEND-", bind_return_key=True, size=(15, 1))],
]

window = sg.Window("Client", layout, size=(600, 425))

username = ""
client = None

def connect():
    global username, client
    if len(values["-NAME-"]) < 1:
        sg.popup_error("Enter a valid name.")
    else:
        username = values["-NAME-"]
        connect_to_server(username)

def connect_to_server(name):
    global client, HOST_PORT, HOST_ADDR
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST_ADDR, HOST_PORT))
        client.send(name.encode())

        window["-NAME-"].update(disabled=True)
        window["-CONNECT-"].update(disabled=True)
        window["-MESSAGE-"].update(disabled=False)

        thread = threading.Thread(target=receive_message_from_server,
                                  args=(client,))
        thread.start()

        # Update the display after connecting
        msgs.append(f'Connected as: {name}')
        text = "\n".join(msgs)
        window["-DISPLAY-"].update(disabled=False)
        # window["-DISPLAY-"].update(f'{text}\n')

    except Exception as e:
        sg.popup_error(
            "Cannot connect to host: " + HOST_ADDR + " on port: " + str(
                HOST_PORT) + ". Server may be unavailable. Try again later.")


def receive_message_from_server(sck):
    try:
        while True:
            from_server = sck.recv(MAX_BUFFER_SIZE).decode()

            if not from_server:
                break

            if '->' in from_server:
                from_server = from_server.replace('->', ' -> ')

            msgs.append(from_server)
            text = "\n".join(msgs)
            window["-DISPLAY-"].update(f'{text}\n')
    except OSError:
        exit()

    sck.close()
    window.close()

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break
    elif event == "-CONNECT-":
        connect()
    elif event == "-STOP1-":
        if client:
            client.close()
        window.close()
        exit()
    elif event == "-SEND-":
        msg = values["-MESSAGE-"].replace('\n', '')
        if msg:
            client.send(msg.encode())
            msgs.append('You -> '+msg)
            text = "\n".join(msgs)
            window["-DISPLAY-"].update(f'{text}\n')
            window["-MESSAGE-"].update(value="")
            window["-MESSAGE-"].set_focus()

window.close()

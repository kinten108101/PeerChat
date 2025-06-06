from socket import socket as make_socket
from lib.promise import Promise
from threading import Thread

class Request():
  def __init__(self, address, message):
    self.address = address
    self.message = message

class Response():
  def __init__(self, client_connection):
    self.client_connection = client_connection

  def write(self, content):
    self.client_connection.sendall(content.encode())

  def close(self):
    return self.client_connection.close()

class Server():
  def __init__(self, address):
    self.address = address

  def work_listen(self, cancellable, on_connection):
    address = self.address
    socket = make_socket()
    socket.bind(address)
    socket.listen(1)
    while cancellable.is_set():
      try:
        client = socket.accept()
        def _a71(client, _):
          client_conn, client_address = client
          request = client_conn.recv(1024)
          request = request.decode()
          print(f"listen: received \"{request}\"")
          request = Request(client_address, request)
          response = Response(client_conn)
          on_connection(request, response)
        Thread(target=_a71, args=(client, None)).start()
      except TimeoutError:
        pass
    socket.close()

  def listen_async(self, cancellable):
    return Promise(target=self.work_listen, args=[cancellable])

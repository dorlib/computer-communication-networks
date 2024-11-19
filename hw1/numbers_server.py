import math
import re
import select
import sys
from socket import *

DEFAULT_PROT = 1337
HOST = 'localhost'


def fetch_users(path):
    """ Fetches users from a file and returns dictionary of user names and their passwords
    :parameter
    path (str) : path to file
    :return
    result (dict) : dictionary of user names and their passwords"""
    users = {}
    with open(path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = re.split(r'\s+', line)  # Split on any whitespace
                if len(parts) == 2:
                    username, password = parts
                    users[username] = password
                else:
                    print(f"Warning: Skipping malformed line: {line}")

    return users


def authenticate(client_socket, users):
    """Authenticate a client."""
    while True:  # Loop until authentication succeeds
        # Wait for the username and password from the client
        username = client_socket.recv(1024).decode().strip()
        password = client_socket.recv(1024).decode().strip()

        # Authenticate the user
        if username in users and password == users[username]:
            client_socket.send(f"Hi {username}, good to see you.\n".encode())
            return username
        else:
            client_socket.send(b"Failed to login. Please try again.\n")


def calculate(x, y, op):
    """return the result of x op y"""
    try:
        x, y = int(x), int(y)
        if op == "/":
            result = x / y
        elif op == "+":
            result = x + y
        elif op == "*":
            result = x * y
        elif op == "^":
            result = x ** y
        elif op == "-":
            result = x - y
        if isinstance(result, int) and abs(result) > 2 ** 31 - 1:
            return "error: result is too big"
        return f"response: {result}"
    except OverflowError:
        return "error: result is too big"
    except ValueError:
        return "error: invalid input"


def find_max(numbers):
    """find the maximum between the numbers"""
    if len(numbers) == 0:
        return None

    if isinstance(len(numbers), int) and abs(len(numbers)) > 2 ** 31 - 1:
        return "error: result is too big"

    for number in numbers:
        if isinstance(number, int) and abs(number) > 2 ** 31 - 1:
            return "error: result is too big"
    max_number = max(numbers)


    return f"the maximum is {max_number}"


def quit_program(client_socket):
    """quit the program"""
    client_socket.send(b"Goodbye.\n")
    client_socket.close()
    return 'QUIT'


def find_factors(number):
    """Find the distinct prime factors of a given number."""
    x = int(number)
    
    if isinstance(x, int) and abs(x) > 2 ** 31 - 1:
        return "error: result is too big"
    
    factors = set()  # Use a set to store distinct factors
    for i in range(2, int(math.sqrt(x)) + 1):
        while x % i == 0:
            factors.add(i)  # Add the factor to the set (automatically handles duplicates)
            x //= i
    
    if x > 1:
        factors.add(x)  # Add the remaining prime factor if x > 1

    # Return the distinct prime factors as a comma-separated string
    return f"The distinct prime factors of {number} are: {', '.join(map(str, sorted(factors)))}"


def validate_command(command, parts):
    """validate a command"""
    return len(parts) < 2


def split_expression(expression):
    # Replace operators with space-operator-space
    for op in ['*', '+', '-', '/', '(', ')', '^']:
        expression = expression.replace(op, f' {op} ')
    # Split the expression by spaces
    return expression.split()


def handle_command(client_socket, command):
    """handle a command"""
    quit_flag = 0
    response = ""
    parts = command.split(':')
    if validate_command(command, parts):
        client_socket.send(b"error: invalid command format")
        quit_flag = 1
        return quit_flag

    cmd, args = parts[0], parts[1].strip()
    if cmd == 'quit':
        quit_program(client_socket)
    elif cmd == 'factors':
        response = find_factors(args)
    elif cmd == 'max':
        numbers = list(map(int, args.strip("()").split()))
        print(numbers)
        response = find_max(numbers)
    elif cmd == 'calculate':
        x, op, y = split_expression(args)
        response = calculate(x, y, op)
    else:
        response = "error: unrecognized command"
        quit_flag = 1
    client_socket.send(f"{response}".encode())
    return quit_flag


def main():
    if len(sys.argv) < 2:
        print("Usage: numbers_server.py users_file [port]")
        return

    users_file = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PROT
    users = fetch_users(users_file)

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind((HOST, port))
    server_socket.listen(5)
    print(f"Server listening on port {port}...")

    client_sockets = {}

    while True:
        try:
            read_sockets, _, _ = select.select([server_socket] + list(client_sockets.keys()), [], [])
        except TypeError as e:
            print(f"TypeError in select.select: {e}")
            continue

        for sock in read_sockets:
            if sock == server_socket:
                # Accept new client connection
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")

                # Authenticate immediately upon connection
                username = authenticate(client_socket, users)
                if username:
                    client_sockets[client_socket] = username  # Add to client sockets only after successful authentication
            else:
                # Handle commands from authenticated clients
                try:
                    command = sock.recv(1024).decode().strip()
                    if command:
                        if command == 'quit':
                            del client_sockets[sock]
                            sock.send(b"Goodbye!\n")
                        else:
                            quit_flag = handle_command(sock, command)
                            if quit_flag: # disconnect user
                                 del client_sockets[sock]
                except ConnectionResetError:
                    print("Connection closed by client.")
                    del client_sockets[sock]


if __name__ == "__main__":
    main()

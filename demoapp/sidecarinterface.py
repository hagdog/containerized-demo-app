import json
import os
import socket
from time import sleep

from sidecarmediator.restcontract import MessageKey
from demoapp.configuredlogger import SeerLogger

log = SeerLogger(__name__, import_level=True)


class SidecarNotifier:
    """Opens and sends messages to a file-based socket to provide the system
    under test a systemd notification-compatible interface.

    For this demonstration app, the MAINPID is always 1
    since the seer application is the primary process in a Docker container.

    See the testassitant and sidecar documentation
    for details on the dbus emulation on the socket interface.

    Args:
        socket_file_path (str): The socket file used to communicate with
            a sidecar container that is joined with a system-under-test
            (SUT) container.
        messages_path (str):
            The location of the file in which the messages
            to be sent located
    """

    def __init__(self, socket_file_path, messages_path=None):
        """
        Args"
            socket_file (str):
                The location of the file based socket to create and listen on
        """
        self._socket_file_path = socket_file_path
        self._message_file_path = messages_path

    def send_injected_messages(self):
        log.debug("Loading injected messages.")
        injected_messages = self._load_message_file()
        assert (
            injected_messages is not None
        ), "Could not load or parse injected messages."

        log.debug("Connecting to dbus_connection on sidecar.")
        dbus_connection = self._connect_to_sidecar()

        last_ready_val = False
        last_PID_val = None
        if dbus_connection:
            log.debug("Connected to dbus_connection on sidecar.")

            # send messages read from the config file
            msg_number = 1
            for msg in injected_messages["messages"]:
                lines_of_message = msg["numberoflines"]
                log.debug(f"message has {lines_of_message} lines")
                num_lines = 0
                message = ""

                for line in msg["lines"]:
                    msg_key = line["key"]
                    msg_val = line["value"]
                    message = message + f"{msg_key}={msg_val}"
                    if num_lines < (lines_of_message - 1):
                        message = message + f"\n"
                    num_lines = num_lines + 1

                    if msg_key == MessageKey.ready:
                        last_ready_val = msg_val
                    if (
                        msg_key == MessageKey.mainpid
                        or msg_key == MessageKey.injected_pid
                    ):
                        last_PID_val = msg_val

                encoded_message = message.encode()
                log.debug(f"Sending {msg_number} message {encoded_message}")
                dbus_connection.sendall(encoded_message)
                msg_number = msg_number + 1
                sleep(int(msg["sleepinseconds"]))

            # Clean up after sending all messages.
            dbus_connection.close()
            log.debug(f"Socket closed at {self._socket_file_path}")
            # The contents have been consumed and should not be used again.
            os.remove(self._message_file_path)
            log.debug(
                f"Removed injected messages file: {self._message_file_path}"
            )

            return last_ready_val, last_PID_val

        return False, 0

    def send_ready_update(self, ready=False, pid=0):
        # Convert the ready indication to an integer for sidecar compatibility.
        state = 1 if ready else 0

        log.debug("Connecting dbus_connection on sidecar.")
        dbus_connection = self._connect_to_sidecar()
        if dbus_connection:
            log.debug("Connected to dbus_connection on sidecar.")
            # READY and MAINPID are keys used by the sidecar.
            message = f"READY={state}"
            if pid:
                message += f"\nMAINPID={pid}"

            try:
                log.debug(f"Sending message dbus socket: {message}.")
                dbus_connection.sendall(message.encode())
                dbus_connection.close()
                return True
            except Exception as e:
                log.error(f"Failed to send message to sidecar: {e}.")
        else:
            log.error(
                "Failed to connect to "
                "dbus_connection on sidecar. Unknown error."
            )
        return False

    def _connect_to_sidecar(self):
        """Open the file-based socket for systemd update notifications."""
        echo_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        # Connect the socket to the port where the sidecar is listening
        log.debug(f"Connecting to Socket File: {self._socket_file_path}")
        timeout = 30
        num_seconds = 0
        nap_duration = 2
        last_error = ""
        while num_seconds < timeout:
            try:
                echo_socket.connect(self._socket_file_path)
                log.debug(
                    f"Socket connected at {self._socket_file_path} "
                    f"after {num_seconds} seconds"
                )
                return echo_socket
            except socket.error as error:
                last_error = error
                sleep(nap_duration)
                num_seconds += nap_duration

        log.error(
            "Socket connection timed out "
            f"at {num_seconds} seconds: {last_error}."
        )
        return None

    def _load_message_file(self):
        log.debug(f"Loading message file {self._message_file_path}")
        try:
            with open(self._message_file_path, "r") as fp:
                messages = json.load(fp)
            log.debug(f"{self._message_file_path} loaded: {messages}")
        except Exception as e:
            messages = None
            log.error(
                "Could not the load or parse message file "
                f"'{self._message_file_path}': {e}"
            )
        return messages

    @property
    def has_pending_injections(self):
        return os.path.exists(self._message_file_path)

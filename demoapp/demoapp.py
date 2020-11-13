"""
This script is the entry point for the seer application. Being the entry
point in a Docker container, this script run as the primary process
in the Docker container.

As the primary process, this script, and hence the app, has the PID of 1.
Docker forwards all signals to this process.

Upon execution, a seer is incarnated, i.e. a Seer instance is created,
a connection is made to the sidecar socket, and the application starts
a REST server that provides the service's public interface.

Note: Error checking in this demonstration module is minimal. The code is
simplified for instructional purposes rather than for robust operation.
"""
import argparse
import os
import sys
import threading
from collections import deque

from demoapp.appinterface import RestServer
from demoapp.configuredlogger import SeerLogger
from demoapp.seerpsyche import Seer

log = SeerLogger(__name__, import_level=True)


def main(socket_file, rest_port, memories_file, messages_path):
    # The seer is a stateful object at the core of this application.
    seer = Seer(
        memories_file=memories_file,
        messages_path=messages_path,
        pid=os.getpid(),
        sidecar_socket_file=socket_file,
    )
    # Threads do not have exit values.
    # Use a simple queue to tally errors from within the thread.
    rest_results = deque()
    rest_server = RestServer(
        port=rest_port, seer=seer, result_queue=rest_results
    )

    # The REST server is difficult to terminate if in the main thread.
    rest_thread = threading.Thread(
        name="REST server", target=rest_server.listen
    )
    rest_thread.setDaemon(True)
    rest_thread.start()
    rest_thread.join()
    log.debug(f"REST thread terminated. {__file__} is exiting")

    return interpret_rest_result(rest_results)


def interpret_rest_result(queue):
    # Relocated logic to simplify the main function.
    try:
        # Only one thread pushed only one time.
        return queue.pop()
    except IndexError:
        # If there is nothing in the queue,
        # the shutdown did not execute properly.
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "demoapp is a simple implementation of a "
            "system under test (SUT) service that can be used with the "
            "sidecar container found in this Git repository."
        ),
        prog="demoapp",
    )
    parser.add_argument(
        "--rest-port",
        dest="rest_listener_port",
        default=8000,
        type=int,
        help="The port to open the REST-ful test point interface on.",
    )
    parser.add_argument(
        "--socket-file",
        dest="notification_socket_file_path",
        default="/tmp/testassitant/system_under_test_socket",
        help="The location to open the file based socket "
        "for system notifications.",
    )
    parser.add_argument(
        "--memories-file",
        dest="memories_file",
        default="/tmp/testassitant/memories.pickle",
        help="A location for a file that retains the seer's wisdom "
        "across container stop and start operations.",
    )
    args = parser.parse_args()

    # The default path is used here in the mocksystemundertest container
    # and also by the pytest scripts in the testdriver container.
    default_injected_messages_path = "/injected_messages.json"

    sys.exit(
        main(
            args.notification_socket_file_path,
            args.rest_listener_port,
            args.memories_file,
            messages_path=default_injected_messages_path,
        )
    )

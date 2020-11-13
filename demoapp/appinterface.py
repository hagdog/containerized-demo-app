import http.server
import json
import requests
import socketserver

from demoapp.configuredlogger import SeerLogger

log = SeerLogger(__name__, import_level=True)

"""The service interface provides access to the application.
"""


class RestServer:
    """The seer sits in a in a kiosk in a mall waiting all day to share
    his/her wisdom.  A sign on the kiosk says "Seer Answers $5."
    An active display monitors his vitals and reports if the seer is
    waking, available, distracted, or sleeping. The active display also
    monitors and reports the seer's current perspective.

    In geek speak, this class uses the socketserver module to implement
    a rudimentary REST interface for the seer application.

    Args:
        port (int): The port on which to listen for REST requests.
        seer (Seer): The seer provides data for the REST request responses.
        result_queue (collections.deque): A queue used to store the results
            of the request to shut down the HTTP server.
    """

    def __init__(self, port, seer, result_queue):
        self.port = port
        self.seer = seer
        self.seer.register_service_interface_shutdown(self.shutdown)
        self._result_queue = result_queue

    def shutdown(self):
        """Shutdown the http server to terminate the REST thread."""
        log.info("REST server is stopping.")
        try:
            self._httpd.shutdown()
            self._result_queue.append(0)
            log.debug("Successful shutdown of httpd listener.")
        except Exception as e:
            log.error(f"Could not shut down the httpd listener: {e}")
            self._result_queue.append(1)

    def listen(self):
        """Open the network based socket and listen for REST requests."""

        log.info(f"REST server started.")

        def wrap_handler(*args):
            # Pass the system under test state instance into the handler
            RestRequestHandler(self.seer, *args)

        with socketserver.TCPServer(("", self.port), wrap_handler) as httpd:
            log.debug(f"REST test point listening on port {self.port}")
            self._httpd = httpd
            httpd.serve_forever()


class RestRequestHandler(http.server.SimpleHTTPRequestHandler):
    """A wrapper handler which intercepts HTTP requests in order to provide a
    REST interface.

    Args:
        seer (Seer): The seer provides data for the REST request responses.
        *args: (varargs):
            Arguments to pass along to SimpleHTTPRequestHandler initializer.
    """

    def __init__(self, seer, *args):
        # Retrieve the system under test state instance and allow the
        # standard handler to initialize
        self.seer = seer
        http.server.SimpleHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        """Handle REST request routing.

        The default implementation of SimpleHTTPRequestHandler serves static
        files from the local filesystem.  This method overrides that behavior
        in order to serve generated JSON responses based on the path requested.
        """
        log.debug(f"REST request: {self.path}")
        if self.path == "/answer":
            self._endpoint_GET_answer()
        elif self.path == "/perspective_index":
            self._endpoint_GET_perspective_index()
        elif self.path == "/service_state":
            self._endpoint_GET_service_state()
        else:
            self.send_error(
                requests.codes.not_found,
                "Unknown GET endpoint for the seer queries: {self.path}",
            )

    def _endpoint_GET_answer(self):
        if str(self.seer.state) == "Available":
            # The seer application only responds in the Available.
            self._send_response_200(self.seer.wisdom.answer_question())
        else:
            self.send_error(
                requests.codes.service_unavailable,
                f"The seer is {self.seer.state}. "
                "Please leave a question after the beep.",
            )

    def _endpoint_GET_perspective_index(self):
        if str(self.seer.state) == "Available":
            self._send_response_200(self.seer.wisdom.perspective_index)
        else:
            self.send_error(
                requests.codes.service_unavailable,
                f"The seer is {self.seer.state}. "
                "Please leave a question after the beep.",
            )

    def _endpoint_GET_service_state(self):
        self._send_response_200(str(self.seer.state))

    def _send_response_200(self, payload):
        """Send json response for an HTTP Get request

        Args:
            payload: JSON-serializable data.
        """
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        data = json.dumps(payload)
        log.debug(f"REST response: {data}")
        self.wfile.write(data.encode())

# Overview
The CI/CD containerized test TestAssitant framework provides a
simple yet convenient mechanism to help teams their applications and services.

Their are a few simple requirements to meet in order to integrate your
container-hosted application into TestAssitant. The mocksystemundertest project
is meant to present a demonstrative example for fulfulling the requirements.
The mocksystemundertest project produces a container hosting a simple
application, demoapp. The demoapp application show how an application
interfaces with the TestAssitant framework as well as how container
operations, i.e. Docker commands, affect the hosted application.

The demoapp is an implementation of the Magic 8 Ball toy. It is simplistic
in operation. However, the application supports both mandatory and
optional functionality provided by the TestAssitant containerized testing
framework.

This wiki has a number of references to the sidecar and testdriver
containers. The intent is to help show minutiae that coud
help you with your SUT integration. Additional information on the sidecar and
testdriver containers, and the SidecarMediator API can be found in their
respective repositories.

## The Sidecar Interface

### Overview
The system under test, SUT, is made up of two containers configured
in the "sidecar pattern". The sidecar is designed to work with the
SidecarMediator API to provide a standardized interface for
testing containers. The second container is the container that
hosts your application. This section addresses how to design your
container to work with the sidecar.

To sum it up, team mobius maintains the testdriver and sidecar
containers, and the SidecarMediator API. Your team will manage
the test container so that your test container a) hosts your application
and b) is compliant with the sidecar container.

#### Links
* [The mocksysteundertest Demonstration Container](https://confluence.rspringob.local:8443/display/ST/The+mocksysteundertest+Demonstration+Container) -- 
a functional description of the demoapp application.
* [mobius TestAssitant](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/readme.md) --
TestAssitant overview including build and test instructions.
* [Sidecar Mediator API](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/sidecarmediator/README.md) --
A Python API that can be inluded in pytest test modules.

### Application Readiness
The test container sends notifications to the sidecar container using
a file-based unix socket. This socket implementation is a very simplified take
on the dbus interface used by many OmniStack services.

Readiness is indicated by first sending a 'standby' message. The standy is
typically sent when your application is initializing. The standby
message is a key/vale pair in the following form: \
`"READY=1"`

A follow-on message is sent when you application becomes fully operational: \
`"READY=1\nMAINPID=1"`.

The MAINPID value 1 if your application is the primary process launched
when your test container is started. This is standard behavior for a Docker
container.

Once the standby and ready notifications have been sent the `wait_for_ready()`
function in the SidecarMediator API will return `True`.

#### Links
| Project        | File           | Info  |
| ------------- |-------------|: -----|
| demoapp      | [sidecarinterface.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/sidecarinterface.py) | The `send_ready_update()` function creates the standby and ready messages. |
| demoapp      | [seerpsyche.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/seerpsyche.py) | State transitions use `notifier.send_ready_update()` to update the sidecar with readiness messages. |
| testdriver      | [test_sidecar.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/testdriver/src/tests/sidecarmediator/test_sidecar.py) | The `wait_for_ready()` and `wait_for_stop()` functions in the SidecarMediator are used frequently with start and stop operations on the SUT container.|
| testdriver      | [test_sidecar_injection.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/testdriver/src/tests/sidecarmediator/test_sidecar_injection.py) | Ready messages are cached on a filesystem and read by the application when it starts. |

### The Sidecar Reset Operation
The `reset_sut()` function in the SidecarMediator API updates the
the sidecar's opinion of readiness of the application hosted by the SUT.
After a reset operation, `wait_for_ready()` will timeout since the sidecar now
believes that the hosted application, and thus the SUT, is
not ready. This is true even if the application itself is truly ready.

The SUT must be designed to recover from a sidecar reset operation. In order to recover,
the application must send standby and a ready messages to the sidecar.
Once sidecar has received those two messages, `wait_for_ready()` will return
True.

#### Links
| Project        | File           | Info  |
| ------------- |-------------|: -----|
| demoapp      | [seerpsyche.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/seerpsyche.py) | For both initial readiness and getting to ready after a reset, demoapp sends two notificaitons to the sidecar container. Upon Seer object creation, a Waking object results in a 'standby ready' notification to the sidecar. The `self.event(Event.rally)` on the Seer object causes a transistion to the Available state and a message is sent to the sidecar to indicate that the app is ready.|
| sidecarmediator | [README.md](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/sidecarmediator/README.md) | See `reset_sut()` and `wait_for_ready()`. |
| testdriver      | [test_sidecar.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/testdriver/src/tests/sidecarmediator/test_sidecar.py) | `test_reset()`|

## Signal Support
Docker can be used to send signals to a container. The SidecarMediator API
uses Docker in its backend to allow you to send signals during your application testing.

The hosted application in your SUT is not required to handle signals.
However, it is advisable that your application handle at least SIGTERM for
neater and faster container shutdown operations.

### SIGTERM
When Docker stops a container, Docker sends SIGTERM to the primary process,
i.e. PID = 1.

Well-behaved applications respond to SIGTERM, generally, by quickly saving
resources, if desired, and exiting immediately afterwards. Docker
stops the container when the primary process terminates.

### SIGKILL
If Docker tries to stop a container and the primary process does not terminate
in a timely manner, Docker sends SIGKILL to the primary process and stops
the container. SIGKILL cannot be handled.

### Other Signals
The `send_signal` function in the SidecarMediator API can be used to send
any signal to the SUT--including SIGTERM.

#### Links
| Project        | File           | Info  |
| ------------- |-------------|: -----|
| sidecarmediator | [README.md](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/sidecarmediator/README.md) | See `send_signal()`. |
| demoapp      | [sidecarinterface.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/seerpsyche.py) | SIGTERM: In an orderly shutdown, the seers "memories" are saved in the `Seer._handle_shutdown_signal() function`. The memories are recovered at startup in `Seer.__init__()`|
| demoapp      | [seerpsyche.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/seerpsyche.py) | Other signals are used to manage state transistions and configuration updates in demoapp. See `_register_event_signals`(), `_register_shutdown_signal()`, `register_service_interface_shutdown()`, `_handle_event_signal()` |
| testdriver      | [test_sidecar.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/testdriver/src/tests/sidecarmediator/test_sidecar.py) | `test_signal_sut()`, Stop testing indirectly tests SIGTERM since Docker sends SIGTERM when stopping a container.|

### Logging
As in any Docker container, stdout and stderr are captured and available
via Docker log operations. The logs are available via the `collect_logs()` function
in the SidecarMediator API as well.

For the mocksystemundertest container, the Python logging mechanism is configured
to log messages to stdout. The `collect_logs()` function in the SidecarMediator API
cause the Docker-cached logs to be  written to a bound volume.

#### Links
| Project        | File           | Info  |
| ------------- |-------------|: -----|
| demoapp      | [docker-compose.yaml](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/docker-compose.yaml) | A volume is mounted where the logs are collected. |

## Test Support
All of the testing for demoapp is in the `test_demoapp.py` file which is located
in the testdriver container.

The links for `test_sidecar.py` and  `test_sidecar_injection.py` are
shown in this wiki to help illustrate how functionality is supported.
This information might help you in your development of your SUT container.

### Execution
The mocksystemundertest container uses a script, /runTests.sh, as the entry
point to the container. The runTests.sh script in the mocksystemundertest SUT
launches a pytest session.

All CICD automation uses the `/runTests.sh` entry point. While you could use
and alternative entry point, your container would not compatible with other
mobius/CICD infrastructure.

Test scripts for your application can be included in a custom testdriver
container that your team maintains. The test scripts are built
into the testdriver container.

### Data Injection
The demoapp includes support for message injection.

JSON-encoded messages are read upon demoapp startup. These injected messages
are processed similarly to messages received on the dbus emulation socket.

#### Links
| Project        | File           | Info  |
| ------------- |-------------|: -----|
| demoapp      | [sidecarinterface.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/demoapp/sidecarinterface.py) | `send_injected_messages` processes messages on a filesystem and sends them to the sidecar|
| testdriver      | [test_sidecar_injection.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/testdriver/src/tests/sidecarmediator/test_sidecar_injection.py) | Direct testing of message injection functionality. |


### Test Results
Test results are deposited on a filesystem managed by docker-compose. There are no implementation requirements
for SUT containers.

#### Links
| Project        | File           | Info  |
| ------------- |-------------|: -----|
| demoapp      | [docker-compose.py](https://stash.rspringob.local/projects/CICD/repos/mobius-testassitant/browse/projects/mocksystemundertest/docker-compose.yml) | Note the volume binding.|
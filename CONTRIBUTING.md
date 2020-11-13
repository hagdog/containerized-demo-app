# Contributing to the Sidecar Mediator Project

Welcome! The mobius team is so glad that you are interested in
contributing to the Sidecar Mediator project.

The mobius team is responsible for implementing new functionality
and peforming maintenance on the testassitant (sidecar) container that 
manages containerized systems under test (SUT's). mobius also
maintains the Python module, Sidecar Mediator, which provides a programmatic
interface to the testassitant.

The mobius team is committed to considering requests and suggestions
from engineering test and development teams. If you would like to discuss
changes to the behavior of the testassitant container, please contact
a mobius team member of file a Jira ticket and assign it
to the mobius team.

The Sidecar Mediator is a used widely in the HCI engineering organization.
For this reason, mobius generally updates the testassitant and
Sidecar Mediator modules with functionality that can be shared by the organization.

If your team has needs that are too specialized for general usage, consider
forking the mobius repository and publishing a customized module for
your team to use. In order to prevent usage issues, your published module
cannot be named "sidecarmediator". If you wish to publish your module to 
Artifactory, please contact Releng for details.

While the Sidecar Mediator module is Python based, the testassitant can be
accessed through other means. Your team could, for example, create a 
C++ interface to the testassitant. The C++ code can leverage the REST
interface on the sidecar just like Sidecar Mediator. The Sidecar Mediator code and
the testassitant code will provide clues on how you would interoperate
with the testassitant using the language of your choice.

A generic utility library for dispatching multiple interdependent tasks.

The fundamental difference between this and most build systems is that the
build order is not 'compiled' at the start; new dependencies may be added and
tasks may be changed dynamically depending on events generated over the course
of the run. This naturally encodes notions of continuous integration tests
(e.g. by generating events from file watchers) and capturing generated files
from processes with output unknown in advance (e.g. some debug logs).

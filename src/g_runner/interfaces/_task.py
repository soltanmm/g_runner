import abc


class Task(object):
  """A task to perform.

  Implementors should provide value semantics with respect to the interface.
  Running the task should not cause the internal state of the task to change
  (i.e. a task is a record representation of a purely side-effect operation
  affecting only non-g_runner objects)."""
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def run(self):
    """Perform the task's task."""
    raise NotImplementedError()

  @abc.abstractmethod
  def input_paths(self):
    """Get an iterable over the input paths of this task."""
    raise NotImplementedError()

  @abc.abstractmethod
  def output_paths(self):
    """Get an iterable over the output paths of this task."""
    raise NotImplementedError()

  @abc.abstractmethod
  def __eq__(self, other):
    raise NotImplementedError()

  @abc.abstractmethod
  def __hash__(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def __copy__(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def __deepcopy__(self, memo):
    raise NotImplementedError()

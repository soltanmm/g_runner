import abc

from g_runner.interfaces import _path
from g_runner.interfaces import _task


class Tracker(object):
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def tasks(self):
    """Get all tasks."""
    raise NotImplementedError()

  @abc.abstractmethod
  def tasks_by_tags(self, tags):
    """Get tasks that have all of the given tags.

    The only requirement of tags are that they be usable as hash map keys."""
    raise NotImplementedError()

  @abc.abstractmethod
  def tagged_tasks(self):
    """Get 2-tuples of associated tags and tagged task sequences.

    Does not necessarily return all tasks; untagged tasks are not returned."""
    raise NotImplementedError()

  @abc.abstractmethod
  def tasks_by_outputs(self, output_paths):
    """Get tasks that have all specified outputs."""
    raise NotImplementedError()

  @abc.abstractmethod
  def tasks_by_inputs(self, input_paths):
    """Get tasks that have all specified inputs."""
    raise NotImplementedError()

  @abc.abstractmethod
  def paths(self):
    """Get all tracked paths."""
    raise NotImplementedError()

  @abc.abstractmethod
  def __eq__(self, other):
    """Get equivalence between trackers.

    We only require that this be consistent between trackers of the same type;
    there's no consistency requirement between trackers of different types."""
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


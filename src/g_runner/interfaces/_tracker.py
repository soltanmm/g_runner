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
  def replaced(self, old_paths=None, new_paths=None,
               old_tasks=None, new_tasks=None, new_tagged_tasks=None):
    """Get a new tracker with old items replaced with new items.

    Arguments:
      old_paths (iterable): an iterable of paths to be replaced. If unspecified,
        new_paths are simply added.
      new_paths (iterable): an iterable of paths to replace the old_paths with.
        If unspecified, the old_paths are simply removed. If both are
        unspecified, there will be no relative difference between the new
        tracker and self with respect to paths.
      old_tasks (iterable): an iterable of paths to be replaced. If unspecified,
        new_tasks are simply added.
      new_tasks (iterable): an iterable of tasks to replace the old_tasks with.
        If unspecified and new_tagged_tasks is unspecified, the old_tasks are
        simply removed.  If all are unspecified, there will be no relative
        difference between the new tracker and self with respect to tasks.
      new_tagged_tasks (iterable): an iterable of 2-sequences of tasks and
        sequences of tags. Is aggregated with new_tasks for task replacement."""
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


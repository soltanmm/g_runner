"""Functionality for easier task automation."""

import copy
import subprocess

from g_runner import interfaces
from g_runner import runner
from g_runner.runner import tracker as _tracker


"""First component of every path uniquely associated with a specific task.

Note that because Task objects are valid dictionary keys we can place tasks
directly within lists/tuples following this component to make their associated
paths."""
TASK_PATH_TAG = object()

"""First component of every path associated with a file."""
FILE_PATH_TAG = object()


class ScriptedTask(interfaces.Task):

  def __init__(self, callee, input_paths, output_paths, args=(), kwargs={}):
    """By contract the 'callee' object must be without visible side effects."""
    self._callee = callee
    self._input_paths = tuple(input_paths)
    self._output_paths = tuple(output_paths)
    self._args = args
    self._kwargs = kwargs

  def __call__(self, *args, **kwargs):
    """Allow transparent access to the internal callable."""
    return self._callee(*args, **kwargs)

  def run(self):
    return self._callee(*self._args, **self._kwargs)

  def input_paths(self):
    return self._input_paths

  def output_paths(self):
    return self._output_paths

  def __eq__(self, other):
    if not isinstance(other, ScriptedTask):
      return False
    return (
        self._callee is other._callee and
        self._args == other._args and
        self._kwargs == other._kwargs and
        self._input_paths == other._input_paths and
        self._output_paths == other._output_paths)

  def __hash__(self):
    return hash((self._callee, self._input_paths, self._output_paths))

  def __copy__(self):
    return ScriptedTask(self._callee, self._input_paths, self._output_paths,
                        self._args, self._kwargs)

  def __deepcopy__(self, memo):
    return ScriptedTask(copy.deepcopy(self._callee, memo),
                        copy.deepcopy(self._input_paths, memo),
                        copy.deepcopy(self._output_paths, memo),
                        copy.deepcopy(self._args, memo),
                        copy.deepcopy(self._kwargs, memo))

def _run_command_line(command, **subprocess_kwargs):
  return subprocess.check_call(command, **subprocess_kwargs)


class CommandLineTask(ScriptedTask):

  def __init__(self, command, input_paths=(), output_paths=(),
               **subprocess_kwargs):
    super(CommandLineTask, self).__init__(
        _run_command_line, input_paths, output_paths, args=(command,),
        kwargs=subprocess_kwargs)


class TrackerBuilder(object):
  """Class of decorator-like functions to build up a tracker and run it.

  n.b. while constructing the tracker paths"""

  def __init__(self):
    self._tracker = _tracker.Tracker()
    self._tasks_to_task_paths = {}
    self._task_paths_to_tasks = {}

  def _add_callable_task(self, callee, input_paths=(), output_paths=(),
                        args=(), kwargs={}, custom_path=None):
    """Add a task to the tracker builder."""
    if custom_path is not None:
      assert isinstance(custom_path, interfaces.Path)
      path = custom_path
    else:
      base_task = ScriptedTask(callee, input_paths=input_paths,
                               output_paths=output_paths, args=args,
                               kwargs=kwargs)
      path = (TASK_PATH_TAG, base_task)
    task = ScriptedTask(callee, input_paths=input_paths,
                        output_paths=tuple(output_paths) + (path,), args=args,
                        kwargs=kwargs)
    self._tasks_to_task_paths[task] = path
    self._task_paths_to_tasks[path] = task
    self._tracker = self._tracker.replaced(
        new_paths=(path,), new_tasks=(task,)
    )
    return task

  def _add_command_line_task(self, command, input_paths=(), output_paths=(),
                             custom_path=None, **subprocess_kwargs):
    """Add a command line task to the tracker builder."""
    if custom_path is not None:
      assert isinstance(custom_path, interfaces.Path)
      path = custom_path
    else:
      base_task = CommandLineTask(command, input_paths=input_paths,
                                  output_paths=output_paths,
                                  **subprocess_kwargs)
      path = (TASK_PATH_TAG, base_task)
    task = CommandLineTask(command, input_paths=input_paths,
                           output_paths=tuple(output_paths) + (path,),
                           **subprocess_kwargs)
    self._tasks_to_task_paths[task] = path
    self._task_paths_to_tasks[path] = task
    self._tracker = self._tracker.replaced(
        new_paths=(path,), new_tasks=(task,)
    )
    return task

  def _task(self, object_to_scripted_task_function, input_paths=(),
            output_paths=(), custom_path=None):
    # normalize inputs
    input_paths = (
        tuple(
            self._tasks_to_task_paths[path] for path in input_paths
            if isinstance(path, ScriptedTask)
        ) + tuple(
            path for path in input_paths if not isinstance(path, ScriptedTask)
        )
    )
    def task_decorator(input_task_object):
      """Decorator to add a task to the builder."""
      return object_to_scripted_task_function(input_task_object, input_paths,
                                              output_paths, custom_path)
    return task_decorator

  def task(self, input_paths=(), output_paths=(), args=(), kwargs={},
           custom_path=None):
    def task_decorator(callee, input_paths, output_paths, custom_path):
      return self._add_callable_task(
          callee, input_paths=input_paths, output_paths=output_paths,
          custom_path=custom_path, args=args, kwargs=kwargs)
    return self._task(task_decorator, input_paths, output_paths, custom_path)

  def command(self, input_paths=(), output_paths=(), custom_path=None,
              **subprocess_kwargs):
    def task_decorator(command, input_paths, output_paths, custom_path):
      return self._add_command_line_task(
          callee, input_paths=input_paths, output_paths=output_paths,
          custom_path=custom_path, **subprocess_kwargs)
    return self._task(task_decorator, input_paths, output_paths, custom_path)

  def run(self, runner_event_iterator=[], **kwargs):
    return runner.run_tracker(self._tracker, runner_event_iterator, **kwargs)


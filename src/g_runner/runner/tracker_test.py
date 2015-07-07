import copy
import unittest

from g_runner import interfaces
from g_runner.runner import tracker as _tracker


class TestTask(interfaces.Task):

  def __init__(self, task_name, inputs, outputs):
    self.name = task_name
    self.inputs = tuple(inputs)
    self.outputs = tuple(outputs)

  def run(self):
    pass

  def input_paths(self):
    return self.inputs

  def output_paths(self):
    return self.outputs

  def __eq__(self, other):
    return (
        isinstance(other, TestTask) and self.inputs == other.inputs and
        self.outputs == other.outputs and self.name == other.name)

  def __hash__(self):
    return hash((self.name, self.inputs, self.outputs))

  def __copy__(self):
    return TestTask(self.name, self.inputs, self.outputs)

  def __deepcopy__(self, memo):
    return TestTask(copy.deepcopy(self.name, memo),
                    copy.deepcopy(self.inputs, memo),
                    copy.deepcopy(self.outputs, memo))


class TrackerTest(unittest.TestCase):

  def test_updown(self):
    self.assertIsInstance([], interfaces.Path)
    self.assertIsInstance(['a', 1], interfaces.Path)
    self.assertIsInstance((3,), interfaces.Path)
    tracker = _tracker.Tracker()

  def test_tracker_updates(self):
    tracker = _tracker.Tracker()
    tracker.add_path((1,))
    tracker.add_path((2,))
    tracker.add_path((3,))
    self.assertEqual(3, len(tracker.paths()))
    tracker.add_task(TestTask('12', [(1,)], [(2,)]))
    tracker.add_task(TestTask('23', [(2,)], [(3,)]))
    self.assertEqual(2, len(tracker.tasks()))
    self.assertEqual(1, len(tracker.tasks_by_inputs([(1,)])))
    self.assertEqual(1, len(tracker.tasks_by_inputs([(2,)])))
    self.assertEqual(0, len(tracker.tasks_by_inputs([(1,), (2,)])))

if __name__ == '__main__':
  unittest.main(verbosity=2)

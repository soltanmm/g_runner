import copy
import time
import unittest

from g_runner import interfaces
from g_runner import runner
from g_runner.runner import tracker as _tracker


class TestTask(interfaces.Task):

  def __init__(self, task_name, inputs, outputs):
    self.name = task_name
    self.inputs = tuple(inputs)
    self.outputs = tuple(outputs)
    self.run_time = None
    self.ran_count = 0

  def run(self):
    self.run_time = time.time()
    time.sleep(0.001)
    self.ran_count = self.ran_count + 1

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


class RunnerTest(unittest.TestCase):

  def test_line_run(self):
    tracker = _tracker.Tracker()
    tracker.add_path((1,))
    tracker.add_path((2,))
    tracker.add_path((3,))
    task12 = TestTask('12', [(1,)], [(2,)])
    task23 = TestTask('23', [(2,)], [(3,)])
    tracker.add_task(task12)
    tracker.add_task(task23)
    runner.run_tracker(tracker, iter([
        runner.Event(
            path_selector=lambda unused_tracker: [(1,)],
            flags=runner.EventFlags(
                paths_state=runner.PathState.up_to_date
            )
        )
    ]))
    self.assertEqual(1, task12.ran_count)
    self.assertEqual(1, task23.ran_count)
    self.assertLessEqual(task12.run_time, task23.run_time)

  def test_line_run_initializing_task(self):
    tracker = _tracker.Tracker()
    tracker.add_path((1,))
    tracker.add_path((2,))
    tracker.add_path((3,))
    task0 = TestTask('0', [], [(1,)])
    task12 = TestTask('12', [(1,)], [(2,)])
    task23 = TestTask('23', [(2,)], [(3,)])
    tracker.add_task(task0)
    tracker.add_task(task12)
    tracker.add_task(task23)
    runner.run_tracker(tracker, iter([]))
    self.assertEqual(1, task0.ran_count)
    self.assertEqual(1, task12.ran_count)
    self.assertEqual(1, task23.ran_count)
    self.assertLessEqual(task0.run_time, task12.run_time)
    self.assertLessEqual(task12.run_time, task23.run_time)

  def test_join_initializing_task(self):
    tracker = _tracker.Tracker()
    tracker.add_path((4,))
    tracker.add_path((3,))
    tracker.add_path((2,))
    tracker.add_path((1,))
    task0 = TestTask('0', [], [(1,)])
    task12 = TestTask('12', [(1,)], [(2,)])
    task13 = TestTask('13', [(1,)], [(3,)])
    task234 = TestTask('234', [(2,), (3,)], [(4,)])
    tracker.add_task(task0)
    tracker.add_task(task12)
    tracker.add_task(task13)
    tracker.add_task(task234)
    runner.run_tracker(tracker, iter([]))
    self.assertEqual(1, task0.ran_count)
    self.assertEqual(1, task12.ran_count)
    self.assertEqual(1, task13.ran_count)
    self.assertEqual(1, task234.ran_count)
    self.assertLessEqual(task0.run_time, task12.run_time)
    self.assertLessEqual(task0.run_time, task13.run_time)
    self.assertLessEqual(task13.run_time, task234.run_time)
    self.assertLessEqual(task12.run_time, task234.run_time)

if __name__ == '__main__':
  unittest.main(verbosity=2)

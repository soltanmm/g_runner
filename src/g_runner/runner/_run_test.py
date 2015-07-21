import copy
import multiprocessing
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


class FailingTestTask(TestTask):

  def __init__(self, task_name, inputs, outputs, error):
    super(FailingTestTask, self).__init__(task_name, inputs, outputs)
    self.error = error

  def run(self):
    raise self.error


class RunnerTest(unittest.TestCase):

  def test_not_a_tracker(self):
    with self.assertRaises(TypeError):
      runner.run_tracker('42', [])

  def test_callbacks_not_of_right_type(self):
    with self.assertRaises(TypeError):
      runner.run_tracker(_tracker.Tracker(), [], callbacks='asdf')

  def test_line_run(self):
    task12 = TestTask('12', [(1,)], [(2,)])
    task23 = TestTask('23', [(2,)], [(3,)])
    tracker = _tracker.Tracker().replaced(
      new_paths=[(1,), (2,), (3,)],
      new_tasks=[
          task12,
          task23
      ]
    )
    runner.run_tracker(tracker, [
        runner.Event(
            path_selector=lambda unused_tracker: [(1,)],
            flags=runner.EventFlags(
                paths_state=runner.PathState.up_to_date
            )
        )
    ], outdated=True)
    self.assertEqual(1, task12.ran_count)
    self.assertEqual(1, task23.ran_count)
    self.assertLessEqual(task12.run_time, task23.run_time)

  def test_up_to_date_line_run_does_nothing(self):
    task12 = TestTask('12', [(1,)], [(2,)])
    task23 = TestTask('23', [(2,)], [(3,)])
    tracker = _tracker.Tracker().replaced(
      new_paths=[(1,), (2,), (3,)],
      new_tasks=[
          task12,
          task23
      ]
    )
    runner.run_tracker(tracker, [
        runner.Event(
            path_selector=lambda unused_tracker: [(1,)],
            flags=runner.EventFlags(
                paths_state=runner.PathState.up_to_date
            )
        )
    ], outdated=False)
    self.assertEqual(0, task12.ran_count)
    self.assertEqual(0, task23.ran_count)

  def test_line_run_initializing_task(self):
    task0 = TestTask('0', [], [(1,)])
    task12 = TestTask('12', [(1,)], [(2,)])
    task23 = TestTask('23', [(2,)], [(3,)])
    tracker = _tracker.Tracker().replaced(
      new_paths=[(1,), (2,), (3,)],
      new_tasks=[
          task0,
          task12,
          task23
      ]
    )
    runner.run_tracker(tracker, [], outdated=True)
    self.assertEqual(1, task0.ran_count)
    self.assertEqual(1, task12.ran_count)
    self.assertEqual(1, task23.ran_count)
    self.assertLessEqual(task0.run_time, task12.run_time)
    self.assertLessEqual(task12.run_time, task23.run_time)

  def test_join_initializing_task(self):
    task0 = TestTask('0', [], [(1,)])
    task12 = TestTask('12', [(1,)], [(2,)])
    task13 = TestTask('13', [(1,)], [(3,)])
    task234 = TestTask('234', [(2,), (3,)], [(4,)])
    tracker = _tracker.Tracker().replaced(
        new_paths=[(4,), (3,), (2,), (1,)],
        new_tasks=[
            task0,
            task12,
            task13,
            task234
        ]
    )
    runner.run_tracker(tracker, [], outdated=True)
    self.assertEqual(1, task0.ran_count)
    self.assertEqual(1, task12.ran_count)
    self.assertEqual(1, task13.ran_count)
    self.assertEqual(1, task234.ran_count)
    self.assertLessEqual(task0.run_time, task12.run_time)
    self.assertLessEqual(task0.run_time, task13.run_time)
    self.assertLessEqual(task13.run_time, task234.run_time)
    self.assertLessEqual(task12.run_time, task234.run_time)

  def test_failure(self):
    tracker = _tracker.Tracker().replaced(
        new_paths=[(1,)],
        new_tasks=[
            FailingTestTask('', [], [(1,)], RuntimeError('foo'))
        ]
    )
    with self.assertRaises(runner.RunnerError):
      runner.run_tracker(tracker, [], outdated=True)

  def test_failure_keep_going(self):
    task2 = TestTask('2', [], [(2,)])
    task23 = TestTask('23', [(2,)], [(3,)])
    tracker = _tracker.Tracker().replaced(
        new_paths=[(1,), (2,), (3,)],
        new_tasks=[
            FailingTestTask('', [], [(1,)], RuntimeError('foo')),
            task2,
            task23
        ]
    )
    with self.assertRaises(runner.RunnerError):
      runner.run_tracker(tracker, [], keep_going=True, outdated=True)
    self.assertEqual(1, task2.ran_count)
    self.assertEqual(1, task23.ran_count)

if __name__ == '__main__':
  unittest.main(verbosity=2)

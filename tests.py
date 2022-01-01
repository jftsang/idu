import unittest
from os import uname
from os.path import join
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from idu import IDu, HELP, run_du, DirectoryDu

sysname = uname().sysname
SUPPORTED = {'Linux', 'Darwin'}

class TestIDu(unittest.TestCase):
    def setUp(self):
        self.td = TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

        self.idu = IDu(self.td.name, self.td.name)

    @patch('idu.print')
    @patch('idu.input', return_value='?')
    def test_qn_prints_help(self, m_input, m_print):
        self.idu.prompt()
        m_input.assert_called()
        m_print.assert_called_with(HELP)

    @patch('idu.input', return_value='q')
    def test_q_quits(self, m_input):
        with self.assertRaises(SystemExit) as cm:
            self.idu.prompt()
            m_input.assert_called()
            self.assertEqual(0, cm.exception.code)

    @patch('idu.IDu.prompt', side_effect=KeyboardInterrupt)
    @patch('idu.run_du', return_value=([], ''))
    def test_ctrl_c_quits(self, m_run_du, m_prompt):
        self.idu.loop()
        m_prompt.assert_called_once()

    @patch('idu.IDu.prompt', side_effect=EOFError)
    @patch('idu.run_du', return_value=([], ''))
    def test_ctrl_d_quits(self, m_run_du, m_prompt):
        self.idu.loop()
        m_prompt.assert_called_once()

    @patch('idu.IDu.__str__', return_value='')
    @patch('idu.IDu.update')
    @patch('idu.input', return_value='p')
    def test_p_prints_but_doesnt_refresh(self, m_input, m_update, m_idu_str):
        self.idu.prompt()
        m_input.assert_called()
        m_update.assert_not_called()
        m_idu_str.assert_called()

    @patch('idu.IDu.__str__', return_value='')
    @patch('idu.IDu.update')
    @patch('idu.input', return_value='P')
    def test_capital_p_refreshes_and_prints(self, m_input, m_update, m_idu_str):
        self.idu.prompt()
        m_input.assert_called()
        m_update.assert_called()
        m_idu_str.assert_called()

    @patch('idu.run_du', return_value=([], ''))
    def test_update_runs_du(self, m_run_du):
        self.idu.update()
        m_run_du.assert_called()

    @patch('idu.run_du', return_value=([], ''))
    @patch('idu.input', return_value='..')
    def test_dotdot_goes_up_to_parent(self, m_input, m_run_du):
        self.idu.prompt()
        m_input.assert_called()
        m_run_du.assert_called_with(Path(self.td.name).resolve().parent)
        # and the directory has changed
        self.assertEqual(
            Path(self.td.name).resolve().parent, self.idu.directory
        )
        # but the base directory has not
        self.assertEqual(Path(self.td.name).resolve(), self.idu.base_directory)

    @patch('idu.subprocess.run', side_effect=KeyboardInterrupt)
    def test_interrupted_update_doesnt_change_dir(self, m_subprocess_run):
        self.idu.directory = '/foo'
        self.idu.update('/bar')  # raises KeyboardInterrupt
        m_subprocess_run.assert_called()
        self.assertEqual('/foo', self.idu.directory)

    @patch('idu.run_du', side_effect=RuntimeError)
    def test_doesnt_like_nonexistent_directory(self, m_run_du):
        idu = IDu(directory=join(self.td.name, 'foo'))
        with self.assertRaises(RuntimeError):
            idu.loop()


@unittest.skipIf(
    sysname not in SUPPORTED,
    'Skipping unit tests for run_du as this is neither a Linux nor a '
    'Darwin system.'
)
class TestRunDu(unittest.TestCase):
    def setUp(self):
        self.td = TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def mkfile(self, path, nbytes):
        with open(join(self.td.name, path), 'w') as f:
            f.write('x' * nbytes)

    def mkdir(self, path):
        (Path(self.td.name) / path).mkdir(parents=True, exist_ok=True)

    def test_run_du_empty_directory(self):
        results, stderr = run_du(self.td.name)
        self.assertEqual('', stderr)
        if sysname == 'Linux':
            expected = [DirectoryDu(self.td.name, 4)]
        elif sysname == 'Darwin':
            expected = [DirectoryDu(self.td.name, 0)]
        else:
            raise NotImplementedError

        self.assertListEqual(expected, results)

    def test_run_du_nonexistent_directory(self):
        results, stderr = run_du(join(self.td.name, 'nonexistent'))
        self.assertIn('No such file or directory', stderr)
        self.assertListEqual([], results)

    @unittest.expectedFailure  # issue #2
    def test_run_du_directory_with_files(self):
        nbytes = 1_000
        self.mkfile('foo.txt', nbytes)
        results, stderr = run_du(self.td.name)
        self.assertEqual('', stderr)
        self.assertSetEqual({DirectoryDu(self.td.name, nbytes)}, set(results))

    def test_run_du_directory_with_subdirectory(self):
        self.mkdir('foo/')
        results, stderr = run_du(self.td.name)
        self.assertEqual('', stderr)
        if sysname == 'Linux':
            expected = {
                DirectoryDu(self.td.name, 8),
                DirectoryDu(join(self.td.name, 'foo/'), 4),
            }
        elif sysname == 'Darwin':
            expected = {
                DirectoryDu(self.td.name, 0),
                DirectoryDu(join(self.td.name, 'foo/'), 0),
            }
        else:
            raise NotImplementedError
        self.assertSetEqual(expected, set(results))

    def test_run_du_directory_with_subdirectories(self):
        self.mkdir('foo/')
        self.mkdir('foo/boo')
        self.mkdir('bar')
        results, stderr = run_du(self.td.name)
        self.assertEqual('', stderr)
        if sysname == 'Linux':
            expected = {
                DirectoryDu(self.td.name, 16),
                DirectoryDu(join(self.td.name, 'foo/'), 8),
                DirectoryDu(join(self.td.name, 'foo/boo/'), 4),
                DirectoryDu(join(self.td.name, 'bar/'), 4),
            }
        elif sysname == 'Darwin':
            expected = {
                DirectoryDu(self.td.name, 0),
                DirectoryDu(join(self.td.name, 'foo/'), 0),
                DirectoryDu(join(self.td.name, 'foo/boo/'), 0),
                DirectoryDu(join(self.td.name, 'bar/'), 0),
            }
        else:
            raise NotImplementedError
        self.assertSetEqual(expected, set(results))


if __name__ == '__main__':
    unittest.main()

import unittest
from os.path import join, dirname
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from idu import IDu, HELP


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
    def test_P_refreshes_and_prints(self, m_input, m_update, m_idu_str):
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
        self.assertEqual(Path(self.td.name).resolve().parent, self.idu.directory)
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

if __name__ == '__main__':
    unittest.main()

"""离线测试，不发送请求、不启动连接。"""
import subprocess
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs
import campus
import pppoe


class CampusTests(unittest.TestCase):
    def test_query_encoding(self):
        query = parse_qs(campus.make_query("demo", 'a&+"\\密码', "telecom", "192.0.2.1"))
        self.assertEqual(query["user_account"], ["demo@telecom"])
        self.assertEqual(query["user_password"], ['a&+"\\密码'])

    def test_jsonp(self):
        self.assertEqual(campus.parse_response('dr1003({"result":1});')["result"], 1)
        self.assertEqual(campus.parse_response('{"result":0}')["result"], 0)
        with self.assertRaises(ValueError):
            campus.parse_response('other({"result":1})')

    @patch("campus.subprocess.run")
    @patch("campus.getpass.getpass", return_value="test-secret")
    def test_password_not_in_argv(self, password, run):
        run.return_value = subprocess.CompletedProcess([], 0, 'dr1003({"result":1})', '')
        with patch("sys.argv", ["campus.py", "--interface", "eth0", "--wan-ip", "192.0.2.1", "--username", "demo", "--allow-http"]):
            self.assertEqual(campus.main(), 0)
        self.assertNotIn("test-secret", str(run.call_args.args))
        self.assertIn("test-secret", run.call_args.kwargs["input"])
        self.assertIn("if!eth0", run.call_args.args[0])


class PPPTests(unittest.TestCase):
    @patch("pppoe.subprocess.run")
    def test_reject_non_pppoe(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, '802-3-ethernet\n', '')
        with patch("sys.argv", ["pppoe.py", "00000000-0000-4000-8000-000000000001"]):
            self.assertEqual(pppoe.main(), 1)
        self.assertEqual(run.call_count, 1)

    @patch("pppoe.subprocess.run")
    def test_single_activation(self, run):
        run.side_effect = [subprocess.CompletedProcess([], 0, 'pppoe\n', ''), subprocess.CompletedProcess([], 0)]
        with patch("sys.argv", ["pppoe.py", "00000000-0000-4000-8000-000000000001"]):
            self.assertEqual(pppoe.main(), 0)
        self.assertEqual(run.call_count, 2)
        self.assertIn("--ask", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()

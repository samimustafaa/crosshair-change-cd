import unittest
from game_status import identify_game_process, detect_running_game

class GameStatusTests(unittest.TestCase):
    def test_detect_running_client_with_game_folder(self):
        match=detect_running_game([
            {"name":"chrome.exe","exe":"C:\\Program Files\\Chrome\\chrome.exe"},
            {"name":"client.exe","exe":"C:\\Creative Destruction\\client.exe"},
        ])
        self.assertEqual(match,"client.exe")

    def test_detect_when_game_in_background(self):
        self.assertEqual(detect_running_game([{"name":"client.exe","exe":None}]),"client.exe")

    def test_unrelated_process_not_detected(self):
        self.assertIsNone(detect_running_game([
            {"name":"client.exe","exe":"C:\\OtherApp\\client.exe"},
            {"name":"notepad.exe","exe":"C:\\Windows\\notepad.exe"},
        ]))

    def test_specific_client_names(self):
        self.assertEqual(identify_game_process({"name":"CDRevive.exe","exe":None}),"cdrevive.exe")
        self.assertEqual(identify_game_process({"name":"Creative Destruction.exe","exe":None}),
                         "creative destruction.exe")

    def test_inaccessible_process_does_not_fail(self):
        class DeadProcess:
            @property
            def info(self): raise RuntimeError("exited")
        self.assertEqual(detect_running_game([
            DeadProcess(), {"name":"CLIENT.EXE","exe":None}
        ]),"client.exe")

if __name__ == "__main__":
    unittest.main()

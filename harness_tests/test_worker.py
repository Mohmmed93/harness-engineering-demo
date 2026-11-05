import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('worker',Path(__file__).parents[1]/'harness/worker.py')
w=importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=w.connect(Path(self.tmp.name)/'queue.db')
        self.task={'id':'ticket-1','name':'Example','list':{'id':w.LIST_ID}}
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_duplicate_status_updates_do_not_dispatch_again(self):
        self.assertTrue(w.enqueue(self.db,self.task))
        self.task['description']='A new comment or edit'
        self.assertFalse(w.enqueue(self.db,self.task))
        self.assertIsNotNone(w.claim(self.db))
        self.assertIsNone(w.claim(self.db))
    def test_empty_description_held_before_execution(self):
        w.enqueue(self.db,self.task)
        w.hold_incomplete(self.db)
        self.assertIsNone(w.claim(self.db))
        self.assertEqual(self.db.execute('SELECT state FROM jobs').fetchone()[0],'needs_input')
    def test_wrong_list_rejected(self):
        self.task['list']['id']='another-list'
        with self.assertRaises(ValueError): w.enqueue(self.db,self.task)
    def test_closed_tasks_skipped(self):
        self.task['status']={'type':'closed'}
        self.assertFalse(w.enqueue(self.db,self.task))
    def test_claim_visible_to_second_connection(self):
        w.enqueue(self.db,self.task)
        db2=w.connect(Path(self.tmp.name)/'queue.db')
        try:
            self.assertIsNotNone(w.claim(self.db))
            self.assertIsNone(w.claim(db2))
        finally: db2.close()
    def test_credentials_not_in_subprocess_environment(self):
        with patch.dict(w.os.environ,{'CLICKUP_TOKEN':'secret','GITHUB_TOKEN':'secret','CUSTOM_SECRET':'secret'}):
            self.assertNotIn('CLICKUP_TOKEN',w.child_env())
            self.assertNotIn('GITHUB_TOKEN',w.child_env())
            self.assertNotIn('CUSTOM_SECRET',w.child_env())
    def test_dry_run_never_launches_process(self):
        w.enqueue(self.db,self.task)
        job=w.claim(self.db)
        with patch.object(w,'STATE',Path(self.tmp.name)),patch.object(w,'command') as command:
            w.run_job(self.db,job,True)
            command.assert_not_called()
        self.assertEqual(self.db.execute('SELECT state FROM jobs').fetchone()[0],'dry_run')
    def test_clickup_missing_token_fails_clearly(self):
        with patch.dict(w.os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'CLICKUP_TOKEN'):w.clickup_tasks()

if __name__=='__main__': unittest.main()

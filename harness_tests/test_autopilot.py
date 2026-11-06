import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'harness'))
import autopilot as a
import json
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads(a.POLICY.read_text())
        self.types={'17':'bug','0':'task'}
        self.task={'id':'one','name':'Bug','description':'Steps and expectation','list':{'id':'901521438487'},
                   'custom_item_id':17,'points':1,'priority':{'id':'3'},'status':{'status':'to do','type':'open'}}
    def test_boundary_points_allowed(self):
        for points in (0.5,1,2,'0.5','2'):
            self.task['points']=points
            self.assertTrue(a.eligible(self.task,self.types,self.policy)[0])
    def test_invalid_or_out_of_range_points_held(self):
        for points in (None,True,False,0,0.25,3,'NaN','Infinity','bad'):
            self.task['points']=points
            self.assertFalse(a.eligible(self.task,self.types,self.policy)[0])
    def test_priority_rules(self):
        for value,expected in (('1',False),('2',False),('3',True),('4',True)):
            self.task['priority']={'id':value}
            self.assertEqual(a.eligible(self.task,self.types,self.policy)[0],expected)
        self.task['priority']=None
        self.assertFalse(a.eligible(self.task,self.types,self.policy)[0])
    def test_type_and_status_are_required(self):
        self.task['custom_item_id']=0
        self.assertFalse(a.eligible(self.task,self.types,self.policy)[0])
        self.task['custom_item_id']=17;self.task['status']['status']='in progress'
        self.assertFalse(a.eligible(self.task,self.types,self.policy)[0])
    def test_incident_triage_overrides_metadata(self):
        self.task['description']='HARNESS_INCIDENT_TRIAGE'
        self.assertFalse(a.eligible(self.task,self.types,self.policy)[0])
    def test_other_list_rejected(self):
        self.task['list']['id']='other'
        self.assertFalse(a.eligible(self.task,self.types,self.policy)[0])
    def test_bot_comments_do_not_change_revision(self):
        base=a.snapshot(self.task,[])
        own={'id':'1','comment_text':'[harness-autopilot:1:question]\nWhat is expected?'}
        self.assertEqual(a.fingerprint(base),a.fingerprint(a.snapshot(self.task,[own])))
        reply={'id':'2','comment_text':'Expected six tickets'}
        self.assertNotEqual(a.fingerprint(base),a.fingerprint(a.snapshot(self.task,[reply,own])))
    def test_comment_sent_once(self):
        class API:
            def __init__(self):self.saved=[];self.posts=0
            def request(self,path,body=None):
                if body:
                    self.posts+=1;self.saved.append({'id':'1','comment_text':body['comment_text']});return {}
                return {'comments':self.saved}
        api=API()
        self.assertEqual(a.post_once(api,'one','[harness-autopilot:1:question]','Question'),'posted')
        self.assertEqual(a.post_once(api,'one','[harness-autopilot:1:question]','Question'),'already_posted')
        self.assertEqual(api.posts,1)
    def test_same_revision_not_reinvestigated_but_reply_can_resume(self):
        with tempfile.TemporaryDirectory() as d:
            db=a.connect(Path(d)/'a.db')
            data=a.snapshot(self.task,[])
            self.assertTrue(a.can_start(db,data,self.policy))
            job=a.new_attempt(db,data);a.set_state(db,job,'waiting_for_input')
            self.assertFalse(a.can_start(db,data,self.policy))
            data['replies']=[{'id':'2','text':'Answer'}]
            self.assertTrue(a.can_start(db,data,self.policy))
            a.set_state(db,job,'pr_open')
            self.assertFalse(a.can_start(db,data,self.policy));db.close()
    def test_daily_limit_is_persistent(self):
        with tempfile.TemporaryDirectory() as d:
            db=a.connect(Path(d)/'a.db')
            for task_id in ('one','two'):
                task=deepcopy(self.task);task['id']=task_id
                j=a.new_attempt(db,a.snapshot(task,[]));a.set_state(db,j,'out_of_scope')
            task=deepcopy(self.task);task['id']='three'
            self.assertFalse(a.can_start(db,a.snapshot(task,[]),self.policy));db.close()
    def test_dry_tick_does_not_start_agent_or_post(self):
        class API:
            def request(_,path,body=None):
                if '/custom_item' in path:return {'custom_items':[{'id':17,'name':'bug'}]}
                return {'comments':[]}
            def open_tasks(_):return [self.task]
        with tempfile.TemporaryDirectory() as d,patch.object(a,'process') as run:
            db=a.connect(Path(d)/'a.db');a.tick(db,API(),self.policy,False)
            run.assert_not_called();self.assertEqual(db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],0);db.close()
    def test_changed_priority_blocks_publication_retry(self):
        # Verify decision logic rather than contacting GitHub.
        class API:
            def request(_,path,body=None):
                if '/custom_item' in path:return {'custom_items':[{'id':17,'name':'bug'}]}
                task=deepcopy(self.task);task['priority']={'id':'1'};return task
        with tempfile.TemporaryDirectory() as d,patch.object(a,'STATE',Path(d)),patch.object(a,'publish_repair') as publish:
            db=a.connect(Path(d)/'a.db');data=a.snapshot(self.task,[]);job=a.new_attempt(db,data)
            folder=Path(d)/f'attempt-{job}';folder.mkdir();(folder/'task.json').write_text(json.dumps(data));(folder/'base.txt').write_text('a'*40)
            row=db.execute('SELECT * FROM attempts').fetchone();a.complete_publication(db,row,API(),self.policy)
            publish.assert_not_called();self.assertEqual(db.execute('SELECT state FROM attempts').fetchone()[0],'superseded');db.close()
    def test_process_questions_and_verified_repair_handoff(self):
        # Exercise the real state machine and worker database, replacing external execution only.
        class API:
            def __init__(inner): inner.saved=[]
            def request(inner,path,body=None):
                if body:
                    inner.saved.append({'id':str(len(inner.saved)), 'comment_text':body['comment_text']})
                    return {}
                if '/custom_item' in path:return {'custom_items':[{'id':17,'name':'bug'}]}
                if path.endswith('/comment'):return {'comments':inner.saved}
                return deepcopy(self.task)
        for decision in ('needs_input','ready','no_patch'):
            with self.subTest(decision=decision),tempfile.TemporaryDirectory() as d:
                api=API();root=Path(d);db=a.connect(root/'a.db')
                data=a.snapshot(self.task,[]);job=a.new_attempt(db,data)
                result={'decision':'ready' if decision=='no_patch' else decision,'summary':'Investigation',
                        'questions':['Which filter?'] if decision=='needs_input' else [],'reproduction':'Open and search'}
                def fake_repair(wdb,claimed,**kwargs):
                    self.assertEqual(kwargs['base_ref'],'a'*40)
                    self.assertEqual(kwargs['agent_timeout'],self.policy['repair_timeout_seconds'])
                    (a.worker.STATE/f'job-{claimed["id"]}').mkdir()
                    a.worker.transition(wdb,claimed['id'],'needs_input' if decision=='no_patch' else 'ready_for_review')
                with patch.object(a,'STATE',root),patch.object(a.worker,'command'),patch.object(a.worker,'git_output',return_value='a'*40),patch.object(a,'inspect_task',return_value=result),patch.object(a.worker,'run_job',side_effect=fake_repair) as repair,patch.object(a,'GitHub'),patch.object(a,'publish_repair',return_value='https://github.com/example/pull/1') as publish:
                    a.process(db,job,data,api,self.policy)
                    state=db.execute('SELECT state FROM attempts').fetchone()[0]
                    if decision=='ready':
                        self.assertEqual(state,'pr_open');repair.assert_called_once();publish.assert_called_once()
                        self.assertTrue((root/f'attempt-{job}'/'repair').is_dir())
                        self.assertIn('https://github.com/example/pull/1',api.saved[0]['comment_text'])
                    elif decision=='no_patch':
                        self.assertEqual(state,'failed');repair.assert_called_once();publish.assert_not_called()
                        self.assertIn('operator must inspect',api.saved[0]['comment_text'])
                        self.assertNotIn('Please clarify',api.saved[0]['comment_text'])
                    else:
                        self.assertEqual(state,'waiting_for_input');repair.assert_not_called();publish.assert_not_called()
                        self.assertIn('Which filter?',api.saved[0]['comment_text'])
                    self.assertFalse(a.can_start(db,a.snapshot(self.task,api.saved),self.policy))
                db.close()

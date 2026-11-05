import importlib.util
from pathlib import Path
import unittest
from copy import deepcopy
spec=importlib.util.spec_from_file_location('incidents',Path(__file__).parents[1]/'harness/incidents.py')
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)

class FakeAPI:
    def __init__(self):self.tasks=[];self.creates=0;self.updates=0
    def open_tasks(self):return self.tasks
    def create(self,incident):
        self.creates+=1
        task={'id':str(self.creates),'description':incident['description']}
        self.tasks.append(task);return task
    def update(self,task,description):self.updates+=1;task['description']=description

class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.e={'result':'failure','sha':'a'*40,'runId':'123','runAttempt':'1','url':i.SITE,'identityBefore':'success','identityAfter':'success'}
        self.r={'suites':[{'file':'tests/search.ts','specs':[{'title':'search','tests':[{'status':'unexpected','results':[{'error':{'message':'expect(locator).toHaveCount: expected 6 got 0'}}]}]}]}]}
    def test_repeat_run_does_not_create_or_append(self):
        api=FakeAPI();incident=i.make_incident(self.e,self.r)
        self.assertEqual(i.publish(api,incident)['action'],'created')
        self.assertEqual(i.publish(api,incident)['action'],'already_reported')
        self.assertEqual((api.creates,api.updates),(1,0))
    def test_new_commit_updates_same_open_incident_preserving_notes(self):
        api=FakeAPI();i.publish(api,i.make_incident(self.e,self.r));api.tasks[0]['description']+='\nHuman note'
        self.e.update(sha='b'*40,runId='124')
        self.assertEqual(i.publish(api,i.make_incident(self.e,self.r))['action'],'updated')
        self.assertIn('Human note',api.tasks[0]['description'])
        self.assertEqual(api.creates,1)
    def test_new_failure_creates_distinct_incident(self):
        a=i.make_incident(self.e,self.r)
        self.r['suites'][0]['specs'][0]['title']='save'
        self.assertNotEqual(a['key'],i.make_incident(self.e,self.r)['key'])
    def test_identity_failure_is_not_application_bug(self):
        self.e['identityAfter']='failure'
        self.assertEqual(i.make_incident(self.e,self.r)['classification'],'infrastructure-or-unknown')
    def test_missing_report_is_infrastructure(self):
        self.assertEqual(i.make_incident(self.e,{})['classification'],'infrastructure-or-unknown')
    def test_browser_launch_failure_is_infrastructure(self):
        self.r['suites'][0]['specs'][0]['tests'][0]['results'][0]['error']['message']='browserType.launch missing executable'
        self.assertEqual(i.make_incident(self.e,self.r)['classification'],'infrastructure-or-unknown')
    def test_flaky_success_not_reported_as_assertion_failure(self):
        self.r['suites'][0]['specs'][0]['tests'][0]['status']='flaky'
        self.assertEqual(i.failures(self.r),[])
    def test_success_never_creates_task(self):
        self.e['result']='success';api=FakeAPI()
        self.assertEqual(i.publish(api,i.make_incident(self.e,self.r))['action'],'no_failure')
        self.assertEqual(api.creates,0)
    def test_rehearsal_is_labelled_and_separate(self):
        actual=i.make_incident(self.e,self.r)
        self.e['rehearsal']=True
        rehearsal=i.make_incident(self.e,self.r)
        self.assertNotEqual(actual['key'],rehearsal['key'])
        self.assertIn('Reporting rehearsal',rehearsal['name'])
        self.assertIn('intentional test failure',rehearsal['description'])
    def test_wrong_target_rejected(self):
        self.e['url']='https://other.example/'
        with self.assertRaises(ValueError):i.make_incident(self.e,self.r)
    def test_duplicate_matches_stop_writes(self):
        api=FakeAPI();incident=i.make_incident(self.e,self.r);i.publish(api,incident)
        api.tasks.append(deepcopy(api.tasks[0]))
        with self.assertRaises(ValueError):i.publish(api,incident)
        self.assertEqual(api.updates,0)
    def test_every_incident_requires_triage(self):
        self.assertIn(i.TRIAGE,i.make_incident(self.e,self.r)['description'])

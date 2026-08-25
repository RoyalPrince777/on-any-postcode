import unittest
from gates import app, db, uid
from background_258 import register_background_258

if 'background_258' not in app.blueprints:
    register_background_258(app, db, uid)


class Background258(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client(); self.h={'X-Link-User':'1'}

    def test_protocol_contract(self):
        r=self.c.get('/api/258')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['runtime'],'24/7_background_worker')
        self.assertEqual(r.json['authority'],'human_final')
        self.assertFalse(r.json['autonomous_real_world_execution'])
        self.assertIn('hrm_audit',r.json['safe_job_types'])

    def test_jobs_require_auth(self):
        self.assertEqual(self.c.post('/api/258/jobs',json={'job_type':'health_probe'}).status_code,401)
        self.assertEqual(self.c.get('/api/258/jobs').status_code,401)

    def test_safe_job_can_queue(self):
        r=self.c.post('/api/258/jobs',headers=self.h,json={'job_type':'health_probe','payload':'ci'})
        self.assertEqual(r.status_code,202)
        self.assertTrue(r.json['queued'])
        self.assertEqual(r.json['protocol'],'25:8')

    def test_sensitive_job_fails_closed(self):
        r=self.c.post('/api/258/jobs',headers=self.h,json={'job_type':'transfer_money'})
        self.assertEqual(r.status_code,403)
        self.assertEqual(r.json['status'],'blocked_human_approval_required')
        self.assertFalse(r.json['queued'])

    def test_health_is_truthful_about_worker(self):
        r=self.c.get('/api/258/health')
        self.assertEqual(r.status_code,200)
        self.assertIn('worker_live',r.json)
        self.assertEqual(r.json['authority'],'human_final')


if __name__=='__main__': unittest.main()

import unittest
from gates import app, db, uid
from oap_intelligence import register_oap_intelligence

if 'oap_intelligence' not in app.blueprints:
    register_oap_intelligence(app, db, uid)


class OAPIntelligence(unittest.TestCase):
    def setUp(self):
        self.c=app.test_client()

    def test_health_and_authority(self):
        r=self.c.get('/api/intelligence/health')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['authority'],'human_final')
        self.assertFalse(r.json['autonomous_real_world_execution'])
        self.assertTrue(r.json['adaptive'])
        self.assertTrue(r.json['coherent'])

    def test_parent_child_structure(self):
        r=self.c.get('/api/intelligence')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['parent'],'SMI')
        for child in ['oap_world_intelligence','earth_intelligence','continent_intelligence','country_intelligence','universe_intelligence']:
            self.assertIn(child,r.json['children'])

    def test_adaptive_coherence_contract(self):
        r=self.c.get('/api/intelligence/adaptive-coherence')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['adaptive'])
        self.assertTrue(r.json['coherent'])
        self.assertEqual(r.json['conflict_policy'],'hold_and_reconcile_before_propagation')
        self.assertEqual(r.json['learning_state'],'purple_until_verified')
        self.assertFalse(r.json['autonomous_real_world_execution'])
        self.assertEqual(r.json['authority'],'human_final')
        self.assertIn('adapt_to_verified_evidence',r.json['rules'])
        self.assertIn('preserve_hierarchy_and_permissions',r.json['rules'])

    def test_world_hierarchy_local_first(self):
        r=self.c.get('/api/world-intelligence')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['local_first'])
        self.assertTrue(r.json['no_level_skipping'])
        self.assertTrue(r.json['adaptive'])
        self.assertTrue(r.json['coherent'])
        self.assertEqual(r.json['hierarchy'][0],'postcode')
        self.assertEqual(r.json['hierarchy'][-2],'earth')
        self.assertEqual(r.json['hierarchy'][-1],'universe')

    def test_earth_intelligence(self):
        r=self.c.get('/api/earth-intelligence')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['parent'],'OAP World Intelligence')
        self.assertEqual(r.json['scope'],'earth')
        self.assertIn('continent_intelligence',r.json['children'])
        self.assertTrue(r.json['evidence_first'])
        self.assertTrue(r.json['prediction_requires_verified_sources'])
        self.assertTrue(r.json['adaptive'])
        self.assertTrue(r.json['coherent'])
        self.assertEqual(r.json['authority'],'human_final')

    def test_africa_continent_intelligence(self):
        r=self.c.get('/api/continent-intelligence?continent=Africa')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['parent'],'Earth Intelligence')
        self.assertEqual(r.json['continent'],'Africa')
        self.assertEqual(r.json['child'],'Country Intelligence')
        self.assertIn('sika_africa',r.json['organs'])
        self.assertIn('movement',r.json['organs'])
        self.assertFalse(r.json['united_states_of_africa']['government_claim'])
        self.assertFalse(r.json['united_states_of_africa']['legal_state_claim'])
        self.assertFalse(r.json['sika_africa']['legal_tender_claim'])
        self.assertFalse(r.json['sika_africa']['bank_claim'])
        self.assertEqual(r.json['authority'],'human_final')

    def test_country_intelligence_local_hierarchy(self):
        r=self.c.get('/api/country-intelligence?continent=Africa&country=Ghana')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['parent'],'Continent Intelligence')
        self.assertEqual(r.json['country'],'Ghana')
        self.assertEqual(r.json['continent'],'Africa')
        self.assertEqual(r.json['hierarchy'][0],'country')
        self.assertEqual(r.json['hierarchy'][-1],'spot')
        self.assertTrue(r.json['local_first'])
        self.assertTrue(r.json['no_level_skipping'])
        self.assertFalse(r.json['precise_location_default'])

    def test_universe_intelligence(self):
        r=self.c.get('/api/universe-intelligence')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['parent'],'Earth Intelligence')
        self.assertEqual(r.json['scope'],'universe')
        self.assertTrue(r.json['scientific_claims_require_verified_sources'])
        self.assertTrue(r.json['earth_remains_home_context'])
        self.assertTrue(r.json['adaptive'])
        self.assertTrue(r.json['coherent'])
        self.assertFalse(r.json['autonomous_real_world_execution'])
        self.assertEqual(r.json['authority'],'human_final')

    def test_context_is_evidence_not_prediction(self):
        r=self.c.get('/api/world-intelligence/context?scope=postcode&value=SE15')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['context']['prediction'])
        self.assertFalse(r.json['context']['precise_location_used'])
        self.assertTrue(r.json['context']['adaptive'])
        self.assertTrue(r.json['context']['coherent'])
        self.assertEqual(r.json['context']['source_mode'],'live_oap_records')

    def test_invalid_scope_rejected(self):
        self.assertEqual(self.c.get('/api/world-intelligence/context?scope=planet').status_code,400)


if __name__=='__main__': unittest.main()

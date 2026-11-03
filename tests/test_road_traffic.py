import copy
import math
import unittest
from backend.runway_scenarios import geography, build_demonstration
from backend.road_traffic import build_road_traffic, road_pose
from backend.evidence import received_facts

class RoadTrafficTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.geo=geography()

    def test_seeded_loops_close_and_keep_vehicle_spacing(self):
        for seed in range(20):
            t=build_road_traffic(self.geo,seed)
            self.assertEqual(t,build_road_traffic(self.geo,seed))
            self.assertEqual(len(t['vehicles']),6)
            r=t['routes'][0];p=r['points']
            self.assertEqual({k:p[0][k] for k in ('x','z','heading')},{k:p[-1][k] for k in ('x','z','heading')})
            self.assertGreater(r['lengthMetres'],1000);self.assertLess(r['lengthMetres'],1050)
            self.assertTrue(all(a['distanceMetres']<b['distanceMetres'] for a,b in zip(p,p[1:])))
            for now in range(0,3601,30):
                poses=[road_pose(t,v,now) for v in t['vehicles']]
                for i,a in enumerate(poses):
                    for b in poses[i+1:]:self.assertGreater(math.hypot(a['x']-b['x'],a['z']-b['z'])*1000,12)

    def test_source_time_repeatability_pause_wrap_and_speed(self):
        t=build_road_traffic(self.geo,17);r=t['routes'][0];v=t['vehicles'][0]
        for now in (0,10,60,123.45,3599.9):
            a=road_pose(t,v,now);b=road_pose(t,v,now)
            self.assertEqual(a,b)
            later=road_pose(t,v,now+.01)
            self.assertLessEqual(math.hypot(a['x']-later['x'],a['z']-later['z'])*1000,.03001)
            self.assertLess(abs((later['heading']-a['heading']+180)%360-180),3)
        wrap=(r['lengthMetres']-v['offsetMetres'])/r['speedMetresPerSecond']
        a,b=road_pose(t,v,wrap-.001),road_pose(t,v,wrap+.001)
        self.assertLess(math.hypot(a['x']-b['x'],a['z']-b['z'])*1000,.0061)
        self.assertLess(abs((a['heading']-b['heading']+180)%360-180),1)

    def test_ambient_geometry_cannot_create_report_facts(self):
        w=build_demonstration(17,'rejected_takeoff')[0];old=copy.deepcopy(w);old.pop('ambientTraffic')
        for time in (0,60,120,3600):self.assertEqual(received_facts(w,time),received_facts(old,time))
        self.assertTrue(all(e['aircraftId'] not in {v['id'] for v in w['ambientTraffic']['vehicles']} for e in w['events']))
        self.assertIsNone(build_road_traffic({},17))

    def test_versioned_map_preserves_dimensions_sites_and_source_kinds(self):
        g=self.geo;self.assertEqual(g['version'],2);self.assertEqual(len(g['features']),850)
        self.assertEqual(len([f for f in g['features'] if f['kind']=='jet_bridge']),15)
        self.assertEqual(len([f for f in g['features'] if f['kind']=='water']),24)
        t2=next(f for f in g['features'] if f['id']=='osm-way-133146402');self.assertEqual(t2['heightMetres'],40)
        self.assertEqual(g['referenceSites'][0]['renderAs'],'outline-only')
        self.assertTrue(g['referenceSites'][0]['holes'])
        for f in (f for f in g['features'] if f.get('holes')):self.assertTrue(f['roofTriangles'])

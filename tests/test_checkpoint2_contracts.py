"""PROCEDURAL: regressions for the Bluebird handoff and C02 evidence gates."""
from dataclasses import replace
import unittest

from backend.bluebird_inbound import BLUEBIRD_787, HANDOFF
from backend.evidence import build_context, validate_scenario
from backend.fleet_scenarios import build_fleet
from backend.stand_clearance_lesson import build_stand_clearance_lesson
from backend.training_session import TrainingSession
from backend.typed_claims import Claim, check_claim


class Checkpoint2Contracts(unittest.TestCase):
    def test_bluebird_keeps_sector_tracks_and_airport_authority_separate(self):
        driver = TrainingSession(17, BLUEBIRD_787, "continuous")
        paired = driver.scenario
        baseline, _, _ = build_fleet(17, "fleet_b787_priority_landing")
        validate_scenario(paired)
        self.assertEqual(paired["aircraft"][0]["visibleFrom"], HANDOFF)
        self.assertEqual(paired["aircraft"][0]["waypoints"][0]["t"], HANDOFF)
        during_gap = build_context(paired, "A1", 75)
        self.assertEqual({fact["source"] for fact in during_gap["facts"]}, {"bluebird-synthetic-observation"})
        self.assertEqual({fact["flightInstance"] for fact in during_gap["facts"]}, {"TRN101"})
        self.assertEqual(max(fact["receiptTime"] for fact in during_gap["facts"]), 60)
        for cutoff in (0, *(cue["at"] for cue in baseline["demoQuestions"])):
            actual = build_context(paired, "A1", cutoff + HANDOFF)["facts"]
            expected = build_context(baseline, "A1", cutoff)["facts"]
            self.assertEqual(
                [(f["fact_id"], f["value"], f["status"]) for f in actual if f["source"] == "exercise-operations"],
                [(f["fact_id"], f["value"], f["status"]) for f in expected],
            )

    def test_current_release_requires_correct_scope_and_receipt(self):
        world, _, _ = build_stand_clearance_lesson(17)
        release = next(r for r in world["events"] if r["receiptTime"] == 150)
        claim = Claim(world["scenarioId"], "A3", "TRN103", "movement_condition",
                      release["facts"][0]["value"], (release["id"],))
        self.assertEqual(check_claim(world, 149.999, claim).status, "unknown")
        self.assertEqual(check_claim(world, 150, claim).status, "supported")
        self.assertEqual(check_claim(world, 150, replace(claim, flight="TRN102")).rule, "wrong_flight")
        self.assertEqual(check_claim(world, 150, replace(claim, run_id="old")).rule, "wrong_run")

    def test_camera_citation_cannot_establish_movement_authority(self):
        world, _, _ = build_stand_clearance_lesson(17)
        frame = dict(captureId="rgb-90", runId=world["scenarioId"], aircraftId="A3",
                     flightInstance="TRN103", sourceTime=90, trackingValid=True, visibleVehicle="present")
        claim = Claim(world["scenarioId"], "A3", "TRN103", "visible_vehicle", "present", ("rgb-90",))
        self.assertEqual(check_claim(world, 90, claim, [frame]).status, "supported")
        self.assertEqual(check_claim(world, 91, claim, [frame]).status, "unknown")
        self.assertEqual(check_claim(world, 91, replace(claim, historical=True), [frame]).status, "supported")
        release = replace(claim, property="movement_condition", value="released")
        self.assertEqual(check_claim(world, 150, release, [frame]).status, "unknown")


if __name__ == "__main__":
    unittest.main()

"""Test suite for Team Goldo App."""
import csv
import io
import unittest

import main

DAMAGE_DONE_ROW = """[21:22:09.644] [@Lor'dan] [Tunneling Tentacle {3025271884087296}:13241000031137] [Storm {3647535335866368}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (2602 kinetic {836045448940873}) <6505>"""
DAMAGE_DONE_ROW_2 = """[21:22:10.644] [@Lor'dan] [Tunneling Tentacle {3025271884087296}:13241000031137] [Storm {3647535335866368}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (2602 kinetic {836045448940873}) <6505>"""
DAMAGE_DONE_MISSED_ROW = """[21:22:09.644] [@Lor'dan] [Tunneling Tentacle {3025271884087296}:13241000031137] [Storm {3647535335866368}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (0 -miss {836045448945502}) <1>"""
DAMAGE_DONE_DODGED_ROW = """[21:22:09.644] [@Lor'dan] [Tunneling Tentacle {3025271884087296}:13241000031137] [Storm {3647535335866368}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (0 -dodge {836045448945505}) <1>"""
DAMAGE_RECVD_ROW = """[21:22:09.775] [Tunneling Tentacle {3025271884087296}:13241000031137] [@Lor'dan] [Slap {3025808754999296}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (5083 kinetic {836045448940873}) <5083>"""
DAMAGE_SHIELDED_ROW = """[21:22:09.775] [Tunneling Tentacle {3025271884087296}:13241000031137] [@Lor'dan] [Slap {3025808754999296}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (2776 kinetic {836045448940873} -shield {836045448945509} (22703 absorbed {836045448945511})) <2776>"""
APPLY_FORCE_ABS_ROW = """[21:27:14.202] [@Meyrah] [@Lor'dan] [Force Armor {812736661422080}] [ApplyEffect {836045448945477}: Force Armor {812736661422080}] ()\n"""
DAMAGE_FORCE_ABSORBED_ROWS = ["""[21:29:59.374] [The Terror From Beyond {3025233229381632}:13241000114922] [@Lor'dan] [Monsterous Swipe {3025456567681338}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (8973 kinetic {836045448940873} (8973 absorbed {836045448945511})) <8973>\n""",
"""[21:29:59.374] [The Terror From Beyond {3025233229381632}:13241000114922] [@Lor'dan] [Monsterous Swipe {3025456567681338}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (4362 kinetic {836045448940873} -shield {836045448945509} (4362 absorbed {836045448945511})) <4362>\n""",
"""[21:29:59.374] [The Terror From Beyond {3025233229381632}:13241000114922] [@Lor'dan] [Monsterous Swipe {3025456567681338}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (0 -dodge {836045448945505}) <1>\n""",
"""[21:29:59.374] [The Terror From Beyond {3025233229381632}:13241000114922] [@Lor'dan] [Monsterous Swipe {3025456567681338}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (4362 kinetic {836045448940873} -shield {836045448945509} (638 absorbed {836045448945511})) <4362>\n""",
"""[21:29:59.374] [The Terror From Beyond {3025233229381632}:13241000114922] [@Lor'dan] [Monsterous Swipe {3025456567681338}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (0 -dodge {836045448945505}) <1>\n"""]
DAMAGE_RECVD_MISSED = """[21:30:02.541] [The Terror From Beyond {3025233229381632}:13241000114922] [@Lor'dan] [Monsterous Swipe {3025456567681338}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (0 -miss {836045448945502}) <1>"""
DAMAGE_RECVD_DODGED = """[21:36:18.104] [Tunneling Tentacle {3025271884087296}:13241000211746] [@Lor'dan] [Slap {3025808754999296}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (0 -dodge {836045448945505}) <1>"""
HEAL_RECVD = """[21:40:55.032] [@Lor'dan] [@Lor'dan] [Into the Fray {3172499068026880}] [ApplyEffect {836045448945477}: Heal {836045448945500}] (4480) <5600>"""
NEGATIVE_THREAT_ROW="""[21:59:39.846] [@Lor'dan] [Pearl {3374109127868416}:9182000098644] [Swoop {3379568031301632}] [Event {836045448945472}: ModifyThreat {836045448945483}] () <-1492337>"""


class TestParserFunctions(unittest.TestCase):

    def setUp(self):
        self.parser = main.Parser()
        self.parser.in_combat = True
        self.parser.ignore_pull = False
        self.parser.player_id = "Lor'dan"
        self.parser.healer_id = None
        self.parser.pull = dict([
            ('damage_done', {self.parser.player_id: {'amount': 0}}),
            ('damage_received', {self.parser.player_id: {
                'attackers': dict(),
                'amount': 0}, }),
            ('heal', {self.parser.player_id: 0}),
            ('threat', {self.parser.player_id: 0}),
            ('target', None),
            ('players', set([self.parser.player_id])), ])

    def test_damage_done(self):
        file_ = io.StringIO(DAMAGE_DONE_ROW)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_done"]["Lor'dan"]["amount"], 2602)
        self.assertEqual(self.parser.pull["threat"]["Lor'dan"], 6505)

    def test_damage_done_missed(self):
        file_ = io.StringIO(DAMAGE_DONE_MISSED_ROW)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_done"]["Lor'dan"]["amount"], 0)
        self.assertEqual(self.parser.pull["damage_done"]["Lor'dan"]["Storm "]["missed"], 1)

    def test_damage_done_dodged(self):
        file_ = io.StringIO(DAMAGE_DONE_DODGED_ROW)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_done"]["Lor'dan"]["amount"], 0)
        self.assertEqual(self.parser.pull["damage_done"]["Lor'dan"]["Storm "]["dodged"], 1)

    def test_damage_received(self):
        file_ = io.StringIO(DAMAGE_RECVD_ROW)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["Tunneling Tentacle "]["Slap "]["total_damage"], 5083)

    def test_damage_receveived_shielded(self):
        file_ = io.StringIO(DAMAGE_SHIELDED_ROW)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["Tunneling Tentacle "]["Slap "]["shielded"], 1)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["Tunneling Tentacle "]["Slap "]["total_damage"], 2776)

    def test_damage_received_absorbed(self):
        file_ = io.StringIO()
        file_.writelines(APPLY_FORCE_ABS_ROW)
        file_.writelines(DAMAGE_FORCE_ABSORBED_ROWS)
        file_.seek(0)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["The Terror From Beyond "]["Monsterous Swipe "]["total_damage"], 17697)
        self.assertEqual(self.parser.pull["heal"]["Meyrah"], 13973)

    def test_damage_received_missed(self):
        file_ = io.StringIO()
        file_.writelines(DAMAGE_RECVD_MISSED)
        file_.seek(0)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["The Terror From Beyond "]["Monsterous Swipe "]["total_damage"], 0)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["The Terror From Beyond "]["Monsterous Swipe "]["missed"], 1)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["The Terror From Beyond "]["Monsterous Swipe "]["hit"], 0)

    def test_damage_received_dodged(self):
        file_ = io.StringIO()
        file_.writelines(DAMAGE_RECVD_DODGED)
        file_.seek(0)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["Tunneling Tentacle "]["Slap "]["total_damage"], 0)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["Tunneling Tentacle "]["Slap "]["dodged"], 1)
        self.assertEqual(self.parser.pull["damage_received"]["Lor'dan"]["attackers"]["Tunneling Tentacle "]["Slap "]["hit"], 0)

    def test_heal_received(self):
        file_ = io.StringIO()
        file_.writelines(HEAL_RECVD)
        file_.seek(0)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["heal"]["Lor'dan"], 4480)
        self.assertEqual(self.parser.pull["threat"]["Lor'dan"], 5600)

    def test_threat(self):
        file_ = io.StringIO()
        file_.writelines(DAMAGE_DONE_ROW+"\n")
        file_.writelines(DAMAGE_DONE_ROW_2)
        file_.seek(0)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["threat"]["Lor'dan"], 13010)

    def test_negative_threat(self):
        file_ = io.StringIO()
        file_.writelines(DAMAGE_DONE_ROW+"\n")
        file_.writelines(DAMAGE_DONE_ROW_2+"\n")
        file_.writelines(NEGATIVE_THREAT_ROW+"\n")
        file_.seek(0)
        log_file = csv.DictReader(
            file_, fieldnames=main.CSV_HEADER, delimiter=']',
            skipinitialspace=True)
        for row in log_file:
            self.parser.dispatch_row(row)
        self.assertEqual(self.parser.pull["threat"]["Lor'dan"], -1479327)


if __name__ == '__main__':
    unittest.main()

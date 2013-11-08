""" Log combat parser for team goldo app."""
# -*- coding: utf8 -*-

import csv
import datetime
import logging
import string

import webapp2
import gviz_api
from goldo_templates import (chart_page_template, table_page_template,
                             main_page_template)
from goldo_mappings import (
    ABSORB, DODGE, SHIELD, PARRY, ENTER_COMBAT,
    FORCE_ARMOR, PLAYER_TAG, DAMAGE_DONE, DAMAGE_RECEIVED, DEATH,
    LEAVE_COMBAT, HEAL, REVIVE, NO_DAMAGE)
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

CSV_HEADER = ['time', 'from', 'to', 'skill', 'effect', 'amount']


class MainPage(webapp2.RequestHandler):
    def get(self):
        upload = blobstore.create_upload_url('/upload')
        self.response.out.write(main_page_template.format(upload))


#TODO: improve ?
class Raid:
    raid = list()


class Upload(blobstore_handlers.BlobstoreUploadHandler):
    def actual_time(self, time, date):
            """Returns the actual time"""
            actual_time = datetime.datetime.strptime(
                string.join((date, time)), '%Y-%m-%d %H:%M:%S.%f')
            return actual_time

    def post(self):
        upload_files = self.get_uploads('file')
        try:
            myFile = upload_files[0]
        except IndexError:
            self.redirect('/')
            return False
        #TODO: add file validation
        try:
            uploaded_file = myFile.open()
            current_date = myFile.filename.split('_', 2)[1]
        except (IndexError, IOError):
            self.redirect('/')
        else:
            log_file = csv.DictReader(
                uploaded_file, fieldnames=CSV_HEADER, delimiter=']',
                skipinitialspace=True)
            self.parse(current_date, log_file)
            uploaded_file.close()
            self.redirect('/results')

    def parse_enter_combat(self, row, current_date):
        self.in_combat = True
        self.player_id = row['from'][2:]
        self.pull_start_time = self.actual_time(row['time'][1:], current_date)
        pull = dict([('start', self.pull_start_time),
                    ('damage_done', {self.player_id: {'amount': 0}}),
                    ('damage_received', {self.player_id: {
                        'attackers': dict(),
                        'amount': 0}, }),
                    ('heal', {self.player_id: 0}),
                    ('target', None),
                    ('players', set([self.player_id])), ])
        logging.debug("Entering New Combat: {0} - {1}".format(
            row['time'][1:], row['from'][2:]))
        return pull

    def parse_damage_done(self, row, pull):
        if NO_DAMAGE in row['amount']:
            return pull
        player_damage_dict = pull['damage_done'][self.player_id]
        pull['target'] = row['to'][1:].split('{', 1)[0]
        skill = row['skill'][1:].split('{', 1)[0]
        damage_amount_done = row['amount'][1:].split(None, 1)[0]
        player_damage_dict.setdefault(
            skill, {'hit': 0, 'dodged': 0, 'missed': 0, 'total_damage': 0})
        if not damage_amount_done.isdigit():
            damage_amount_done = damage_amount_done[:-1]
        if int(damage_amount_done) is 0:
            if DODGE in row['amount']:
                player_damage_dict[skill]['dodged'] += 1
            else:
                player_damage_dict[skill]['missed'] += 1
        else:
            player_damage_dict['amount'] += int(damage_amount_done)
            player_damage_dict[skill]['hit'] += 1
            player_damage_dict[skill]['total_damage'] += int(
                damage_amount_done)
        return pull

    def parse_heal(self, row, pull):
        heal_amount = row['amount'][1:].split(None, 1)[0][:-1]
        try:
            pull['heal'][self.player_id] += int(heal_amount)
        except ValueError:
            pull['heal'][self.player_id] += int(heal_amount[:-1])
        return pull

    def parse_damage_received(self, row, pull):
        player_damage_dict = \
            pull['damage_received'][self.player_id]['attackers']
        attacker = row['from'][1:].split('{', 1)[0]
        skill = row['skill'][1:].split('{', 1)[0]
        raw_damage, dmg_type = row['amount'][1:].split(None, 2)[:2]
        player_damage_dict.setdefault(attacker, dict())
        player_damage_dict[attacker].setdefault(
            skill, {'hit': 0, 'dodged': 0, 'shielded': 0, 'total_damage': 0})
        if raw_damage != '0':
            player_damage_dict[attacker][skill].setdefault(
                'dmg_type', dmg_type)
        if not raw_damage.isdigit():
            raw_damage = raw_damage[:-1]
        if ABSORB in row['amount']:
            absorbed_damage = row['amount'][1:].partition('(')[2].split(
                ABSORB, 1)[0].split(None, 1)[0]
            if self.healer_id in pull['heal']:
                pull['heal'][self.healer_id] += int(absorbed_damage)
            else:
                pull['heal'][self.healer_id] = int(absorbed_damage)
                row['amount'][1:].partition('(')[2].split(
                    ABSORB, 1)[0].split(None, 1)[0]
            if self.healer_id in pull['heal']:
                pull['heal'][self.healer_id] += int(absorbed_damage)
            else:
                pull['heal'][self.healer_id] = int(absorbed_damage)
            if self.healer_id in pull['heal']:
                pull['heal'][self.healer_id] += int(absorbed_damage)
            else:
                pull['heal'][self.healer_id] = int(absorbed_damage)
        if (DODGE or PARRY) in row['amount']:
            player_damage_dict[attacker][skill]['dodged'] += 1
        elif SHIELD in row['amount']:
            player_damage_dict[attacker][skill]['shielded'] += 1
        else:
            player_damage_dict[attacker][skill]['hit'] += 1
        player_damage_dict[attacker][skill]['total_damage'] += int(
            raw_damage)
        pull['damage_received'][self.player_id]['amount'] += int(
            raw_damage)
        return pull

    def parse_exit_combat(self, row, pull, current_date):
        pull['stop'] = self.pull_end_time
        Raid.raid.append(pull)
        logging.debug("Pull Dict: {}".format(pull))

    def initialize_pull(self):
        self.in_combat = False
        self.player_id = None
        self.healer_id = None
        self.pull_start_time = None
        self.pull_end_time = None

    def parse(self, current_date, log_file):
        self.player_id = 'None'
        self.initialize_pull()
        for row in log_file:
            row = {key: unicode(row_field, 'iso-8859-1').encode('utf-8')
                   for key, row_field in row.items()}
            if not self.in_combat and ENTER_COMBAT in row['effect']:
                logging.debug("Entering Combat:{0} - {1}".format(
                    row['time'][1:], row['from'][2:]))
                pull = self.parse_enter_combat(row, current_date)
                continue
            elif FORCE_ARMOR in row['effect'] and PLAYER_TAG in row['to']:
                self.healer_id = row['from'][2:]
                continue
            elif self.in_combat and DAMAGE_DONE in row['effect'] and \
                    self.player_id in row['from']:
                pull = self.parse_damage_done(row, pull)
                continue
            elif self.in_combat and HEAL \
                in row['effect'] and self.player_id in row['from'] and not \
                    REVIVE in row['skill']:
                pull = self.parse_heal(row, pull)
                continue
            elif self.in_combat and DAMAGE_RECEIVED in row['effect'] and \
                    self.player_id in row['to']:
                pull = self.parse_damage_received(row, pull)
                continue
            elif self.in_combat and self.player_id in row['to'] and \
                    DEATH in row['effect'] or LEAVE_COMBAT in row['effect']:
                self.pull_end_time = self.actual_time(
                    row['time'][1:], current_date)
                logging.debug("Death:{0} - \ {1}".format(
                    row['time'][1:], row['from'][2:]))
                self.parse_exit_combat(row, pull, current_date)
                self.initialize_pull()
                continue
        return True


class Result(webapp2.RequestHandler):

    def get(self):
        # Creating the data
        description = {"pull_start_time": ("datetime", "Pull Start Time"),
                       "total_damage": ("number", "Total Damage"),
                       "players_number": ("number", "Number of Player(s)"),
                       "pull_id": ("number", "Pull Id"),
                       "pull_duration": ("timeofday", "Pull Duration"),
                       "pull_target": ("string", "Pull Target"),
                       }
        data = list()
        for pull in Raid.raid:
                if pull['stop'] - pull['start'] < datetime.timedelta(0):
                    pull['stop'] = pull['stop'] + datetime.timedelta(days=1)
                data.append(
                    {"pull_start_time": pull['start'],
                     "total_damage": sum(player['amount'] for player in
                                         pull['damage_done'].values()),
                     "players_number": len(pull['players']),
                     "pull_id": Raid.raid.index(pull),
                     "pull_duration":
                     datetime.datetime.min + (pull['stop'] - pull['start']),
                     "pull_target": pull['target'], }
                )

        #Loading it into gviz_api.DataTable
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)

        #Creating a JSon string
        json_pull = data_table.ToJSon(
            columns_order=("pull_id", "pull_start_time", "pull_target",
                           "pull_duration", "total_damage", "players_number"),
            order_by=("pull_start_time", "asc"))

        #Putting the JSon string into the template
        self.response.out.write(
            table_page_template.format(json_pull=json_pull))


class Chart(webapp2.RequestHandler):
    def get(self, chart_id):
        pull = Raid.raid[int(chart_id)]

        # Creating the data
        skill_table_description = {"player": ("string", "Player"),
                                   "skill": ("string", "Skill"),
                                   "hit": ("number", "Hits"),
                                   "missed": ("number", "Missed"),
                                   "dodged": ("number", "Dodged"),
                                   "total_damage": (
                                       "number", "Total Damage")}
        skill_data = list()
        for player, skill_dict in pull['damage_done'].items():
            for skill, result in skill_dict.items():
                if skill is not 'amount':
                    skill_data.append(
                        {"player": player,
                         "skill": skill,
                         "hit": result.get('hit'),
                         "dodged": result.get('dodged'),
                         "missed": result.get('missed'),
                         "total_damage": result.get('total_damage')}
                    )

        #Loading it into gviz_api.DataTable
        skill_data_table = gviz_api.DataTable(skill_table_description)
        skill_data_table.LoadData(skill_data)

        # Creating the data
        dmg_table_description = {"player": ("string", "Player"),
                                 "attacker": ("string", "Attacker"),
                                 "skill": ("string", "Skill"),
                                 "hit": ("number", "Hits"),
                                 "shielded": ("number", "Shielded"),
                                 "dodged": ("number", "Dodged"),
                                 "total_damage": ("number", "Total Damage"),
                                 "dmg_type": ("string", "Damage Type")}
        dmg_data = list()
        for player, attacker_dict in pull['damage_received'].items():
            for attacker, skill_dict in attacker_dict['attackers'].items():
                if attacker is not 'amount':
                    for skill, result in skill_dict.items():
                        dmg_data.append(
                            {"player": player,
                             "attacker": attacker,
                             "skill": skill,
                             "hit": result.get('hit'),
                             "dodged": result.get('dodged'),
                             "shielded": result.get('shielded'),
                             "total_damage": result.get('total_damage'),
                             "dmg_type": result.get('dmg_type')}
                        )

        #Loading it into gviz_api.DataTable
        dmg_data_table = gviz_api.DataTable(dmg_table_description)
        dmg_data_table.LoadData(dmg_data)
        # Creating the data
        chart_dmg_description = {"player": ("string", "Player"),
                                 "damage": ("number", "Damage")}
        chart_dmg_data = list()
        bar_dmg_description = {"player": ("string", "Player"),
                               "dps": ("number", "DPS")}
        bar_dmg_data = list()
        chart_heal_description = {"player": ("string", "Player"),
                                  "heal": ("number", "heal")}
        chart_heal_data = list()
        bar_heal_description = {"player": ("string", "Player"),
                                "hps": ("number", "HPS")}
        bar_heal_data = list()
        chart_dmg_received_description = {"player": ("string", "Player"),
                                          "damage_received":
                                          ("number", "Damage Received")}
        chart_dmg_received_data = list()

        for player, damage_dict in pull['damage_done'].iteritems():
            chart_dmg_data.append(
                {"player": player, "damage": damage_dict['amount']})
            bar_dmg_data.append(
                {"player": player, "dps": damage_dict['amount'] / (
                    pull['stop'] - pull['start']).total_seconds()})

        for player, heal in pull['heal'].iteritems():
            chart_heal_data.append(
                {"player": player, "heal": heal})
            bar_heal_data.append(
                {"player": player,
                 "hps": heal / (pull['stop'] - pull['start']).total_seconds()})

        for player, damage in pull['damage_received'].iteritems():
            chart_dmg_received_data.append(
                {"player": player, "damage_received": damage['amount']})

        # Loading it into gviz_api.DataTable
        pie_dmg_data_table = gviz_api.DataTable(chart_dmg_description)
        pie_dmg_data_table.LoadData(chart_dmg_data)

        bar_dmg_data_table = gviz_api.DataTable(bar_dmg_description)
        bar_dmg_data_table.LoadData(bar_dmg_data)

        pie_heal_data_table = gviz_api.DataTable(chart_heal_description)
        pie_heal_data_table.LoadData(chart_heal_data)

        bar_heal_data_table = gviz_api.DataTable(bar_heal_description)
        bar_heal_data_table.LoadData(bar_heal_data)

        pie_dmg_received_data_table = gviz_api.DataTable(
            chart_dmg_received_description)
        pie_dmg_received_data_table.LoadData(chart_dmg_received_data)

        # Creating a JSon string
        json_pie_dmg_chart = pie_dmg_data_table.ToJSon(
            columns_order=("player", "damage"))
        json_bar_dmg_chart = bar_dmg_data_table.ToJSon(
            columns_order=("player", "dps"))
        json_pie_heal_chart = pie_heal_data_table.ToJSon(
            columns_order=("player", "heal"))
        json_bar_heal_chart = bar_heal_data_table.ToJSon(
            columns_order=("player", "hps"))
        json_pie_dmg_received_chart = pie_dmg_received_data_table.ToJSon(
            columns_order=("player", "damage_received"))
        json_skill_data_table = skill_data_table.ToJSon(
            columns_order=(
                "player", "skill", "hit", "dodged", "missed", "total_damage"),
            order_by=("player", "skill"))
        json_dmg_data_table = dmg_data_table.ToJSon(columns_order=(
            "player", "attacker", "skill", "hit",
            "dodged", "shielded", 'total_damage', 'dmg_type'),
            order_by=("player", "attacker", "skill"))

        # Putting the JSon string into the template
        response = chart_page_template.format(
            pie_dmg=json_pie_dmg_chart,
            bar_dmg=json_bar_dmg_chart,
            pie_heal=json_pie_heal_chart,
            bar_heal=json_bar_heal_chart,
            pie_dmg_received=json_pie_dmg_received_chart,
            skill_table=json_skill_data_table,
            dmg_table=json_dmg_data_table)
        self.response.out.write(response)

app = webapp2.WSGIApplication([('/', MainPage), ('/upload',
                              Upload), ('/chart/(\d+)', Chart), ('/results',
                              Result)],
                              debug=True)

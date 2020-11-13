""" Log combat parser for team goldo app."""
# -*- coding: utf8 -*-

import csv
import datetime
import logging
import os
import json
import uuid

import gviz_api
from goldo_templates import (chart_page_template, table_page_template,
                             main_page_template)
from flask import Flask, render_template, request, redirect, Response
from werkzeug.utils import secure_filename
# Imports the Google Cloud client library
from google.cloud import datastore
from dateutil.tz import gettz
from dateutil.utils import default_tzinfo

from goldo_mappings import (
    ABSORB, DODGE, SHIELD, PARRY, ENTER_COMBAT,
    FORCE_ARMOR, PLAYER_TAG, DAMAGE_DONE, DAMAGE_RECEIVED, DEATH,
    LEAVE_COMBAT, HEAL, REVIVE, NO_DAMAGE)

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'txt'}
PARIS_TZ = gettz('Europe/Paris')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CSV_HEADER = ['time', 'from', 'to', 'skill', 'effect', 'amount']

# All conditions must be met before handling row
ROW_DISPATCH_DICT = {
    (('in_combat', False), ('effect', ENTER_COMBAT)):
    'parse_enter_combat',
    (('in_combat', True), ('effect', DAMAGE_DONE), ('from', 'player_id')):
    'parse_damage_done',
    (('in_combat', True), ('effect', DAMAGE_RECEIVED), ('to', 'player_id')):
    'parse_damage_received',
    (('effect', FORCE_ARMOR), ('to', PLAYER_TAG)):
    'parse_affect_healer',
    (('in_combat', True), ('effect', HEAL), ('from', 'player_id'), (
        'skill', REVIVE)): 'parse_heal',
    (('in_combat', True), ('effect', DEATH), ('to', 'player_id')):
    'parse_exit_combat',
    (('in_combat', True), ('effect', LEAVE_COMBAT), ('to', 'player_id')):
    'parse_exit_combat',
}

DMG_RCVD_DISPATCH_DICT = {
    ABSORB: 'absorb',
    DODGE: 'dodge_or_parry',
    PARRY: 'dodge_or_parry',
    SHIELD: 'shield',
}


@app.route('/')
def get():
    """GET method handler."""
    response = Response(main_page_template)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect("/")
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return redirect("/")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    with open(os.path.join(app.config['UPLOAD_FOLDER'], file.filename, ), "rt", encoding="ISO-8859-1") as file_:
        parser = Parser()
        parser.main(file_, file.filename)
    return redirect("/results")

class Parser():

    def actual_time(self, time, date):
        """Returns the actual time"""
        actual_time = datetime.datetime.strptime(
            ' '.join((date, time)), '%Y-%m-%d %H:%M:%S.%f')
        actual_time = default_tzinfo(actual_time, PARIS_TZ)
        return actual_time

    def main(self, uploaded_file, filename):
        """
        POST method handler: retrieve file, parse it and redirect to results.
        """
        try:
            self.current_date = filename.split('_', 2)[1]
        except (IndexError, IOError):
            self.redirect('/')
        else:
            log_file = csv.DictReader(
                uploaded_file, fieldnames=CSV_HEADER, delimiter=']',
                skipinitialspace=True)
            self.parse(log_file)
            uploaded_file.close()
            # self.redirect('/results')

    def parse_enter_combat(self, row):
        """Parse enter combat."""
        self.in_combat = True
        self.player_id = row['from'][2:]
        current_date = self.current_date
        self.pull_start_time = self.actual_time(row['time'][1:], current_date)
        self.pull = dict([
            ('start', self.pull_start_time),
            ('damage_done', {self.player_id: {'amount': 0}}),
            ('damage_received', {self.player_id: {
                'attackers': dict(),
                'amount': 0}, }),
            ('heal', {self.player_id: 0}),
            ('target', None),
            ('players', set([self.player_id])), ])
        logging.debug("Entering New Combat: {0} - {1}".format(
            row['time'][1:], row['from'][2:]))
        return True

    def parse_damage_done(self, row):
        """Parse damage done."""
        if NO_DAMAGE in row['amount']:
            return True
        player_damage_dict = self.pull['damage_done'][self.player_id]
        self.pull['target'] = row['to'][1:].split('{', 1)[0]
        skill = row['skill'][1:].split('{', 1)[0]
        damage_amount_done = row['amount'][1:].split(None, 1)[0]
        player_damage_dict.setdefault(
            skill, {'hit': 0, 'dodged': 0, 'missed': 0, 'total_damage': 0})
        try:
            damage_amount_done = int(damage_amount_done)
        except ValueError:
            damage_amount_done = int(damage_amount_done[:-1])
        if damage_amount_done == 0:
            if DODGE in row['amount']:
                player_damage_dict[skill]['dodged'] += 1
            else:
                player_damage_dict[skill]['missed'] += 1
        else:
            player_damage_dict['amount'] += damage_amount_done
            player_damage_dict[skill]['hit'] += 1
            player_damage_dict[skill]['total_damage'] += damage_amount_done
        return True

    def parse_heal(self, row):
        """Parse heal done."""
        heal_amount = row['amount'][1:].split(None, 1)[0][:-1]
        try:
            self.pull['heal'][self.player_id] += int(heal_amount)
        except ValueError:
            self.pull['heal'][self.player_id] += int(heal_amount[:-1])
        return True

    def parse_damage_received(self, row):
        """Parse damage received."""
        damage_dict = self.pull['damage_received']
        player_damage_dict = damage_dict[self.player_id]['attackers']
        attacker = row['from'][1:].split('{', 1)[0]
        skill = row['skill'][1:].split('{', 1)[0]
        raw_damage, dmg_type = row['amount'][1:].split(None, 2)[:2]
        player_damage_dict.setdefault(attacker, dict())
        player_damage_dict[attacker].setdefault(
            skill, {'hit': 0, 'dodged': 0, 'shielded': 0, 'total_damage': 0})
        skill_dict = player_damage_dict[attacker][skill]
        try:
            raw_damage = int(raw_damage)
        except ValueError:
            raw_damage = int(raw_damage[:-1])
        if raw_damage != 0:
            player_damage_dict[attacker][skill].setdefault(
                'dmg_type', dmg_type)
        for effect, handler in DMG_RCVD_DISPATCH_DICT.items():
            if effect in row['amount']:
                getattr(self, handler)(row, skill_dict)
                if handler == 'dodge_or_parry':
                    return True
        skill_dict['hit'] += 1
        skill_dict['total_damage'] += raw_damage
        self.pull['damage_received'][self.player_id]['amount'] += raw_damage
        return True

    def absorb(self, row, skill_dict):
        """Some damage got absorbed by a healer 'bubble'."""
        raw_damage, dmg_type = row['amount'][1:].split(None, 2)[:2]
        try:
            raw_damage = int(raw_damage)
        except ValueError:
            raw_damage = int(raw_damage[:-1])
        absorbed_damage = int(row['amount'][1:].partition('(')[2].split(
            ABSORB, 1)[0].split(None, 1)[0])
        if absorbed_damage > raw_damage:
            # If abs > raw, we're probably dealing with a pure shield absorb
            return True
        try:
            self.pull['heal'][self.healer_id] += int(absorbed_damage)
        except KeyError:
            self.pull['heal'][self.healer_id] = int(absorbed_damage)
        return True

    def dodge_or_parry(self, row, skill_dict):
        """Attack dodged or parried."""
        skill_dict['dodged'] += 1
        return True

    def shield(self, row, skill_dict):
        """Attack partially shielded."""
        skill_dict['shielded'] += 1
        return True

    def parse_affect_healer(self, row):
        """Affect current healer name to healer_id for later purposes."""
        self.healer_id = row['from'][2:]

    def parse_exit_combat(self, row):
        """Parse exit combat."""
        current_date = self.current_date
        self.pull['stop'] = self.actual_time(row['time'][1:], current_date)
        # Instantiates a client
        datastore_client = datastore.Client()
        kind = 'Pull'
        pull_key = datastore_client.key(kind)
        # Prepares the new entity
        pull = datastore.Entity(key=pull_key, exclude_from_indexes=("data",))
        pull["id"] = str(uuid.uuid4())
        pull["create_datetime"] = datetime.datetime.now()
        if self.pull["stop"] < self.pull["start"]:
            self.pull["stop"] = self.pull["stop"] + datetime.timedelta(days=1)
        pull["start_datetime"] = self.pull["start"]
        pull["stop_datetime"] = self.pull["stop"]
        pull["target"] = self.pull["target"]
        pull["player(s)"] = len(self.pull["players"])
        pull["total_damage"] = sum(player['amount'] for player in
                                   self.pull['damage_done'].values())
        pull["data"] = json.dumps(self.pull, default=str)
        # Saves the entity
        datastore_client.put(pull)
        logging.debug("Pull Dict: {}".format(self.pull))
        self.initialize_pull()

    def initialize_pull(self):
        """(Re)initialize pull."""
        self.in_combat = False
        self.player_id = None
        self.healer_id = None
        self.pull_start_time = None
        self.pull_end_time = None

    def parse(self, log_file):
        """Main parsing function."""
        self.player_id = 'None'
        self.initialize_pull()
        for row in log_file:
            row = {key: row_field for key, row_field in row.items()}
            self.dispatch_row(row)
        return True

    def dispatch_row(self, row):
        """
        Dispatch row to handlers based on conditions in ROW_DISPATCH_DICT.
        """
        for conditions, handler in ROW_DISPATCH_DICT.items():
            for condition, value in conditions:
                if condition == 'in_combat':
                    if not value == self.in_combat:
                        break
                elif value == 'player_id':
                    if not self.player_id in row[condition]:
                        break
                elif value == REVIVE:
                    if REVIVE in row[condition]:
                        break
                elif not value in row[condition]:
                    break
            else:
                getattr(self, handler)(row)
        return True


@app.route('/results')
def results():
        """GET method handler."""
        # Creating the data
        description = {"pull_start_time": ("datetime", "Pull Start Time"),
                       "total_damage": ("number", "Total Damage"),
                       "players_number": ("number", "Number of Player(s)"),
                       "pull_id": ("string", "Pull Id"),
                       "pull_duration": ("timeofday", "Pull Duration"),
                       "pull_target": ("string", "Pull Target"),
                       }
        data = list()
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='Pull')
        query.projection = ["id", "start_datetime", "stop_datetime", "target", "total_damage", "player(s)"]
        results = list(query.fetch())

        for result in results:
            data.append(
                {"pull_start_time": datetime.datetime.fromtimestamp(result['start_datetime']/1000000),
                    "total_damage": result["total_damage"],
                    "players_number": result["player(s)"],
                    "pull_id": "<a href=/chart/"+result["id"]+">Pull details<a/>",
                    "pull_duration": datetime.datetime.min + datetime.timedelta(microseconds=result["stop_datetime"] - result["start_datetime"]),
                    "pull_target": result['target'], }
            )

        #Loading it into gviz_api.DataTable
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)

        #Creating a JSon string
        json_pull = data_table.ToJSon(
            columns_order=("pull_start_time", "pull_target",
                           "pull_duration", "total_damage", "players_number", "pull_id"),
            order_by=("pull_start_time", "desc"))

        #Putting the JSon string into the template
        return table_page_template.format(json_pull=json_pull)


@app.route("/chart/<chart_id>")
def get_chart(chart_id):
        """GET method handler."""
        datastore_client = datastore.Client()
        query = datastore_client.query(kind='Pull')
        query.add_filter('id', '=', chart_id)
        results = list(query.fetch())
        result = results[0]
        pull = json.loads(result["data"])
        pull["stop"] = datetime.datetime.strptime(pull["stop"], '%Y-%m-%d %H:%M:%S.%f%z')
        pull["start"] = datetime.datetime.strptime(pull["start"], '%Y-%m-%d %H:%M:%S.%f%z')

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
                if skill != 'amount':
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
                if attacker != 'amount':
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
        bar_dtps_description = {"player": ("string", "Player"),
                                "dtps": ("number", "DTPS")}
        bar_dtps_data = list()

        for player, damage_dict in pull['damage_done'].items():
            chart_dmg_data.append(
                {"player": player, "damage": damage_dict['amount']})
            bar_dmg_data.append(
                {"player": player, "dps": damage_dict['amount'] / (
                    pull['stop'] - pull['start']).total_seconds()})

        for player, heal in pull['heal'].items():
            chart_heal_data.append(
                {"player": player, "heal": heal})
            bar_heal_data.append(
                {"player": player,
                 "hps": heal / (pull['stop'] - pull['start']).total_seconds()})

        for player, damage in pull['damage_received'].items():
            chart_dmg_received_data.append(
                {"player": player, "damage_received": damage['amount']})
            bar_dtps_data.append(
                {"player": player,
                 "dtps": damage["amount"] / (pull['stop'] - pull['start']).total_seconds()})

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
        bar_dtps_data_table = gviz_api.DataTable(bar_dtps_description)
        bar_dtps_data_table.LoadData(bar_dtps_data)

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
        json_bar_dtps = bar_dtps_data_table.ToJSon(
            columns_order=("player", "dtps"))
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
            dmg_table=json_dmg_data_table,
            bar_dtps=json_bar_dtps)
        return response

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=5000, debug=True)

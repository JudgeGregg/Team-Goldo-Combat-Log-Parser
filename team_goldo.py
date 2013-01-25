# -*- coding: utf8 -*-

import csv
import datetime
import webapp2
import logging
import string
import gviz_api
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


chart_page_template = """
<!DOCTYPE html>
<html><head>
  <title>Team Goldo Combat Log Parser Results Charts</title>
    <style>
        div{{ font-family: 'Droid Serif'}}
        .goldenrod {{color: goldenrod; text-align: center;}}
        .bold {{font-weight: bold}}
        .beige-background {{background-color: beige;}}
        .large-font {{font-family: 'Droid Serif'; font-size: 20px}}
        .medium-font {{font-family: 'Droid Serif'; font-size: 15px}}
    </style>
  <script src="https://www.google.com/jsapi" type="text/javascript"></script>
  <script>
        var cssClassNames = {{
        'headerRow': 'goldenrod bold large-font',
        'oddTableRow': 'beige-background',
        'tableCell': 'goldenrod bold medium-font google-greg',
        'rowNumberCell': 'goldenrod bold'}}
    google.load('visualization', '1', {{packages:['corechart', 'table']}});
    google.setOnLoadCallback(drawDmgPieChart);
    google.setOnLoadCallback(drawDmgBarChart);
    google.setOnLoadCallback(drawHealPieChart);
    google.setOnLoadCallback(drawHealBarChart);
    google.setOnLoadCallback(drawDmgReceivedPieChart);
    google.setOnLoadCallback(drawSkillTable);
    google.setOnLoadCallback(drawDmgTable);
    function drawDmgPieChart() {{
      var json_pie_dmg_chart = new google.visualization.PieChart
      (document.getElementById('piechart_dmg_div_json'));
      var json_pie_dmg_data = new google.visualization.DataTable
      ({pie_dmg}, 0.6);
      json_pie_dmg_chart.draw(json_pie_dmg_data);
    }}
    function drawDmgBarChart() {{
      var json_bar_dmg_chart= new google.visualization.BarChart
      (document.getElementById('barchart_dmg_div_json'));
      var json_bar_dmg_data = new google.visualization.DataTable
      ({bar_dmg}, 0.6);
      json_bar_dmg_chart.draw(json_bar_dmg_data);
    }}
    function drawHealPieChart() {{
      var json_pie_heal_chart = new google.visualization.PieChart
      (document.getElementById('piechart_heal_div_json'));
      var json_pie_heal_data = new google.visualization.DataTable
      ({pie_heal}, 0.6);
      json_pie_heal_chart.draw(json_pie_heal_data);
    }}
    function drawHealBarChart() {{
      var json_bar_heal_chart= new google.visualization.BarChart
      (document.getElementById('barchart_heal_div_json'));
      var json_bar_heal_data = new google.visualization.DataTable
      ({bar_heal}, 0.6);
      json_bar_heal_chart.draw(json_bar_heal_data);
    }}
     function drawDmgReceivedPieChart() {{
      var json_pie_dmg_received_chart = new google.visualization.PieChart
      (document.getElementById('piechart_dmg_received_div_json'));
      var json_pie_dmg_received_data = new google.visualization.DataTable
      ({pie_dmg_received}, 0.6);
      json_pie_dmg_received_chart.draw(json_pie_dmg_received_data);
    }}
    function drawSkillTable() {{
      var json_table = new google.visualization.Table
      (document.getElementById('skilltable_div_json'));
      var json_data = new google.visualization.DataTable
      ({skill_table}, 0.6);
      var json_view = new google.visualization.DataView(json_data);
      json_table.draw(json_view,{{'showRowNumber': true, 'allowHtml' : true,
      'cssClassNames': cssClassNames }});
    }}
    function drawDmgTable() {{
      var json_table = new
      google.visualization.Table(document.getElementById(
      'dmgtable_div_json'));
      var json_data = new google.visualization.DataTable
      ({dmg_table}, 0.6);
    }}
    function drawDmgTable() {{
      var json_table = new
      google.visualization.Table(document.getElementById(
      'dmgtable_div_json'));
      var json_data = new google.visualization.DataTable
      ({dmg_table}, 0.6);
      google.visualization.Table(document.getElementById(
      'dmgtable_div_json'));
      var json_data = new google.visualization.DataTable
      ({dmg_table}, 0.6);
      var json_view = new google.visualization.DataView(json_data);
      json_table.draw(json_view,{{'showRowNumber': true, 'allowHtml' : true,
      'cssClassNames': cssClassNames }});
    }}
    </script></head>
  <body>
    <div id = dmg_container>
    <div id = piechart_dmg_div_json></div>
    <div id = barchart_dmg_div_json></div>
    <div style="clear:both;"></div>
    </div>
    <div id = heal_container>
    <div id = piechart_heal_div_json></div>
    <div id = barchart_heal_div_json></div>
    <div style="clear:both;"></div>
    </div>
    <div id = "piechart_dmg_received_div_json"></div>
    <div id = "skilltable_div_json"></div>
    <div id = "dmgtable_div_json"></div>
  </body>
</html>
"""

table_page_template = """
<!DOCTYPE html>
<html><head>
  <link href='http://fonts.googleapis.com/css?family=Droid+Serif'
        rel='stylesheet' type='text/css'>
  <style> div{{ font-family: 'Droid Serif'}}
         .goldenrod {{color: goldenrod; text-align: center;}}
         .bold {{font-weight: bold}}
         .beige-background {{background-color: beige;}}
         .large-font {{font-family: 'Droid Serif'; font-size: 20px}}
         .medium-font {{font-family: 'Droid Serif'; font-size: 15px}}
  </style>
  <title>Team Goldo Combat Log Parser Results</title>
  <script src="https://www.google.com/jsapi" type="text/javascript"></script>
  <script>
    google.load('visualization', '1', {{packages:['table']}});
    google.setOnLoadCallback(drawTable);
    var cssClassNames = {{
    'headerRow': 'goldenrod bold large-font',
    'oddTableRow': 'beige-background',
    'tableCell': 'goldenrod bold medium-font',
    'rowNumberCell': 'goldenrod bold'}}
    function drawTable() {{
      var json_table = new
      google.visualization.Table(document.getElementById('table_div_json'));
      var json_data = new google.visualization.DataTable
      ({json_pull}, 0.6);
      var json_view = new google.visualization.DataView(json_data);
      json_table.draw(json_view,{{'showRowNumber': true, 'allowHtml' : true,
      'cssClassNames': cssClassNames }});
      google.visualization.events.addListener
      (json_table, 'select', function() {{
      var selection = json_table.getSelection();
      json_table.setSelection(null);
      var selected_row = selection[0].row;
      var selected_pull_number = json_view.getValue(selected_row, 0);
      document.location.href = '/chart/' + selected_pull_number; }});
    }}
  </script></head>
  <body>
    <div id="table_div_json"></div>
  </body>
</html>
"""


class MainPage(webapp2.RequestHandler):
    def get(self):
        upload = blobstore.create_upload_url('/upload')
        self.response.out.write("""
        <!DOCTYPE html>
        <html><head>
        <link href='http://fonts.googleapis.com/css?family=Droid+Serif'
        rel='stylesheet' type='text/css'>
        <title>Team Goldo Combat Log Parser</title>
        <style>
            h1 {{ font-family: 'Droid Serif'; }}
            div {{ font-size: 15px;
                color: goldenrod;
                text-align: center; }}
            #jawa {{ position: relative;
                    display: none; }}
        </style></head>
        <body>
            <div id='jawa'>
            <p><h1>Please wait while the Jawas gather your data<h1>
            <img src='/img/jawa.gif' alt='Running Jawas' /></p>
            </div>
            <div id='upload'>
            <p><img src='/img/swtor_logo.png' alt='SWTOR Logo' /></p>
            <h1>Upload your combat log</h1>
            <form name="upload" action="{}" method="post"
                enctype="multipart/form-data">
            <input type="file" name="file" /><br /><br />
            <input type='button' onClick='submitform()' value="Submit">
                <script type="text/javascript">
                function submitform()
                {{
                   document.getElementById('upload').style.display = 'none';
                   document.getElementById('jawa').style.display = 'block';
                   document.upload.submit();
                 }}
                </script>

            </form>
            </div>
        </body></html>
        """.format(upload))


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
        myFile = upload_files[0]
        uploaded_file = myFile.open()
        current_date = myFile.filename.split('_', 2)[1]
        log_file = csv.reader(
            uploaded_file, delimiter=']', skipinitialspace=True)
        self.parser(current_date, log_file)
        uploaded_file.close()
        self.redirect('/results')

    def synchronize_raid(self):
        for current_pull in Raid.raid:
            for pull in Raid.raid:
                if pull['start'] < current_pull['start'] < pull['stop']:
                    logging.debug("Synchronizing Raid: \
                            {}".format(Raid.raid))
                    logging.debug("Synchronizing pulls: \
                            {}{}".format(current_pull, pull))
                    for player in current_pull['damage_done']:
                        if player in pull['damage_done']:
                            pull['damage_done'][player]['amount'] += \
                                current_pull['damage_done'][player]['amount']
                        else:
                            pull['damage_done'][player]['amount'] = \
                                current_pull['damage_done'][player]['amount']
                    for player in current_pull['damage_received']:
                        if player in pull['damage_received']:
                            pull['damage_received'][player] += \
                                current_pull['damage_received'][player]
                        else:
                            pull['damage_received'][player] = \
                                current_pull['damage_received'][player]
                    for player in current_pull['heal']:
                        if player in pull['heal']:
                            pull['heal'][player] += \
                                current_pull['heal'][player]
                        else:
                            pull['heal'][player] = \
                                current_pull['heal'][player]
                    pull['players'].update(current_pull['players'])
                    if current_pull['stop'] > pull['stop']:
                        pull['stop'] = current_pull['stop']
                    logging.debug("Synchronized Raid: \
                            {}".format(Raid.raid))
                    Raid.raid.remove(current_pull)

    def parse_enter_combat(self, row, current_date):
        self.in_combat = True
        self.player_id = row[1][2:]
        self.pull_start_time = self.actual_time(
            row[0][1:], current_date)
        for pull in reversed(Raid.raid):
            if (pull['start'] < self.pull_start_time < pull['stop'] or
                0 < (self.pull_start_time - pull['stop']).total_seconds() < 5
                or -5 <
                (self.pull_start_time - pull['start']).total_seconds()
                    < 0):
                if self.player_id not in pull['players']:
                    pull['players'].add(self.player_id)
                    pull['damage_done'][self.player_id] = {'amount': 0}
                    pull['damage_received'][self.player_id] = {
                        'attackers': dict(),
                        'amount': 0}
                    if self.player_id not in pull['heal']:
                        pull['heal'][self.player_id] = 0
                logging.debug("Retrieving previous pull: \
                        {0}{1}".format(self.pull_start_time, pull['stop']))
                return pull
        pull = dict([('start', self.pull_start_time),
                    ('damage_done', {self.player_id: {'amount': 0}}),
                    ('damage_received', {self.player_id: {
                        'attackers': dict(),
                        'amount': 0}, }),
                    ('heal', {self.player_id: 0}),
                    ('target', None),
                    ('players', set([self.player_id])), ])
        logging.debug("Entering New Combat: {0} - \
            {1}".format(row[0][1:], row[2][2:].encode('ascii', 'replace')))
        self.new_pull = True
        return pull

    def parse_damage_done(self, row, pull):
        if '{836045448945506}' in row[5]:
            return pull
        player_damage_dict = pull['damage_done'][self.player_id]
        pull['target'] = row[2][1:].split('{', 1)[0]
        skill = row[3][1:].split('{', 1)[0]
        damage_amount_done = row[5][1:].split(None, 1)[0]
        player_damage_dict.setdefault(
            skill, {'hit': 0, 'dodged': 0, 'missed': 0, 'total_damage': 0})
        if not damage_amount_done.isdigit():
            damage_amount_done = damage_amount_done[:-1]
        if int(damage_amount_done) is 0:
            if '{836045448945505}' in row[5]:
                player_damage_dict[skill]['dodged'] += 1
            else:
                player_damage_dict[skill]['missed'] += 1
        else:
            player_damage_dict['amount'] += int(damage_amount_done)
            player_damage_dict[skill]['hit'] += 1
            player_damage_dict[skill]['total_damage'] \
                += int(damage_amount_done)
        return pull

    def parse_heal(self, row, pull):
        heal_amount = row[5][1:].split(None, 1)[0][:-1]
        if heal_amount.isdigit():
            pull['heal'][self.player_id] += int(heal_amount)
        else:
            pull['heal'][self.player_id] += int(heal_amount[:-1])
        return pull

    def parse_damage_received(self, row, pull):
        player_damage_dict = \
            pull['damage_received'][self.player_id]['attackers']
        attacker = row[1][1:].split('{', 1)[0]
        skill = row[3][1:].split('{', 1)[0]
        raw_damage, dmg_type = row[5][1:].split(None, 2)[:2]
        player_damage_dict.setdefault(attacker, dict())
        player_damage_dict[attacker].setdefault(
            skill, {'hit': 0, 'dodged': 0, 'shielded': 0, 'total_damage': 0})
        if raw_damage != '0':
            player_damage_dict[attacker][skill].setdefault(
                'dmg_type', dmg_type)
        if not raw_damage.isdigit():
            raw_damage = raw_damage[:-1]
        if '{836045448945511}' in row[5]:
            absorbed_damage = \
                row[5][1:].partition('(')[2].split(
                    '{836045448945511}', 1)[0].split(None, 1)[0]
            if self.healer_id in pull['heal']:
                pull['heal'][self.healer_id] += int(absorbed_damage)
            else:
                pull['heal'][self.healer_id] = int(absorbed_damage)
                row[5][1:].partition('(')[2].split(
                    '{836045448945511}', 1)[0].split(None, 1)[0]
            if self.healer_id in pull['heal']:
                pull['heal'][self.healer_id] += int(absorbed_damage)
            else:
                pull['heal'][self.healer_id] = int(absorbed_damage)
            if self.healer_id in pull['heal']:
                pull['heal'][self.healer_id] += int(absorbed_damage)
            else:
                pull['heal'][self.healer_id] = int(absorbed_damage)
        if ('{836045448945505}' or '{836045448945508}') in row[5]:
            player_damage_dict[attacker][skill]['dodged'] += 1
        elif '{836045448945509}' in row[5]:
            player_damage_dict[attacker][skill]['shielded'] += 1
        else:
            player_damage_dict[attacker][skill]['hit'] += 1
        player_damage_dict[attacker][skill]['total_damage'] \
            += int(raw_damage)
        pull['damage_received'][self.player_id]['amount'] \
            += int(raw_damage)
        return pull

    def parse_exit_combat(self, row, pull, current_date):
        if self.new_pull:
            pull['stop'] = self.pull_end_time
            Raid.raid.append(pull)
            logging.debug("Pull Dict: {}".format(pull))
        if not self.new_pull and self.pull_end_time > pull['stop']:
            pull['stop'] = self.pull_end_time
            logging.debug("Pull Time Extended: {}".format(self.pull_end_time))

    def initialize_pull(self):
        self.new_pull = False
        self.in_combat = False
        self.player_id = None
        self.healer_id = None
        self.pull_start_time = None
        self.pull_end_time = None

    def parser(self, current_date, log_file):
        self.player_id = 'None'
        self.initialize_pull()
        for row in log_file:
            row = [unicode(row_field, 'iso-8859-1') for row_field in row]
            if not self.in_combat and '{836045448945489}' in row[4]:
                logging.debug("Entering Combat:{0} - \
                    {1}".format(row[0][1:], row[2][2:].encode(
                    'ascii', 'replace')))
                pull = self.parse_enter_combat(row, current_date)
                continue
            elif '{812736661422080}' in row[4] and '@' in row[2]:
                self.healer_id = row[1][2:]
                continue
            elif self.in_combat and '{836045448945501}' \
                    in row[4] and self.player_id in row[1]:
                pull = self.parse_damage_done(row, pull)
                continue
            elif self.in_combat and '{836045448945500}' \
                in row[4] and self.player_id in row[1] and not \
                    '{810619242545152}' in row[3]:
                pull = self.parse_heal(row, pull)
                continue
            elif self.in_combat and '{836045448945501}' in row[4] and \
                    self.player_id in row[2]:
                pull = self.parse_damage_received(row, pull)
                continue
            elif self.in_combat and self.player_id in row[2] and \
                    '{836045448945493}' in row[4] or '{836045448945490}' \
                        in row[4]:
                self.pull_end_time = self.actual_time(
                    row[0][1:], current_date)
                logging.debug("Death:{0} - \
                    {1}".format(row[0][1:], row[2][2:].encode(
                    'ascii', 'replace')))
                self.parse_exit_combat(row, pull, current_date)
                self.initialize_pull()
                continue
        self.synchronize_raid()
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

        pie_dmg_received_data_table = \
            gviz_api.DataTable(chart_dmg_received_description)
        pie_dmg_received_data_table.LoadData(chart_dmg_received_data)

        # Creating a JSon string
        json_pie_dmg_chart = \
            pie_dmg_data_table.ToJSon(columns_order=("player", "damage"))
        json_bar_dmg_chart = \
            bar_dmg_data_table.ToJSon(columns_order=("player", "dps"))
        json_pie_heal_chart = \
            pie_heal_data_table.ToJSon(columns_order=("player", "heal"))
        json_bar_heal_chart = \
            bar_heal_data_table.ToJSon(columns_order=("player", "hps"))
        json_pie_dmg_received_chart = \
            pie_dmg_received_data_table.ToJSon(columns_order=(
                "player", "damage_received"))
        json_skill_data_table = \
            skill_data_table.ToJSon(columns_order=(
                "player", "skill", "hit", "dodged", "missed", "total_damage"),
                order_by=("player", "skill"))
        json_dmg_data_table = \
            dmg_data_table.ToJSon(columns_order=(
                "player", "attacker", "skill", "hit",
                "dodged", "shielded", 'total_damage', 'dmg_type'),
                order_by=("player", "attacker", "skill"))

        # Putting the JSon string into the template
        response = chart_page_template.format(pie_dmg=json_pie_dmg_chart,
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

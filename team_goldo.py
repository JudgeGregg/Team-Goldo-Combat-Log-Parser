#!/usr/bin/python
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
    </style>
  <script src="https://www.google.com/jsapi" type="text/javascript"></script>
  <script>
    google.load('visualization', '1', {{ packages:['corechart'] }});

    google.setOnLoadCallback(drawDmgPieChart);
    google.setOnLoadCallback(drawDmgBarChart);
    google.setOnLoadCallback(drawHealPieChart);
    google.setOnLoadCallback(drawHealBarChart);
    google.setOnLoadCallback(drawDmgReceivedPieChart);
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
    }} </script></head>
  <body>
    <div id = dmg_container>
    <div id = piechart_dmg_div_json></div>
    <div id = barchart_dmg_div_json></div>
    <div style="clear:both;"></div>
    </div>
    <div id = heal_container>
    <div id = piechart_heal_div_json></div>
    <div id = barchart_heal_div_json></div>
    </div>
    <div id = "piechart_dmg_received_div_json"></div>
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
    'tableCell': 'goldenrod bold medium-font google-greg',
    'rowNumberCell': 'goldenrod bold'}}
    function drawTable() {{
      var json_table = new
      google.visualization.Table(document.getElementById('table_div_json'));
      var json_data = new google.visualization.DataTable
      ({json_pull_dict}, 0.6);
      var json_view = new google.visualization.DataView(json_data);
      json_view.hideRows(json_view.getFilteredRows([{{column: 2, maxValue:
      [0,3,0]}}]));
      json_table.draw(json_view,{{ 'showRowNumber': true, 'allowHtml' : true,
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


class Upload(blobstore_handlers.BlobstoreUploadHandler):

    raid = []
    pull_time_list = []
    pull_end_time_list = []

    def actual_time(self, time, date):
            """Returns the actual time"""
            actual_time = datetime.datetime.strptime(string.join((date,
                time)), '%Y-%m-%d %H:%M:%S.%f')
            return actual_time

    def post(self):
        upload_files = self.get_uploads('file')
        myFile = upload_files[0]
        f = myFile.open()
        self.current_date = myFile.filename.split('_', 2)[1]
        log_file = csv.reader(f,\
                delimiter=']', skipinitialspace=True)
        self.parser(self.current_date, log_file)

    def parseEnterCombat(self, row, in_combat, current_date, player_id,
            new_pull):
        in_combat = True
        player_id = row[1][2:]
        pull_start_time = self.actual_time(row[0][1:],
                current_date)
        for pull_time in self.pull_time_list:
            if (abs((pull_start_time - pull_time).total_seconds())
                    < 2):
                pull_start_time = pull_time
                pull_dict = \
                    self.raid[self.pull_time_list.index(pull_time)]
                pull_dict['damage_done'][player_id] = 0
                pull_dict['damage_received'][player_id] = 0
                return pull_dict, in_combat, new_pull, player_id, \
                    pull_start_time
        self.pull_time_list.append(pull_start_time)
        pull_dict = dict([('damage_done', {player_id: 0}),
            ('heal', {player_id: 0}),
            ('damage_received', {player_id: 0})])
        new_pull = True
        return pull_dict, in_combat, new_pull, player_id, pull_start_time

    def parseDamageDone(self, row, pull_dict, player_id):
        damage_amount_done = row[5][1:].split(None, 1)[0]
        if damage_amount_done.isdigit():
            pull_dict['damage_done'][player_id]\
                += int(damage_amount_done)
        else:
            pull_dict['damage_done'][player_id] \
                += int(damage_amount_done[:-1])
        return pull_dict

    def parseHeal(self, row, pull_dict, player_id):
        heal_amount = row[5][1:].split(None, 1)[0][:-1]
        if heal_amount.isdigit():
            try:
                pull_dict['heal'][player_id] += \
                    int(heal_amount)
            except KeyError:
                pull_dict['heal'][player_id] = \
                    int(heal_amount)
        else:
            try:
                pull_dict['heal'][player_id] += \
                        int(heal_amount[:-1])
            except KeyError:
                pull_dict['heal'][player_id] = \
                        int(heal_amount[:-1])
        return pull_dict

    def parseDamageReceived(self, row, pull_dict, player_id, healer_id):
        raw_damage = row[5][1:].split(None, 1)[0]
        if '{836045448945511}' in row[5]:
            absorbed_damage = \
                row[5][1:].partition('(')[2].split('{836045448945511}',
                    1)[0].split(None, 1)[0][:-1]
            damage_received_amount = int(raw_damage) - int(absorbed_damage)
            try:
                pull_dict['heal'][healer_id] += int(absorbed_damage)
            except KeyError:
                pull_dict['heal'][healer_id] = int(absorbed_damage)
        else:
            damage_received_amount = raw_damage
            pull_dict['damage_received'][player_id] \
                += int(damage_received_amount)
        return pull_dict

    def parseExitCombat(self, row, pull_dict, new_pull, current_date,
            pull_start_time, pull_end_time):
        if '{836045448945490}' in row[4]:
            pull_end_time = self.actual_time(row[0][1:], current_date)
        if new_pull:
            self.raid.append(pull_dict)
            self.pull_end_time_list.append(pull_end_time)
        if not new_pull and pull_end_time > \
            self.pull_end_time_list[ \
                self.pull_time_list.index(pull_start_time)]:
            self.pull_end_time_list[ \
                self.pull_time_list.index(pull_start_time)] = pull_end_time

    def parser(self, current_date, log_file):
        new_pull = False
        in_combat = False
        death = 0
        b_rez = False
        player_id = None
        healer_id = None
        pull_start_time = None
        pull_end_time = None
        for row in log_file:
            #try:
                row[1] = unicode(row[1], 'iso-8859-1')
                row[2] = unicode(row[2], 'iso-8859-1')
                if not in_combat and '{836045448945489}' in row[4]:
                    pull_dict, in_combat, new_pull, player_id, \
                        pull_start_time = self.parseEnterCombat(row, in_combat,
                        current_date, player_id, new_pull)
                    continue
                elif '{812736661422080}' in row[4] and '@' \
                    in row[2]:
                    healer_id = row[1][2:]
                    continue
                elif in_combat and \
                        '{836045448945501}' in row[4] and player_id in row[1]:
                    pull_dict = self.parseDamageDone(row, pull_dict, player_id)
                    continue
                elif in_combat and \
                    '{836045448945500}' in row[4] and player_id in row[1]:
                    pull_dict = self.parseHeal(row, pull_dict, player_id)
                    continue
                elif in_combat and '{836045448945501}' in row[4] and \
                    player_id in row[2]:
                    pull_dict = self.parseDamageReceived(row, pull_dict,
                    player_id, healer_id)
                    continue
                elif in_combat and player_id in row[2] and \
                        '{836045448945493}' in row[4]:
                    death += 1
                    pull_end_time = self.actual_time(row[0][1:], current_date)
                    continue
                elif ('{812826855735296}' in row[4] or '{807217628446720}' \
                        in row[4]) and player_id in row[2]:
                    b_rez = True
                    pull_end_time = self.actual_time(row[0][1:], current_date)
                    continue
                elif in_combat and player_id in row[1] \
                    and ('{973870949466372}' in row[4] or '{836045448945490}' \
                    in row[4] or (death is 2 or (death is 1 and not b_rez) \
                    and '{810619242545152}' in row[3])):
                    self.parseExitCombat(row, pull_dict, new_pull,
                        current_date, pull_start_time, pull_end_time)
                    new_pull = False
                    in_combat = False
                    death = 0
                    b_rez = False
                    player_id = None
                    healer_id = None
                    pull_start_time = None
                    pull_end_time = None
            #except:
            #    logging.info('except ROW: {}'.format(row))
        self.redirect('/results')


class Result(webapp2.RequestHandler):

    def get_players_number(self, pull_dict):
        players_number = len(pull_dict['damage_done'])
        for player in pull_dict['heal']:
            if player not in pull_dict['damage_done']:
                players_number += 1
        return players_number

    def get(self):
        # Creating the data
        description = {"pull_start_time": ("datetime", "Pull Start Time"),
                       "total_damage": ("number", "Total Damage"),
                       "players_number": ("number", "Number of Player(s)"),
                       "pull_id": ("number", "Pull Id"),
                       "pull_duration": ("timeofday", "Pull Duration")}
        data = []
        for pull in Upload.raid:
            try:
                    data.append({"pull_start_time":
                        Upload.pull_time_list[Upload.raid.index(pull)],
                        "total_damage":
                        sum(pull['damage_done'].values()), "players_number":
                        self.get_players_number(pull),
                        "pull_id": Upload.raid.index(pull),
                        "pull_duration":
                        (datetime.datetime.min +
                        (Upload.pull_end_time_list[Upload.raid.index(pull)] -
                        Upload.pull_time_list[Upload.raid.index(pull)]))})
            except:
                    logging.info('EXCEPT PULL:{}'.format(
                    Upload.pull_time_list[Upload.raid.index(pull)]))
        #Loading it into gviz_api.DataTable
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)

        #Creating a JSon string
        json_pull_dict = data_table.ToJSon(columns_order=("pull_id",
            "pull_start_time", "pull_duration", "total_damage",
            "players_number"),
            order_by=("pull_start_time", "asc"))

        #Putting the JSon string into the template
        self.response.out.write(table_page_template.format
                                    (json_pull_dict=json_pull_dict))


class Chart(webapp2.RequestHandler):
    def get(self, chart_id):
        pull_dict = Upload.raid[int(chart_id)]
        pull_start_time_list = Upload.pull_time_list
        pull_end_time_list = Upload.pull_end_time_list

        # Creating the data
        chart_dmg_description = {"player": ("string", "Player"),
                       "damage": ("number", "Damage")}
        chart_dmg_data = []
        bar_dmg_description = {"player": ("string", "Player"),
                        "dps": ("number", "DPS")}
        bar_dmg_data = []
        chart_heal_description = {"player": ("string", "Player"),
                       "heal": ("number", "heal")}
        chart_heal_data = []
        bar_heal_description = {"player": ("string", "Player"),
                        "hps": ("number", "HPS")}
        bar_heal_data = []
        chart_dmg_received_description = {"player": ("string", "Player"),
                        "damage_received": ("number", "Damage Received")}
        chart_dmg_received_data = []

        for player, damage in pull_dict['damage_done'].iteritems():
            chart_dmg_data.append({"player":
                player, "damage": damage})
            bar_dmg_data.append({"player": player,
                "dps": damage / (pull_end_time_list[int(chart_id)] -
                    pull_start_time_list[int(chart_id)]).total_seconds()})

        for player, heal in pull_dict['heal'].iteritems():
            chart_heal_data.append({"player":
                player, "heal": heal})
            bar_heal_data.append({"player": player,
                "hps": heal / (pull_end_time_list[int(chart_id)] -
                    pull_start_time_list[int(chart_id)]).total_seconds()})

        for player, damage in pull_dict['damage_received'].iteritems():
            chart_dmg_received_data.append({"player":
                player, "damage_received": damage})

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
                pie_dmg_received_data_table.ToJSon(columns_order=("player",
                    "damage_received"))

        # Putting the JSon string into the template
        self.response.out.write(chart_page_template.format
                                (pie_dmg=json_pie_dmg_chart,
                                 bar_dmg=json_bar_dmg_chart,
                                 pie_heal=json_pie_heal_chart,
                                 bar_heal=json_bar_heal_chart,
                                 pie_dmg_received=json_pie_dmg_received_chart))


app = webapp2.WSGIApplication(
                              [('/', MainPage), ('/upload',
                              Upload), ('/chart/(\d+)', Chart), ('/results',
                              Result)],
                              debug=True)

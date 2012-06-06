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


class Raid:
    raid = []


class Upload(blobstore_handlers.BlobstoreUploadHandler):
    def actual_time(self, time, date):
            """Returns the actual time"""
            actual_time = datetime.datetime.strptime(string.join((date,
                time)), '%Y-%m-%d %H:%M:%S.%f')
            return actual_time

    def post(self):
        upload_files = self.get_uploads('file')
        myFile = upload_files[0]
        f = myFile.open()
        current_date = myFile.filename.split('_', 2)[1]
        log_file = csv.reader(f,\
                delimiter=']', skipinitialspace=True)
        self.parser(current_date, log_file)

    def parseEnterCombat(self, row, current_date):
        self.in_combat = True
        self.player_id = row[1][2:]
        self.pull_start_time = self.actual_time(row[0][1:],
                current_date)
        for pull in reversed(Raid.raid):
            if  0 < (self.pull_start_time
                    - pull['stop']).total_seconds() < 30:
                if self.player_id not in pull['players']:
                    pull['players'].append(self.player_id)
                logging.debug("Retrieving previous pull: \
                        {0}{1}".format(self.pull_start_time, pull['stop']))
                return pull
        for pull in Raid.raid:
            if (abs((self.pull_start_time - pull['start']).total_seconds())
                    < 2):
                self.pull_start_time = pull['start']
                pull['damage_done'][self.player_id] = 0
                pull['damage_received'][self.player_id] = 2
                if self.player_id not in pull['players']:
                    pull['players'].append(self.player_id)
                logging.info("Entering Previous Combat:{0} - \
                    {1}".format(row[0][1:], row[2][2:].encode('ascii',
                                'replace')))
                return pull
        pull_dict = dict([('start', self.pull_start_time),
            ('damage_done', {self.player_id: 0}),
            ('damage_received', {self.player_id: 0}),
            ('heal', {self.player_id: 0}),
            ('target', None),
            ('players', [self.player_id])
            ])
        logging.info("Entering New Combat:{0} - \
            {1}".format(row[0][1:], row[2][2:].encode('ascii',
                                'replace')))
        self.new_pull = True
        return pull_dict

    def parseDamageDone(self, row, pull_dict):
        pull_dict['target'] = row[2][1:].split('{', 1)[0]
        damage_amount_done = row[5][1:].split(None, 1)[0]
        if damage_amount_done.isdigit():
            pull_dict['damage_done'][self.player_id] \
                += int(damage_amount_done)
        else:
            pull_dict['damage_done'][self.player_id] \
                += int(damage_amount_done[:-1])
        return pull_dict

    def parseHeal(self, row, pull_dict):
        heal_amount = row[5][1:].split(None, 1)[0][:-1]
        if heal_amount.isdigit():
            pull_dict['heal'][self.player_id] \
                += int(heal_amount)
        else:
            pull_dict['heal'][self.player_id] \
                += int(heal_amount[:-1])
        return pull_dict

    def parseDamageReceived(self, row, pull_dict):
        raw_damage = row[5][1:].split(None, 1)[0]
        if not raw_damage.isdigit():
            raw_damage = raw_damage[:-1]
        if '{836045448945511}' in row[5]:
            absorbed_damage = \
                row[5][1:].partition('(')[2].split('{836045448945511}',
                    1)[0].split(None, 1)[0]
            pull_dict['heal'][self.healer_id] += int(absorbed_damage)
        pull_dict['damage_received'][self.player_id] \
                += int(raw_damage)
        return pull_dict

    def parseExitCombat(self, row, pull_dict, current_date):
        if '{836045448945490}' in row[4]:
            logging.info("ExitCombatLine:{0} - \
                {1}".format(row[0][1:], row[2][2:].encode('ascii',
                                'replace')))
            self.pull_end_time = self.actual_time(row[0][1:], current_date)
        if self.new_pull:
            pull_dict['stop'] = self.pull_end_time
            Raid.raid.append(pull_dict)
            logging.info("Pull Dict: {}".format(pull_dict))
        if not self.new_pull and self.pull_end_time > pull_dict['stop']:
            pull_dict['stop'] = self.pull_end_time
            logging.info("Pull Time Extended: {}".format(self.pull_end_time))

    def initialize_pull(self):
        self.new_pull = False
        self.in_combat = False
        self.death = False
        self.b_rez = False
        self.player_id = None
        self.healer_id = None
        self.pull_start_time = None
        self.pull_end_time = None

    def parser(self, current_date, log_file):
        self.player_id = 'None'
        self.initialize_pull()
        for row in log_file:
                row[:2] = unicode(row[:2], 'iso-8859-1')
                if not self.in_combat and '{836045448945489}' in row[4]:
                    logging.info("Entering Combat:{0} - \
                            {1}".format(row[0][1:], row[2][2:].encode('ascii',
                                'replace')))
                    pull_dict = self.parseEnterCombat(row, current_date)
                    continue
                elif '{812736661422080}' in row[4] and '@' \
                    in row[2]:
                    self.healer_id = row[1][2:]
                    pull_dict['heal'][self.healer_id] = 0
                    continue
                elif self.in_combat and '{836045448945501}' \
                        in row[4] and self.player_id in row[1]:
                    pull_dict = self.parseDamageDone(row, pull_dict)
                    continue
                elif self.in_combat and '{836045448945500}'\
                     in row[4] and self.player_id in row[1] and not \
                     '{810619242545152}' in row[3]:
                    pull_dict = self.parseHeal(row, pull_dict)
                    continue
                elif self.in_combat and '{836045448945501}' in row[4] and \
                    self.player_id in row[2]:
                    pull_dict = self.parseDamageReceived(row, pull_dict)
                    continue
                elif self.in_combat and self.player_id in row[2] and \
                        '{836045448945493}' in row[4]:
                    self.death = True
                    self.pull_end_time = self.actual_time(row[0][1:],
                            current_date)
                    logging.info("Death:{0} - \
                            {1}".format(row[0][1:], row[2][2:].encode('ascii',
                                'replace')))
                    continue
                elif self.in_combat and ('{812826855735296}' or \
                        '{807217628446720}') in row[3] and self.player_id \
                        in row[2] and self.death:
                    self.b_rez = True
                    logging.info("Battle rez:{0} -".format(row))
                    self.pull_end_time = self.actual_time(
                           row[0][1:], current_date)
                    continue
                elif self.in_combat and self.player_id in row[1] \
                    and ('{973870949466372}' in row[4] or '{836045448945490}'
                    in row[4] or (self.death and not self.b_rez and \
                            '{810619242545152}' in row[3])):
                    logging.info("ExitCombat: {0} - \
                            death: {1}, b_rez: {2}".format(row, self.death,
                                self.b_rez))
                    self.parseExitCombat(row, pull_dict, current_date)
                    self.initialize_pull()
        self.redirect('/results')


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
        data = []
        for pull in Raid.raid:
#            try:
                if pull['stop'] - pull['start'] < datetime.timedelta(0):
                    pull['stop'] = pull['stop'] + datetime.timedelta(days=1)
                data.append({"pull_start_time": pull['start'],
                        "total_damage": sum(pull['damage_done'].values()),
                        "players_number": len(pull['players']),
                        "pull_id": Raid.raid.index(pull),
                        "pull_duration":
                        datetime.datetime.min + (pull['stop'] - pull['start']),
                        "pull_target": pull['target'],
                        })
#            except:
#                    logging.info('EXCEPT PULL:{}'.format(pull))
#                    logging.info('RAID :{}'.format(Raid.raid))

        #Loading it into gviz_api.DataTable
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)

        #Creating a JSon string
        json_pull_dict = data_table.ToJSon(columns_order=("pull_id",
            "pull_start_time", "pull_target", "pull_duration", "total_damage",
            "players_number"),
            order_by=("pull_start_time", "asc"))

        #Putting the JSon string into the template
        self.response.out.write(table_page_template.format
                                    (json_pull_dict=json_pull_dict))


class Chart(webapp2.RequestHandler):
    def get(self, chart_id):
        pull_dict = Raid.raid[int(chart_id)]

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
                "dps": damage / (pull_dict['stop'] -
                    pull_dict['start']).total_seconds()})

        for player, heal in pull_dict['heal'].iteritems():
            chart_heal_data.append({"player":
                player, "heal": heal})
            bar_heal_data.append({"player": player,
                "hps": heal / (pull_dict['stop'] -
                    pull_dict['start']).total_seconds()})

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

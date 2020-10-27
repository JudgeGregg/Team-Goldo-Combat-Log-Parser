"""Module containing templates for the team_goldo_app."""

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

main_page_template = """
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
        <h1>Upload Combat Log</h1>
        <form name="upload" action="upload" method="post"
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
    </body>
</html>
"""

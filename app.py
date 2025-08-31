from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
file_path = "ipl_point_table.xlsx"

# Load IPL Table
def load_table():
    df = pd.read_excel(file_path)
    df.index += 1
    return df

# Update Points Table
def update_points(team1, runs1, team2, runs2):
    df = load_table()

    if team1 not in df["Team"].values or team2 not in df["Team"].values:
        return "Invalid team names!"

    index1 = df[df["Team"] == team1].index[0]
    index2 = df[df["Team"] == team2].index[0]

    df.at[index1, "Matches Played"] += 1
    df.at[index2, "Matches Played"] += 1

    overs = 20
    nrr1 = (runs1 / overs) - (runs2 / overs)
    nrr2 = (runs2 / overs) - (runs1 / overs)

    if runs1 > runs2:
        df.at[index1, "Wins"] += 1
        df.at[index1, "Points"] += 2
        df.at[index1, "NRR"] += nrr1
        df.at[index2, "Losses"] += 1
        df.at[index2, "NRR"] += nrr2
    elif runs2 > runs1:
        df.at[index2, "Wins"] += 1
        df.at[index2, "Points"] += 2
        df.at[index2, "NRR"] += nrr2
        df.at[index1, "Losses"] += 1
        df.at[index1, "NRR"] += nrr1
    else:
        df.at[index1, "Points"] += 1
        df.at[index2, "Points"] += 1
        df.at[index1, "TIED"] += 1
        df.at[index2, "TIED"] += 1

    df = df.sort_values(by=["Points", "NRR"], ascending=[False, False])
    df.to_excel(file_path, index=False)
    return "Updated Successfully!"

@app.route('/')
def index():
    df = load_table()
    df_html = df.copy()
    df_html['Team'] = df_html['Team'].apply(lambda team: f'<a href="/team/{team}" style="color:black;">{team}</a>')
    return render_template('index.html', table=df_html.to_html(classes='table table-bordered', escape=False))

@app.route('/update', methods=['POST'])
def update():
    team1 = request.form['team1'].upper()
    runs1 = int(request.form['runs1'])
    team2 = request.form['team2'].upper()
    runs2 = int(request.form['runs2'])
    update_points(team1, runs1, team2, runs2)
    return redirect(url_for('index'))

@app.route('/team/<team_name>')
def team_chart(team_name):
    df = load_table()
    team_data = df[df['Team'] == team_name]

    if team_data.empty:
        return f"No data available for team: {team_name}"

    team_row = team_data.iloc[0]
    matches = team_row["Matches Played"]
    if matches == 0:
        return render_template("piechart.html", team=team_name, no_data=True)

    # Filter out zero values for clean labels
    values = []
    labels = []
    if team_row["Wins"] > 0:
        values.append(team_row["Wins"])
        labels.append("Wins")
    if team_row["Losses"] > 0:
        values.append(team_row["Losses"])
        labels.append("Losses")
    if team_row["TIED"] > 0:
        values.append(team_row["TIED"])
        labels.append("Tied")

    # Create pie chart
    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"{team_name} Match Outcome Distribution")
    image_path = f"static/{team_name}_pie.png"
    plt.savefig(image_path)
    plt.close()

    return render_template("piechart.html", team=team_name, image_url=image_path, no_data=False)

if __name__ == '__main__':
    app.run(debug=True)

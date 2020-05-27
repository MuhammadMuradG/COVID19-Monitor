# -*- coding: utf-8 -*-
"""
Created on Fri May  1 04:32:29 2020

@author: Mourad & Sayed
"""

import math
import json
import pandas as pd
import pygal
import pylab
from scipy import stats
import requests
from flask import Flask, render_template, request
from pygal.maps import world
from pygal.style import DarkStyle


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    # Statistics
    PAYLOAD = {"code": "ALL"}
    URL = "https://api.statworx.com/covid"
    RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))

    # Convert to data frame
    DFRAME = pd.DataFrame.from_dict(json.loads(RESPONSE.text))

    # Find the summation
    cases = (
        DFRAME.filter(items=["country", "cases"])
        .groupby("country", as_index=False)
        .sum()
    )

    deaths = (
        DFRAME.filter(items=["country", "deaths"])
        .groupby("country", as_index=False)
        .sum()
    )

    confirmed_total = sum(cases["cases"].to_list())
    deaths_total = sum(deaths["deaths"].to_list())
    # deaths_total = sum(deaths["deaths"].to_list())
    return render_template(
        "index.html",
        conf="Confirmed: ",
        tconf=confirmed_total,
        death="Deaths: ",
        tdeath=deaths_total,
    )


@app.route("/Request", methods=["GET"])
def request_plot():
    # Get from API
    PAYLOAD = {"code": "ALL"}
    URL = "https://api.statworx.com/covid"
    RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))

    # Convert to data frame
    DFRAME = pd.DataFrame.from_dict(json.loads(RESPONSE.text))

    # Return a list of countries and Representation
    countries = DFRAME.filter(items=["country", "cases"]).groupby(
        "country", as_index=False).sum()["country"].to_list()
    Representation = ["cases", "cases_cum", "deaths", "deaths_cum"]

    return render_template(
        "request_plot.html", Representation=Representation, countries=countries
    )


@app.route("/Plot", methods=["POST"])
def plot():
    message1 = None
    message2 = None
    # POST to API
    country = request.form["country"]
    Repres = request.form["Repres"]

    PAYLOAD = {"country": country}
    URL = "https://api.statworx.com/covid"
    RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))

    # Convert to data frame
    DFRAME = pd.DataFrame.from_dict(json.loads(RESPONSE.text))

    # Retrieves the what Repres will be represent
    x = DFRAME["date"].to_list()
    if Repres == "cases":
        y = DFRAME[Repres].to_list()
        n_t = y
    else:
        y = DFRAME[Repres].to_list()
        n_t = DFRAME["cases"].to_list()

    # Compute the number of cases in day t
    i = 0
    for n in n_t:
        if n == 0:
            i += 1
        else:
            break
    n_t = n_t[i:]

    log_n_t = []
    for i in n_t:
        if i == 0:
            log_n_t.append(0)
        elif i < 0:
            log_n_t.append(0)
            message1 = "The government decreased the number of total cases and the number of deaths. The discrepancy is the result of the validation of the same data by the autonomous communities and the transition to a new surveillance strategy. Discrepancies could persist for several days."
        else:
            log_n_t.append(math.log10(i))

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        range(len(n_t)), log_n_t
    )
    R = 10 ** (slope * 6)

    # Find the population of the country
    population = DFRAME["population"].to_list()

    # Retrive the Hospital beds in each country
    # Source: https://ourworldindata.org/grapher/hospital-beds-per-1000-people?tab=chart&year=2013
    if Repres == "cases_cum":
        try:
            beds_data = pd.read_csv(
                "./static/data/hospital-beds-per-1000-people.csv")
            beds_data.filter(
                items=["Entity", "Year", "Hospital beds (per 100,000)"])
            beds_data = beds_data[beds_data["Year"] == 2014]
            beds_data = beds_data[beds_data["Entity"] == country]

            # Compute the number of beds
            numbers_beds = [
                beds_data["Hospital beds (per 100,000)"].to_list()[
                    0] * (p / 100000)
                for p in population
            ]
        except:
            message2 = "Sorry, but the health care capacity for this country still not supported. It will not appear in the representation"

    # Plot the fitting of R values
    line_chart = pygal.Line(
        legend_at_bottom=True,
        stroke=False,
        pretty_print=True,
        human_readable=True,
        height=200,
        style=DarkStyle,
    )
    line_chart.add(
        "Fitting the data, R = {}".format(R),
        [(intercept + slope * x) for x in range(len(log_n_t))],
    )
    line_chart.add("log(Cases)", log_n_t)
    fig_R = line_chart.render_data_uri()

    # Plot the Repres of requested country
    bar_chart = pygal.Bar(
        legend_at_bottom=True,
        pretty_print=True,
        human_readable=True,
        height=300,
        style=DarkStyle,
        tooltip_position="top left",
    )
    bar_chart.x_labels = x
    bar_chart.add(Repres, y)
    if Repres == "cases_cum" and message2 is None:
        bar_chart.add("Health Care Capacity", numbers_beds)
    fig = bar_chart.render_data_uri()

    return render_template(
        "plots.html", country=country, fig=fig, fig_R=fig_R, message1=message1, message2=message2
    )


@app.route("/World_Map", methods=["GET"])
def world_map():
    # Get data from API
    PAYLOAD = {"code": "ALL"}
    URL = "https://api.statworx.com/covid"
    RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))

    # Convert to data frame
    DFRAME = pd.DataFrame.from_dict(json.loads(RESPONSE.text))

    # Return a list of codes of countries and Representation and cases and deaths
    codes = [code.lower() for code in (DFRAME.filter(items=["code", "cases"]).groupby(
        "code", as_index=False).sum()["code"].to_list())]
    Representation = ["cases", "cases_cum", "deaths", "deaths_cum"]

    cases = (
        DFRAME.filter(items=["code", "cases"]).groupby(
            "code").sum().to_dict()["cases"]
    )
    deaths = (
        DFRAME.filter(items=["code", "deaths"])
        .groupby("code")
        .sum()
        .to_dict()["deaths"]
    )

    # Initial the World Map
    WorldMap = world.World(
        show_legend=False,
        pretty_print=True,
        human_readable=True,
        style=DarkStyle,
        tooltip_position=None,
    )

    # Bind the code of country to the number of its cases and deaths
    dict_cases_deaths = {}
    for code in codes:
        dict_cases_deaths[code] = {
            "Cases: {}, Deaths: {}".format(
                cases[code.upper()], deaths[code.upper()])
        }

    # Plot the data
    WorldMap.title = "Current Statistics of Deaths and Cases; updated every day"
    WorldMap.add("General Statistics", dict_cases_deaths)
    fig = WorldMap.render_data_uri()

    return render_template("world_map.html", fig=fig)


@app.route("/Top_Deaths")
def top_deaths():
    line_chart = pygal.Bar(
        title=u"Top Deaths Countries",
        pretty_print=True,
        human_readable=True,
        height=200,
        style=DarkStyle,
    )

    # POST to API
    PAYLOAD = {"code": "ALL"}
    URL = "https://api.statworx.com/covid"
    RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))

    # Convert to data frame
    DFRAME = pd.DataFrame.from_dict(json.loads(RESPONSE.text))

    deaths = (
        DFRAME.filter(items=["code", "country", "deaths"])
        .groupby("country", as_index=False)
        .sum()
    )
    deaths.sort_values(by=["deaths"], ascending=False, inplace=True)

    top_deaths_count = deaths["country"].to_list()[0:10]
    top_deaths_value = deaths["deaths"].to_list()[0:10]

    # Plot the data
    line_chart.x_labels = top_deaths_count
    line_chart.add("Deaths", top_deaths_value)
    fig = line_chart.render_data_uri()

    return render_template("top_deaths.html", fig=fig)


@app.route("/Top_Affected")
def top_affected():
    line_chart = pygal.Bar(
        title=u"Top Affected Countries",
        pretty_print=True,
        human_readable=True,
        height=200,
        style=DarkStyle,
    )

    # POST to API
    PAYLOAD = {"code": "ALL"}
    URL = "https://api.statworx.com/covid"
    RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))

    # Convert to data frame
    DFRAME = pd.DataFrame.from_dict(json.loads(RESPONSE.text))

    cases = (
        DFRAME.filter(items=["code", "country", "cases"])
        .groupby("country", as_index=False)
        .sum()
    )
    cases.sort_values(by=["cases"], ascending=False, inplace=True)

    top_cases_count = cases["country"].to_list()[0:10]
    top_cases_value = cases["cases"].to_list()[0:10]

    # Plot the data
    line_chart.x_labels = top_cases_count
    line_chart.add("Cases", top_cases_value)
    fig = line_chart.render_data_uri()

    return render_template("top_affected.html", fig=fig)


if __name__ == "__main__":
    app.run(debug=True)

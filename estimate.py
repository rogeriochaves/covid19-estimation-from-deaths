import numpy as np
import pandas as pd
import math
import datetime
import collections
import os
import json
import requests


reproduction_number = 2
shape = 4.726
rate = 0.3151
case_fatality_ratio = 0.02

# From R implementation, discrete lognorm distribution
serial_intervals = [0.07304178, 0.1380941983, 0.1254991537, 0.1031686847, 0.0833675732, 0.0675321901,
                    0.0551452103, 0.0454561453, 0.0378228034, 0.0317515990, 0.0268743872,
                    0.0229180320, 0.0196790215, 0.0170044781, 0.0147784468, 0.0129120896,
                    0.0113366661, 0.0099984770, 0.0088551917, 0.0078731556, 0.0070253962,
                    0.0062901340, 0.0056496578, 0.0050894699, 0.0045976289, 0.0041642418,
                    0.0037810675, 0.0034412056, 0.0031388501, 0.0028690930, 0.0026277681,
                    0.0024113235, 0.0022167196, 0.0020413456, 0.0018829508, 0.0017395888,
                    0.0016095705, 0.0014914261, 0.0013838725, 0.0012857867, 0.0011961830,
                    0.0011141943, 0.0010390555, 0.0009700905, 0.0009066999, 0.0008483516,
                    0.0007945720, 0.0007449388, 0.0006990746, 0.0006566419, 0.0006173378]


def move_yyyy_mm_dd(dt, days):
    return (datetime.datetime.strptime(dt, "%Y-%m-%d") + datetime.timedelta(days=days)).strftime("%Y-%m-%d")


# Example a single death
def simulate_one(death, simulations=50):
    probable_days_ago_onset = int(np.random.gamma(shape, rate) * 10)
    n_cases_per_day = np.random.geometric(case_fatality_ratio)
    onset_date = move_yyyy_mm_dd(death, -probable_days_ago_onset)

    incidences = {
        onset_date: n_cases_per_day
    }
    from_onset_to_today = (datetime.datetime.today(
    ) - datetime.datetime.strptime(onset_date, "%Y-%m-%d")).days + 1

    for t in range(1, from_onset_to_today):
        lambda_t = sum([incidences[move_yyyy_mm_dd(onset_date, s)]
                        * serial_intervals[min(t - s, 50)] for s in range(0, t)])
        incidences_t = np.random.poisson(
            lambda_t * reproduction_number, simulations)
        incidences[move_yyyy_mm_dd(onset_date, t)] = incidences_t

    del incidences[onset_date]
    return incidences


def simulate_multiple(deaths):
    projections = [simulate_one(death) for death in deaths]
    result = {}
    for projection in projections:
        for key in projection.keys():
            if key not in result:
                result[key] = projection[key]
            else:
                result[key] = np.array(result[key]) + np.array(projection[key])

    return result


def sorted_collection(collection):
    return collections.OrderedDict(sorted(collection.items()))


def simulate_multiple_many_times(deaths, trajectories_simulations):
    projections = [simulate_multiple(deaths)
                   for _ in range(0, trajectories_simulations)]
    result = {}
    for projection in projections:
        for key in projection.keys():
            if key not in result:
                result[key] = projection[key]
            else:
                result[key] = np.concatenate([result[key], projection[key]])
    return result


def map_percentiles(simulations):
    percentiles = {}
    for key in simulations.keys():
        pcts = np.percentile(simulations[key], [1, 5, 95, 100])
        percentiles[key] = {1: pcts[0], 5: pcts[1], 95: pcts[2], 100: pcts[3]}
    return percentiles


def multiply_dates_per_deaths(deaths_df):
    total_deaths = 0
    sorted_df = deaths_df.sort_values(by=['date'])
    dates = []
    for date in sorted_df.date:
        new_deaths = int(
            sorted_df[(sorted_df.date == date)].deaths) - total_deaths
        dates += [date] * new_deaths
        total_deaths += new_deaths
    return dates


os.system("""
rm caso.csv.gz;
wget https://data.brasil.io/dataset/covid19/caso.csv.gz;
rm caso.csv;
gunzip caso.csv.gz;
""")

df = pd.read_csv("caso.csv")
print("Samples:", df.head())

states_with_death = df[(df.deaths > 0) & (df.place_type == "state")]
states_with_death = list(np.unique(states_with_death["state"])) + ["BR"]

result = {}
for state in states_with_death:
    print("Simulating", state)
    if state == "BR":
        deaths_state = df[(df.deaths > 0) & (df.place_type == "state")]
        deaths_state = deaths_state[["date", "deaths"]].groupby(
            ['date']).sum().reset_index()
    else:
        deaths_state = df[(df.deaths > 0) & (
            df.place_type == "state") & (df.state == state)]

    dates = multiply_dates_per_deaths(deaths_state)
    simulations = simulate_multiple_many_times(
        dates, trajectories_simulations=100)
    sorted_percentiles = sorted_collection(map_percentiles(simulations))
    result[state] = sorted_percentiles

with open('result.json', 'w') as f:
    json.dump(result, f)
    print("Saved to result.json")

requests.put(
    "https://api.myjson.com/bins/1ddqtw",
    headers={"Content-Type": "application/json"},
    data=json.dumps(result),
    timeout=None
)
print("Saved to https://api.myjson.com/bins/1ddqtw")

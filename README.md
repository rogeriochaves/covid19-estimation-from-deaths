# COVID19 estimation from deaths

This project generates infected cases estimations for [covid19br.app](https://covid19br.app/), those estimations use the algorithm from this other project [github.com/thibautjombart/covid19_cases_from_deaths](https://github.com/thibautjombart/covid19_cases_from_deaths), but we rebuilt the implementation in Python instead of R

It works by [running a job on circleci](https://app.circleci.com/pipelines/github/rogeriochaves/covid19-estimation-from-deaths) every day, and publishing the updated estimations so [covid19br.app](https://covid19br.app/) can consume
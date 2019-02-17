# Samu Social Hackathon at the Hive

# Context

To help the [_Samu Social de Paris_](https://www.samusocial.paris/) visit the different hotels we propose a 
tool to help the visit planing process. 

- Our solution proposes to:
    - Create pairs of workers that are available for a visit on a shared time window
    - Propose itinerary of hotel to visit for each pairs of workers based on their initial localisation.
 
## Setup

NB: Phe project runs on `python 3.6`
1. create a virtualenv
````bash
python3 -m venv samu_social
````

2. Install requirements
````bash
pip install -r requirements.txt
````

3. Run the main to get itineraries based on the data provided in the hackathon (not shared in this repo)
````bash
python src/main.py
````


## Useful resources
https://adresse.data.gouv.fr/api (to get `long` and `lat` from an address)

Google [OR-Tools](https://developers.google.com/optimization/routing/) for optimisation 
and especially routing problem.
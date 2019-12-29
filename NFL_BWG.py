"""A class that searches for close NFL games, or possibly any
date in future versions, and determines if the game will be subject to
'Bad weather' i.e snow.

The class is dependant upon nflgame and DarSky API's for schedule and
weather data respectively.
"""
import json
from datetime import datetime, timezone, timedelta
from dateutil import tz
from darksky.api import DarkSky
from darksky.types import weather

import nflgame

class BadWeatherGames():
    """This is a class to lookup weather for upcoming NFL games, and report to
    the user"""

    # The Games are reported in EST, so we set up an EST timezone class
    est =  tz.gettz('America/New_York')
    local_tz = tz.tzlocal()
    
    with open('Api_keys.json') as key:
        DSapi_key = json.load(key)['DS_api']

    nfl_teams = [team[0] for team in nflgame.teams]
    nfl_lat = [33.52713000000,
               33.75735000000,
               39.27790000000,
               42.77379000000,
               35.22584000000,
               41.86250000000,
               39.09532000000,
               41.50618000000,
               32.74778000000,
               39.74396000000,
               42.34005000000,
               44.50117000000,
               29.68493000000,
               39.76000000000,
               30.32387000000,
               39.04895000000,
               34.01387500000,
               32.78322000000,
               33.86423500000,
               25.95801000000,
               44.97401000000,
               42.09188000000,
               29.95116000000,
               40.81361000000,
               40.81361000000,
               37.75233000000,
               39.90147000000,
               40.44673000000,
               47.59476000000,
               37.71399000000,
               38.63278000000,
               27.97884000000,
               36.16654000000,
               38.90778000000,
               38.90748500000,
               ]
    nfl_long = [-112.25876000000,
                -84.40121000000,
                -76.62270000000,
                -78.78679000000,
                -80.85331000000,
                -87.61677000000,
                -84.51623000000,
                -81.69962000000,
                -97.09277000000,
                -105.02028000000,
                -83.04564000000,
                -88.06223000000,
                -95.41092000000,
                -86.16361000000,
                -81.63690000000,
                -94.48388000000,
                -118.2879290000,
                -117.11976000000,
                -118.261314000000,
                -80.23889000000,
                -93.25848000000,
                -71.26491000000,
                -90.08128000000,
                -74.07444000000,
                -74.07444000000,
                -122.19990000000,
                -75.16729000000,
                -80.01574000000,
                -122.33165000000,
                -122.38673000000,
                -90.18854000000,
                -82.50349000000,
                -86.77252000000,
                -76.86444000000
                ]
    nfl_dict = dict(zip(nfl_teams, zip(nfl_lat, nfl_long)))
    #Additions
    nfl_dict['JAX'] = (30.32387, -81.6369)


    def __init__(self):
        self.y_w_p = self.nfl_week()
        self.games = self.get_games()
        self.snow_games = self.check_for_snow_games()

    @staticmethod
    def nfl_week():
        """This function wraps nflgame live calls for the year, week and phase
        into one call."""

        year, week = nflgame.live.current_year_and_week()
        phase = nflgame.live.current_season_phase()
        return [year, week, phase]

    def game_format(self, game):
        """Used to extract pertenant info from nflgame class, and format date"""
        # Parses usefull data from nflgame instance
        sch = game.schedule
        
        
        gametime = datetime(year=sch['year'],
                            month=sch['month'],
                            day=sch['day'],
                            hour=12 + int(sch['time'].split(':')[0]),
                            minute=int(sch['time'].split(':')[1]),
                            )
        gametime = gametime.replace(tzinfo=self.est)
        
        keys = ['Away', 'Home', 'Gametime']
        vals = [nflgame.standard_team(sch['away']),
                nflgame.standard_team(sch['home']),
                gametime
                ]
        _dict = dict(zip(keys, vals))

        return _dict

    def get_games(self):
        """
        Returns
        -------
        clean_games : Map
            Looks up NFL games starting this week and returns them after parseing
            them through the game_format method.
        """
        raw_games = nflgame.games(year=self.y_w_p[0],
                                  week=self.y_w_p[1],
                                  kind=self.y_w_p[2]
                                  )

        clean_games = map(self.game_format, raw_games)

        return clean_games

    def get_weather(self, c_game):
        """
        Parameters
        ----------
        c_game : Dict
            A cleaned game dictionary.

        Returns
        -------
        c_game : Dict
            A cleaned game dictionary with new, relevant, snow precipitation
            forecast information added from DarkSky. Weather data is from the
            hour nearest to kick-off.
        """
        d_s = DarkSky(self.DSapi_key)

        ex_list = [weather.MINUTELY, weather.ALERTS,
                   weather.DAILY, weather.FLAGS
                   ]
        _lat, _long = BadWeatherGames.nfl_dict[c_game['Home']]
        _time = c_game['Gametime']

        forecast = d_s.get_time_machine_forecast(_lat, _long, _time,
                                                 exclude=ex_list,
                                                 timezone='America/New_York'
                                                 )

        c_game['Precip_prob'] = forecast.currently.precip_probability
        c_game['Precip_type'] = forecast.currently.precip_type
        c_game['Precip_intensity'] = forecast.currently.precip_intensity
        c_game['Precip_accum'] = forecast.currently.precipAccumulation

        return c_game

    def check_for_snow_games(self):
        """
        Returns
        -------
        snow_games : List
            Maps the games list through the get_weather method before checking
            if weather data indicates snow. Text is printed with pertinent
            inforamtion.

        """
        
        cw_games = map(self.get_weather, self.games)
        snow_games = [cw_game for cw_game in cw_games if
                      cw_game['Precip_type'] == 'snow']

        if len(snow_games) > 0:
            num_games = len(snow_games)
            print(f'Number of Snow Games : {num_games}')

            for cws_game in snow_games:
                prob = cws_game['Precip_prob']
                away = cws_game['Away']
                home = cws_game['Home']
                _datetime = cws_game['Gametime'].astimezone(self.local_tz)
                date_string = _datetime.strftime('%d/%m/%Y, %H:%M')
                accu = cws_game['Precip_accum']
                dash = 90

                Y = f"""
                {'-'*dash}
                There's a probability of {prob*100} % that snow will fall during the {away} @ {home} game at {date_string} Local time.
                The snow depth could be upto {accu} Inches deep.

                {'-'*dash}
                """
                print(Y)

        else:
            N = f"""
            {'-'*dash}
            Snow is currently not predicted to fall at any NFL games this week.
            {'-'*dash}
            """
            print(N)

        return snow_games

if __name__ == '__main__':

    INST = BadWeatherGames()

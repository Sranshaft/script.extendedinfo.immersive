import xbmcaddon
import os
import xbmc
from Utils import *
import urllib
from urllib2 import Request, urlopen

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_strings = addon.getLocalizedString
Addon_Data_Path = os.path.join(xbmc.translatePath("special://profile/addon_data/%s" % addon_id).decode("utf-8"))

moviedb_key = '34142515d9d23817496eeb4ff1d223d0'
base_url = ""
poster_size = ""
fanart_size = ""
homewindow = xbmcgui.Window(10000)
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'User-agent': 'XBMC/13.2 ( ptemming@gmx.net )'
}

poster_sizes = ["w92", "w154", "w185", "w342", "w500", "w780", "original"]
logo_sizes = ["w45", "w92", "w154", "w185", "w300", "w500", "original"]
backdrop_sizes = ["w300", "w780", "w1280", "original"]
profile_sizes = ["w45", "w185", "h632", "original"]
still_sizes = ["w92", "w185", "w300", "original"]

def checkLogin():
    if addon.getSetting("tmdb_username"):
        session_id = get_session_id()
        if session_id:
            return True
    return ""

def RateMovie(movieid, rating):
    if addon.getSetting("tmdb_username"):
        session_id_string = "session_id=" + get_session_id()
    else:
        session_id_string = "guest_session_id=" + get_guest_session_id()
    values = '{"value": %.1f}' % rating
    url = "http://api.themoviedb.org/3/movie/%s/rating?api_key=%s&%s" % (str(movieid), moviedb_key, session_id_string)
    request = Request(url, data=values, headers=headers)
    response = urlopen(request).read()
    results = simplejson.loads(response)
    # prettyprint(results)
    Notify(addon_name, results["status_message"])

def ChangeFavStatus(media_id=None, media_type="movie", status="true"):
    session_id = get_session_id()
    account_id = get_account_info()
    values = '{"media_type": "%s", "media_id": %s, "favorite": %s}' % (media_type, str(media_id), status)
    url = "http://api.themoviedb.org/3/account/%s/favorite?session_id=%s&api_key=%s" % (str(account_id), str(session_id), moviedb_key)
    request = Request(url, data=values, headers=headers)
    response = urlopen(request).read()
    results = simplejson.loads(response)
    # prettyprint(results)
    Notify(addon_name, results["status_message"])

def CreateList(listname):
    session_id = get_session_id()
    url = "http://api.themoviedb.org/3/list?api_key=%s&session_id=%s" % (moviedb_key, session_id)
    values = {'name': '%s' % listname, 'description': 'List created by ExtendedInfo Script for Kodi.'}
    request = Request(url, data=simplejson.dumps(values), headers=headers)
    response = urlopen(request).read()
    results = simplejson.loads(response)
    # prettyprint(results)
    Notify(addon_name, results["status_message"])
    return results["list_id"]

def AddItemToList(list_id, movie_id):
    session_id = get_session_id()
    url = "http://api.themoviedb.org/3/list/%s/add_item?api_key=%s&session_id=%s" % (list_id, moviedb_key, session_id)
    values = {'media_id': movie_id}
    request = Request(url, data=simplejson.dumps(values), headers=headers)
    response = urlopen(request).read()
    results = simplejson.loads(response)
    Notify(addon_name, results["status_message"])

def GetAccountLists():
    session_id = get_session_id()
    account_id = get_account_info()
    response = GetMovieDBData("account/%s/lists?session_id=%s&" % (str(account_id), session_id), 0)
    # prettyprint(response)
    return response["results"]

def get_account_info():
    session_id = get_session_id()
    response = GetMovieDBData("account?session_id=%s&" % session_id, 999999)
    # prettyprint(response)
    return response["id"]

def get_guest_session_id():
    response = GetMovieDBData("authentication/guest_session/new?", 999999)
    # prettyprint(response)
    return response["guest_session_id"]

def get_session_id():
    request_token = auth_request_token()
    response = GetMovieDBData("authentication/session/new?request_token=%s&" % request_token, 0.1)
    # prettyprint(response)
    if response and "success" in response:
        passDictToSkin({"tmdb_logged_in": "true"})
        return response["session_id"]
    else:
        passDictToSkin({"tmdb_logged_in": ""})
        Notify("login failed")
        return None

def get_request_token():
    response = GetMovieDBData("authentication/token/new?", 0.1)
    # prettyprint(response)
    return response["request_token"]

def auth_request_token():
    request_token = get_request_token()
    username = addon.getSetting("tmdb_username")
    password = addon.getSetting("tmdb_password")
    response = GetMovieDBData("authentication/token/validate_with_login?request_token=%s&username=%s&password=%s&" % (request_token, username, password), 0.1)
    # prettyprint(response)
    if response["success"]:
        return response["request_token"]
    else:
        return None

def HandleTMDBMovieResult(results=[], local_first=True, sortkey="Year"):
    movies = []
    ids = []
    log("starting HandleTMDBMovieResult")
    for movie in results:
        tmdb_id = str(fetch(movie, 'id'))
        if ("backdrop_path" in movie) and (movie["backdrop_path"]):
            backdrop_path = base_url + fanart_size + movie['backdrop_path']
        else:
            backdrop_path = ""
        if ("poster_path" in movie) and (movie["poster_path"]):
            poster_path = base_url + poster_size + movie['poster_path']
            small_poster_path = base_url + "w342" + movie["poster_path"]
        else:
            poster_path = ""
            small_poster_path = ""
        release_date = fetch(movie, 'release_date')
        if release_date:
            year = release_date[:4]
            time_comparer = release_date.replace("-", "")
        else:
            year = ""
            time_comparer = ""
        trailer = "plugin://script.extendedinfo.immersive/?info=playtrailer&&id=" + tmdb_id
        if addon.getSetting("infodialog_onclick"):
            path = 'plugin://script.extendedinfo.immersive/?info=extendedinfo&&id=%s' % tmdb_id
        else:
            path = trailer
        newmovie = {'Art(fanart)': backdrop_path,
                    'Art(poster)': small_poster_path,  # needs to be adjusted to poster_path (-->skin)
                    'Thumb': small_poster_path,
                    'Poster': small_poster_path,
                    'Fanart': backdrop_path,
                    'Title': fetch(movie, 'title'),
                    'Label': fetch(movie, 'title'),
                    'OriginalTitle': fetch(movie, 'original_title'),
                    'Plot': fetch(movie, 'overview'),
                    'ID': tmdb_id,
                    'Path': path,
                    'Trailer': trailer,
                    'Rating': fetch(movie, 'vote_average'),
                    'Credit_id': fetch(movie, 'credit_id'),
                    'Character': fetch(movie, 'character'),
                    'Votes': fetch(movie, 'vote_count'),
                    'User_Rating': fetch(movie, 'rating'),
                    'Year': year,
                    'Time_comparer': time_comparer,
                    'Premiered': release_date}
        if not tmdb_id in ids:
            ids.append(tmdb_id)
            movies.append(newmovie)
    movies = CompareWithLibrary(movies, local_first, sortkey)
    return movies


def HandleTMDBTVShowResult(results, local_first=True, sortkey="year"):
    tvshows = []
    ids = []
    log("starting HandleTMDBTVShowResult")
    for tv in results:
        tmdb_id = fetch(tv, 'id')
        poster_path = ""
        duration = ""
        year = ""
        backdrop_path = ""
        if ("backdrop_path" in tv) and (tv["backdrop_path"]):
            backdrop_path = base_url + fanart_size + tv['backdrop_path']
        if ("poster_path" in tv) and (tv["poster_path"]):
            poster_path = base_url + poster_size + tv['poster_path']
        if "episode_run_time" in tv:
            if len(tv["episode_run_time"]) > 1:
                duration = "%i - %i" % (min(tv["episode_run_time"]), max(tv["episode_run_time"]))
            else:
                duration = "%i" % (tv["episode_run_time"][0])
        release_date = fetch(tv, 'first_air_date')
        if release_date:
            year = release_date[:4]
        newtv = {'Art(fanart)': backdrop_path,
                 'Art(poster)': poster_path,
                 'Thumb': poster_path,
                 'Poster': poster_path,
                 'Fanart': backdrop_path,
                 'Title': fetch(tv, 'name'),
                 'OriginalTitle': fetch(tv, 'original_name'),
                 'Duration': duration,
                 'ID': tmdb_id,
                 'Credit_id': fetch(tv, 'credit_id'),
                 'Plot': fetch(tv, "overview"),
                 'Year': year,
                 'Path': 'plugin://script.extendedinfo.immersive/?info=extendedtvinfo&&id=%s' % tmdb_id,
                 'Rating': fetch(tv, 'vote_average'),
                 'Votes': fetch(tv, 'vote_count'),
                 'Status': fetch(tv, 'status'),
                 'Homepage': fetch(tv, 'homepage'),
                 'Last_air_date': fetch(tv, 'last_air_date'),
                 'First_air_date': release_date,
                 'Number_of_episodes': fetch(tv, 'number_of_episodes'),
                 'Number_of_seasons': fetch(tv, 'number_of_seasons'),
                 'In_production': fetch(tv, 'in_production'),
                 'Release_Date': release_date,
                 'ReleaseDate': release_date,
                 'Premiered': release_date}
        if not tmdb_id in ids:
            ids.append(tmdb_id)
            tvshows.append(newtv)
    # tvshows = CompareWithLibrary(tvshows, local_first, sortkey)
    return tvshows


def HandleTMDBMiscResult(results):
    listitems = []
    for item in results:
        poster_path = ""
        small_poster_path = ""
        if ("poster_path" in item) and (item["poster_path"]):
            poster_path = base_url + poster_size + item['poster_path']
            small_poster_path = base_url + "w342" + item["poster_path"]
        listitem = {'Art(poster)': poster_path,
                    'Poster': poster_path,
                    'Thumb': small_poster_path,
                    'Title': fetch(item, 'name'),
                    'Certification': fetch(item, 'certification'),
                    'Item_count': fetch(item, 'item_count'),
                    'Favorite_count': fetch(item, 'favorite_count'),
                    'Release_date': fetch(item, 'release_date'),
                    'ISO_3166_1': fetch(item, 'iso_3166_1'),
                    'Author': fetch(item, 'author'),
                    'Content': fetch(item, 'content'),
                    'ID': fetch(item, 'id'),
                    'Url': fetch(item, 'url'),
                    'Description': fetch(item, 'description')}
        listitems.append(listitem)
    return listitems

def HandleTMDBSeasonResult(results):
    listitems = []
    for season in results:
        year = ""
        poster_path = ""
        season_number = str(fetch(season, 'season_number'))
        small_poster_path = ""
        air_date = fetch(season, 'air_date')
        if air_date:
            year = air_date[:4]
        if ("poster_path" in season) and season["poster_path"]:
            poster_path = base_url + poster_size + season['poster_path']
            small_poster_path = base_url + "w342" + season["poster_path"]
        if season_number == "0":
            Title = "Specials"
        else:
            Title = "Season %s" % season_number
        listitem = {'Art(poster)': poster_path,
                    'Poster': poster_path,
                    'Thumb': small_poster_path,
                    'Title': Title,
                    'Season': season_number,
                    'air_date': air_date,
                    'Year': year,
                    'ID': fetch(season, 'id')}
        listitems.append(listitem)
    return listitems

def HandleTMDBVideoResult(results):
    listitems = []
    for item in results:
        image = "http://i.ytimg.com/vi/" + fetch(item, 'key') + "/0.jpg"
        listitem = {'Thumb': image,
                    'Title': fetch(item, 'name'),
                    'iso_639_1': fetch(item, 'iso_639_1'),
                    'type': fetch(item, 'type'),
                    'key': fetch(item, 'key'),
                    'youtube_id': fetch(item, 'key'),
                    'site': fetch(item, 'site'),
                    'ID': fetch(item, 'id'),
                    'size': fetch(item, 'size')}
        listitems.append(listitem)
    return listitems

def HandleTMDBPeopleResult(results):
    people = []
    for person in results:
        image = ""
        image_small = ""
        description = "[B]Known for[/B]:[CR][CR]"
        if "known_for" in results:
            for movie in results["known_for"]:
                description = description + movie["title"] + " (%s)" % (movie["release_date"]) + "[CR]"
        builtin = 'RunScript(script.extendedinfo,info=extendedactorinfo,id=%s)' % str(person['id'])
        if "profile_path" in person and person["profile_path"]:
            image = base_url + poster_size + person["profile_path"]
            image_small = base_url + "w342" + person["profile_path"]
        alsoknownas = " / ".join(fetch(person, 'also_known_as'))
        newperson = {'adult': str(fetch(person, 'adult')),
                     'name': person['name'],
                     'title': person['name'],
                     'also_known_as': alsoknownas,
                     'alsoknownas': alsoknownas,
                     'biography': cleanText(fetch(person, 'biography')),
                     'birthday': fetch(person, 'birthday'),
                     'age': calculate_age(fetch(person, 'birthday')),
                     'character': fetch(person, 'character'),
                     'department': fetch(person, 'department'),
                     'job': fetch(person, 'job'),
                     'description': description,
                     'plot': description,
                     'id': str(person['id']),
                     'cast_id': str(fetch(person, 'cast_id')),
                     'credit_id': str(fetch(person, 'credit_id')),
                     'path': "plugin://script.extendedinfo.immersive/?info=action&&id=" + builtin,
                     'deathday': fetch(person, 'deathday'),
                     'place_of_birth': fetch(person, 'place_of_birth'),
                     'placeofbirth': fetch(person, 'place_of_birth'),
                     'homepage': fetch(person, 'homepage'),
                     'thumb': image_small,
                     'icon': image_small,
                     'poster': image}
        people.append(newperson)
    return people


def HandleTMDBPeopleImagesResult(results):
    images = []
    for item in results:
        image = {'aspectratio': item['aspect_ratio'],
                 'thumb': base_url + "w342" + item['file_path'],
                 'vote_average': fetch(item, "vote_average"),
                 'iso_639_1': fetch(item, "iso_639_1"),
                 'poster': base_url + poster_size + item['file_path']}
        images.append(image)
    return images


def HandleTMDBPeopleTaggedImagesResult(results):
    images = []
    if "tagged_images" in results:
        for item in results["tagged_images"]["results"]:
            image = {'aspectratio': item['aspect_ratio'],
                     'thumb': base_url + "w342" + item['file_path'],
                     'vote_average': fetch(item, "vote_average"),
                     'iso_639_1': fetch(item, "iso_639_1"),
                     'poster': base_url + poster_size + item['file_path']}
            images.append(image)
        return images
    else:
        return []


def HandleTMDBCompanyResult(results):
    companies = []
    log("starting HandleLastFMCompanyResult")
    for company in results:
        newcompany = {'parent_company': company['parent_company'],
                      'name': company['name'],
                      'description': company['description'],
                      'headquarters': company['headquarters'],
                      'homepage': company['homepage'],
                      'id': company['id'],
                      'logo_path': company['logo_path']}
        companies.append(newcompany)
    return companies

def GetActorMovieCredits(actor_id):
    response = GetMovieDBData("person/%s/movie_credits?" % (actor_id), 1)
    return HandleTMDBMovieResult(response["cast"])

def GetActorTVShowCredits(actor_id):
    response = GetMovieDBData("person/%s/tv_credits?" % (actor_id), 1)
    return HandleTMDBMovieResult(response["cast"])

def GetCompanyInfo(company_id):
    response = GetMovieDBData("company/%s/movies?append_to_response=movies&" % (company_id), 30)
    if response and "results" in response:
        return HandleTMDBMovieResult(response["results"])
    else:
        return []

def GetCreditInfo(credit_id):
    response = GetMovieDBData("credit/%s?language=%s&" % (str(credit_id), addon.getSetting("LanguageID")), 30)
    # if response and "results" in response:
    # prettyprint(response)
        # return HandleTMDBMovieResult(response["results"])
    # else:
    #     return []

def GetDirectorMovies(person_id):
    response = GetMovieDBData("person/%s/credits?language=%s&" % (person_id, addon.getSetting("LanguageID")), 14)
    # return HandleTMDBMovieResult(response["crew"]) + HandleTMDBMovieResult(response["cast"])
    if "crew" in response:
        return HandleTMDBMovieResult(response["crew"])
    else:
        log("No JSON Data available")

def GetExtendedActorInfo(actorid):
    response = GetMovieDBData("person/%s?append_to_response=tv_credits,movie_credits,combined_credits,images,tagged_images&" % (actorid), 1)
    movie_roles = Get_ListItems_Thread(HandleTMDBMovieResult, response["movie_credits"]["cast"])
    tvshow_roles = Get_ListItems_Thread(HandleTMDBTVShowResult, response["tv_credits"]["cast"])
    movie_crew_roles = Get_ListItems_Thread(HandleTMDBMovieResult, response["movie_credits"]["crew"])
    tvshow_crew_roles = Get_ListItems_Thread(HandleTMDBTVShowResult, response["tv_credits"]["crew"])
    poster_thread = Get_ListItems_Thread(HandleTMDBPeopleImagesResult, response["images"]["profiles"])
    threads = [movie_roles, tvshow_roles, movie_crew_roles, tvshow_crew_roles, poster_thread]
    for item in threads:
        item.start()
    for item in threads:
        item.join()
    tagged_images = []
    if "tagged_images" in response:
        tagged_images = HandleTMDBPeopleTaggedImagesResult(response["tagged_images"]["results"])
    answer = {"general": HandleTMDBPeopleResult([response])[0],
              "movie_roles": movie_roles.listitems,
              "tvshow_roles": tvshow_roles.listitems,
              "movie_crew_roles": movie_crew_roles.listitems,
              "tvshow_crew_roles": tvshow_crew_roles.listitems,
              "tagged_images": tagged_images,
              "images": poster_thread.listitems}
    return answer

def GetExtendedMovieInfo(movieid=None, dbid=None, cache_time=30):
    session_string = ""
    if addon.getSetting("tmdb_username"):
        session_string = "session_id=%s&" % (get_session_id())
    response = GetMovieDBData("movie/%s?append_to_response=account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating&include_image_language=en,null,%s&language=%s&%s" % (movieid, addon.getSetting("LanguageID"), addon.getSetting("LanguageID"), session_string), cache_time)

    authors = []
    directors = []
    genres = []
    year = ""
    Country = ""
    Studio = []
    mpaa = ""
    SetName = ""
    SetID = ""
    poster_path = ""
    poster_path_small = ""
    backdrop_path = ""

    if not response:
        Notify("Could not get movie information")
        return {}
    for item in response['genres']:
        genres.append(item["name"])
    for item in response['credits']['crew']:
        if item["job"] == "Author":
            authors.append(item["name"])
        if item["job"] == "Director":
            directors.append(item["name"])
    if len(response['releases']['countries']) > 0:
        mpaa = response['releases']['countries'][0]['certification']
    else:
        mpaa = ""
    if len(response['production_countries']) > 0:
        Country = response['production_countries'][0]["name"]
    else:
        Country = ""
    Studio = []
    for item in response['production_companies']:
        Studio.append(item["name"])
    Studio = " / ".join(Studio)
    Set = fetch(response, "belongs_to_collection")
    if Set:
        SetName = fetch(Set, "name")
        SetID = fetch(Set, "id")
    else:
        SetName = ""
        SetID = ""
    if 'release_date' in response and fetch(response, 'release_date') is not None:
        year = fetch(response, 'release_date')[:4]
    else:
        year = ""
    Budget = millify(fetch(response, 'budget'))
    Revenue = millify(fetch(response, 'revenue'))
    if ("backdrop_path" in response) and (response["backdrop_path"]):
        backdrop_path = base_url + fanart_size + response['backdrop_path']
    else:
        backdrop_path = ""
    if ("poster_path" in response) and (response["poster_path"]):
        poster_path = base_url + poster_size + response['poster_path']
        poster_path_small = base_url + "w342" + response['poster_path']
        poster_path = Get_File(poster_path)
    path = 'plugin://script.extendedinfo.immersive/?info=youtubevideo&&id=%s' % str(fetch(response, "id"))
    movie = {'Art(fanart)': backdrop_path,
             'Art(poster)': poster_path,
             'Thumb': poster_path_small,
             'Poster': poster_path,
             'Fanart': backdrop_path,
             'Title': fetch(response, 'title'),
             'Label': fetch(response, 'title'),
             'Tagline': fetch(response, 'tagline'),
             'Duration': fetch(response, 'runtime'),
             'mpaa': mpaa,
             'Director': " / ".join(directors),
             'Writer': " / ".join(authors),
             'Budget': Budget,
             'Revenue': Revenue,
             'Homepage': fetch(response, 'homepage'),
             'Set': SetName,
             'SetId': SetID,
             'ID': fetch(response, 'id'),
             'Plot': fetch(response, 'overview'),
             'OriginalTitle': fetch(response, 'original_title'),
             'Genre': " / ".join(genres),
             'Rating': fetch(response, 'vote_average'),
             'Votes': fetch(response, 'vote_count'),
             'Adult': str(fetch(response, 'adult')),
             'Popularity': fetch(response, 'popularity'),
             'Status': fetch(response, 'status'),
             'Path': path,
             'ReleaseDate': fetch(response, 'release_date'),
             'Premiered': fetch(response, 'release_date'),
             'Country': Country,
             'Studio': Studio,
             'Year': year}
    if "videos" in response:
        videos = HandleTMDBVideoResult(response["videos"]["results"])
    else:
        videos = []
    if "account_states" in response:
        account_states = response["account_states"]
    else:
        account_states = None
    similar_thread = Get_ListItems_Thread(HandleTMDBMovieResult, response["similar"]["results"])
    actor_thread = Get_ListItems_Thread(HandleTMDBPeopleResult, response["credits"]["cast"])
    crew_thread = Get_ListItems_Thread(HandleTMDBPeopleResult, response["credits"]["crew"])
    poster_thread = Get_ListItems_Thread(HandleTMDBPeopleImagesResult, response["images"]["posters"])
    threads = [similar_thread, actor_thread, crew_thread, poster_thread]
    for item in threads:
        item.start()
    for item in threads:
        item.join()
    answer = {"general": CompareWithLibrary([movie])[0],
              "actors": actor_thread.listitems,
              "similar": similar_thread.listitems,
              "lists": HandleTMDBMiscResult(response["lists"]["results"]),
              "studios": HandleTMDBMiscResult(response["production_companies"]),
              "releases": HandleTMDBMiscResult(response["releases"]["countries"]),
              "crew": crew_thread.listitems,
              "genres": HandleTMDBMiscResult(response["genres"]),
              "keywords": HandleTMDBMiscResult(response["keywords"]["keywords"]),
              "reviews": HandleTMDBMiscResult(response["reviews"]["results"]),
              "videos": videos,
              "account_states": account_states,
              "images": poster_thread.listitems,
              "backdrops": HandleTMDBPeopleImagesResult(response["images"]["backdrops"])}
    return answer

def GetExtendedSeasonInfo(tmdb_tvshow_id, tvshowname, seasonnumber):
    if not tmdb_tvshow_id:
        response = GetMovieDBData("search/tv?query=%s&language=%s&" % (urllib.quote_plus(tvshowname), addon.getSetting("LanguageID")), 30)
        tmdb_tvshow_id = str(response['results'][0]['id'])
    response = GetMovieDBData("tv/%s/season/%s?append_to_response=videos,images,external_ids,credits&language=%s&include_image_language=en,null,%s&" % (tmdb_tvshow_id, seasonnumber, addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 30)
    # prettyprint(response)
    videos = []
    backdrops = []
    if ("poster_path" in response) and (response["poster_path"]):
        poster_path = base_url + poster_size + response['poster_path']
        poster_path_small = base_url + "w342" + response['poster_path']
    else:
        poster_path = ""
        poster_path_small = ""
    season = {'SeasonDescription': response["overview"],
              'Plot': response["overview"],
              'TVShowTitle': tvshowname,
              'Thumb': poster_path_small,
              'Poster': poster_path,
              'Title': response["name"],
              'ReleaseDate': response["air_date"],
              'AirDate': response["air_date"]}
    if "videos" in response:
        videos = HandleTMDBVideoResult(response["videos"]["results"])
    if "backdrops" in response["images"]:
        backdrops = HandleTMDBPeopleImagesResult(response["images"]["backdrops"])
    answer = {"general": season,
              "actors": HandleTMDBPeopleResult(response["credits"]["cast"]),
              "crew": HandleTMDBPeopleResult(response["credits"]["crew"]),
              "videos": videos,
              "images": HandleTMDBPeopleImagesResult(response["images"]["posters"]),
              "backdrops": backdrops}
    return answer 

def GetExtendedTVShowInfo(tvshow_id):
    response = GetMovieDBData("tv/%s?append_to_response=content_ratings,credits,external_ids,images,keywords,rating,similar,translations,videos&language=%s&include_image_language=en,null,%s&" %
                              (str(tvshow_id), addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 2)
    videos = []
    if "videos" in response:
        videos = HandleTMDBVideoResult(response["videos"]["results"])
    similar_thread = Get_ListItems_Thread(HandleTMDBTVShowResult, response["similar"]["results"])
    actor_thread = Get_ListItems_Thread(HandleTMDBPeopleResult, response["credits"]["cast"])
    crew_thread = Get_ListItems_Thread(HandleTMDBPeopleResult, response["credits"]["crew"])
    poster_thread = Get_ListItems_Thread(HandleTMDBPeopleImagesResult, response["images"]["posters"])
    threads = [similar_thread, actor_thread, crew_thread, poster_thread]
    for item in threads:
        item.start()
    for item in threads:
        item.join()
    answer = {"general": HandleTMDBTVShowResult([response])[0],
              "actors": actor_thread.listitems,
              "similar": similar_thread.listitems,
              "studios": HandleTMDBMiscResult(response["production_companies"]),
              "networks": HandleTMDBMiscResult(response["networks"]),
              "crew": crew_thread.listitems,
              "genres": HandleTMDBMiscResult(response["genres"]),
              "keywords": HandleTMDBMiscResult(response["keywords"]["results"]),
              "videos": videos,
              "seasons": HandleTMDBSeasonResult(response["seasons"]),
              "images": poster_thread.listitems,
              "backdrops": HandleTMDBPeopleImagesResult(response["images"]["backdrops"])}
    return answer

def GetFavItems(media_type):
    session_id = get_session_id()
    account_id = get_account_info()
    response = GetMovieDBData("account/%s/favorite/%s?session_id=%s&language=%s&" % (str(account_id), media_type, str(session_id), addon.getSetting("LanguageID")), 0)
    return HandleTMDBMovieResult(response["results"], False, None)

def GetMovieDBConfig():
    return ("http://image.tmdb.org/t/p/", "w500", "w1280")
    response = GetMovieDBData("configuration?", 60)
    # prettyprint(response)
    if response:
        return (response["images"]["base_url"], response["images"]["poster_sizes"][-2], response["images"]["backdrop_sizes"][-2])
    else:
        return ("", "", "")

def GetMovieDBData(url="", cache_days=14):
    # session_id = get_session_id()
    # url = "http://api.themoviedb.org/3/%sapi_key=%s&session_id=%s" % (url, moviedb_key, session_id)
    url = "http://api.themoviedb.org/3/%sapi_key=%s" % (url, moviedb_key)
    global base_url
    global poster_size
    global fanart_size
    if not base_url:
        log("fetching base_url and size (MovieDB config)")
        base_url = True
        base_url, poster_size, fanart_size = GetMovieDBConfig()
    results = Get_JSON_response(url, cache_days)
    return results

def GetMovieDBID(imdbid):
    response = GetMovieDBData("find/tt%s?external_source=imdb_id&language=%s&" % (imdbid, addon.getSetting("LanguageID")), 30)
    return response["movie_results"][0]["id"]

def GetMovieDBTVShows(tvshowtype):
    response = GetMovieDBData("tv/%s?language=%s&" % (tvshowtype, addon.getSetting("LanguageID")), 2)
    if "results" in response:
        return HandleTMDBTVShowResult(response["results"], False, None)
    else:
        log("No JSON Data available for GetMovieDBTVShows(%s)" % tvshowtype)

def GetMovieDBMovies(movietype):
    response = GetMovieDBData("movie/%s?language=%s&" % (movietype, addon.getSetting("LanguageID")), 2)
    if "results" in response:
        return HandleTMDBMovieResult(response["results"], False, None)
    else:
        log("No JSON Data available for GetMovieDBMovies(%s)" % movietype)

def GetMoviesFromList(list_id):
    response = GetMovieDBData("list/%s?language=%s&" % (str(list_id), addon.getSetting("LanguageID")), 30)
    # prettyprint(response)
    return HandleTMDBMovieResult(response["items"], False, None)

def GetMovieKeywords(movie_id):
    response = GetMovieDBData("movie/%s?append_to_response=account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating&language=%s&" % (movie_id, __addon__.getSetting("LanguageID")), 30)
    response = GetMovieDBData("movie/%s?append_to_response=account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating&include_image_language=en,null,%s&language=%s&" % (movie_id, addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 30)
    keywords = []
    if "keywords" in response:
        for keyword in response["keywords"]["keywords"]:
            newkeyword = {'id': fetch(keyword, 'id'),
                          'name': keyword['name']}
            keywords.append(newkeyword)
        return keywords
    else:
        log("No Keywords in JSON answer")
        return []

def GetMovieLists(Id):
    response = GetMovieDBData("movie/%s?append_to_response=account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating&include_image_language=en,null,%s&language=%s&" % (Id, addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 30)
    return HandleTMDBMiscResult(response["lists"]["results"])

def GetMoviesWithGenre(genreid):
    response = GetMovieDBData("discover/movie?sort_by=release_date.desc&vote_count.gte=10&with_genres=%s&language=%s&" % (str(genreid), addon.getSetting("LanguageID")), 30)
    return HandleTMDBMovieResult(response["results"], False, None)

def GetMoviesWithCertification(country, rating):
    response = GetMovieDBData("discover/movie?sort_by=release_date.desc&vote_count.gte=10&certification_country=%s&certification=%s&language=%s&" % (country, str(rating), addon.getSetting("LanguageID")), 30)
    return HandleTMDBMovieResult(response["results"], False, None)

def GetMoviesWithKeyword(keywordid):
    response = GetMovieDBData("discover/movie?sort_by=release_date.desc&vote_count.gte=10&with_keywords=%s&language=%s&" % (str(keywordid), addon.getSetting("LanguageID")), 30)
    return HandleTMDBMovieResult(response["results"], False, None)

def GetPersonID(person):
    persons = person.split(" / ")
    # if len(persons) > 1:
    #     personlist = []
    #     for item in persons:
    #         personlist.append(item["name"])
    #     dialog = xbmcgui.Dialog()
    #     selection = dialog.select("Select Actor", personlist)
    # else:
    person = persons[0]
    response = GetMovieDBData("search/person?query=%s&include_adult=true&" % urllib.quote_plus(person), 30)
    try:
        return response["results"][0]["id"]
    except:
        log("could not find Person ID")
        return ""

def GetPopularActorList():
    response = GetMovieDBData("person/popular?", 1)
    return HandleTMDBPeopleResult(response["results"])

def GetRatedMovies():
    if addon.getSetting("tmdb_username"):
        session_id = get_session_id()
        account_id = get_account_info()
        response = GetMovieDBData("account/%s/rated/movies?session_id=%s&language=%s&" % (str(account_id), str(session_id), addon.getSetting("LanguageID")), 0)
    else:
        session_id = get_guest_session_id()
        response = GetMovieDBData("guest_session/%s/rated_movies?language=%s&" % (str(session_id), addon.getSetting("LanguageID")), 0)
    return HandleTMDBMovieResult(response["results"], False, None)

def GetSetMovies(set_id):
    response = GetMovieDBData("collection/%s?language=%s&append_to_response=images&include_image_language=en,null,%s&" % (set_id, addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 14)
    if response:
        # prettyprint(response)
        if ("backdrop_path" in response) and (response["backdrop_path"]):
            backdrop_path = base_url + fanart_size + response['backdrop_path']
        else:
            backdrop_path = ""
        if ("poster_path" in response) and (response["poster_path"]):
            poster_path = base_url + poster_size + response['poster_path']
            small_poster_path = base_url + "w342" + response["poster_path"]
        else:
            poster_path = ""
            small_poster_path = ""
        info = {"label": response["name"],
                "Poster": poster_path,
                "Thumb": small_poster_path,
                "Fanart": backdrop_path,
                "overview": response["overview"],
                "overview": response["overview"],
                "ID": response["id"]}
        return HandleTMDBMovieResult(response.get("parts", [])), info
    else:
        log("No JSON Data available")
        return [], {}

def GetSimilarMovies(movie_id):
    response = GetMovieDBData("movie/%s?append_to_response=account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating&include_image_language=en,null,%s&language=%s&" % (movie_id, addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 30)
    if "similar_movies" in response:
        return HandleTMDBMovieResult(response["similar_movies"]["results"])
    else:
        log("No JSON Data available")

def GetTrailer(movieid=None):
    response = GetMovieDBData("movie/%s?append_to_response=account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating&include_image_language=en,null,%s&language=%s&" %
                              (movieid, addon.getSetting("LanguageID"), addon.getSetting("LanguageID")), 30)
    if response and "videos" in response and response['videos']['results']:
        youtube_id = response['videos']['results'][0]['keywords']
        return youtube_id
    Notify("Could not get trailer")
    return ""

def GetTVShowsWithGenre(genre_id):
    response = GetMovieDBData("discover/tv?sort_by=popularity.desc&vote_count.gte=5&with_genres=%s&language=%s&" % (str(genre_id), addon.getSetting("LanguageID")), 30)
    return HandleTMDBTVShowResult(response["results"], False, None)

def GetTVShowsFromNetwork(network_id):
    response = GetMovieDBData("discover/tv?sort_by=popularity.desc&vote_count.gte=5&with_networks=%s&language=%s&" % (str(network_id), addon.getSetting("LanguageID")), 30)
    return HandleTMDBTVShowResult(response["results"], False, None)

def SearchForCompany(Company):
    #Companies = Company.split(" / ")
    #Company = Companies[0]
    import re
    regex = re.compile('\(.+?\)')
    Company = regex.sub('', Company)
    response = GetMovieDBData("search/company?query=%s&" % urllib.quote_plus(Company), 30)
    try:
        return response["results"][0]["id"]
    except:
        log("could not find Company ID")
        return ""

def SearchForSet(setname):
    setname = setname.replace("[", "").replace("]", "").replace("Kollektion", "Collection")
    response = GetMovieDBData("search/collection?query=%s&language=%s&" % (urllib.quote_plus(setname.encode("utf-8")), addon.getSetting("LanguageID")), 14)
    try:
        return response["results"][0]["id"]
    except:
        return ""

def search_movie(medianame, year=''):
    log('TMDB API search criteria: Title[''%s''] | Year[''%s'']' % (medianame, year))
    medianame = urllib.quote_plus(medianame.encode('utf8', 'ignore'))
    response = GetMovieDBData("search/movie?query=%s+%s&language=%s&" % (medianame, year, addon.getSetting("LanguageID")), 1)
    tmdb_id = ''
    try:
        if response == "Empty":
            tmdb_id = ''
        else:
            for item in response['results']:
                if item['id']:
                    tmdb_id = item['id']
                    break
    except Exception as e:
        log(e)
    if tmdb_id == '':
        log('TMDB API search found no ID')
    else:
        log('TMDB API search found ID: %s' % tmdb_id)
    return tmdb_id

def millify(n):
    millnames = [' ', '.000', ' Million', ' Billion', ' Trillion']
    if n and n > 10:
        n = float(n)
        millidx = int(len(str(n)) / 3) - 1
        if millidx == 3:
            return '%.2f%s' % (n / 10 ** (3 * millidx), millnames[millidx])
        else:
            return '%.0f%s' % (n / 10 ** (3 * millidx), millnames[millidx])
    else:
        return ""
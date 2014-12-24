import datetime
from Utils import *

trakt_key = '9d60cea36579a8c95729f0c6dea25953'
base_url = "http://api.trakt.tv/"

def GetTraktCalendarShows(Type):
    shows = []
    results = ""
    url = 'calendar/%s.json/%s/today/14' % (Type, trakt_key)
    try:
        results = Get_JSON_response(base_url + url, 0.5)
    except:
        log("Error when fetching Trakt data from net")
        log("Json Query: " + url)
        results = None
    count = 1
    if results is not None:
        for day in results:
            for episode in day["episodes"]:
                banner = episode["show"]["images"]["banner"]
                fanart = episode["show"]["images"]["fanart"]
                if "banner.jpg" in banner:
                    banner = ""
                if "fanart-dark.jpg" in fanart:
                    fanart = ""
                show = {'Title': episode["episode"]["title"],
                        'TVShowTitle': episode["show"]["title"],
                        'ID': episode["show"]["tvdb_id"],
                        'Runtime': episode["show"]["runtime"],
                        'Duration': episode["show"]["runtime"],
                        'Year': fetch(episode["show"], "year"),
                        'Certification': episode["show"]["certification"],
                        'Studio': episode["show"]["network"],
                        'Plot': episode["show"]["overview"],
                        'Genre': " / ".join(episode["show"]["genres"]),
                        'Thumb': episode["episode"]["images"]["screen"],
                        'Art(poster)': episode["show"]["images"]["poster"],
                        'Poster': episode["show"]["images"]["poster"],
                        'Art(banner)': banner,
                        'Banner': banner,
                        'Art(fanart)': fanart,
                        'Fanart': fanart}
                shows.append(show)
                count += 1
                if count > 20:
                    break
    return shows

def HandleTraktMovieResult(results):
    count = 1
    movies = []
    for movie in results:
        try:
            premiered = str(datetime.datetime.fromtimestamp(int(movie["released"])))[:10]
        except:
            premiered = ""
        if addon.getSetting("infodialog_onclick"):
            path = 'plugin://script.extendedinfo.immersive/?info=extendedinfo&&id=%s' % str(fetch(movie, 'tmdb_id'))
        else:
            path = "plugin://script.extendedinfo.immersive/?info=playtrailer&&id=" + str(fetch(movie, 'tmdb_id'))
        movie = {'Title': movie["title"],
                 'Runtime': movie["runtime"],
                 'Duration': movie["runtime"],
                 'Tagline': movie["tagline"],
                 'Trailer': ConvertYoutubeURL(movie["trailer"]),
                 'Year': movie["year"],
                 'ID': movie["tmdb_id"],
                 'Path': path,
                 'mpaa': movie["certification"],
                 'Plot': movie["overview"],
                 'Premiered': premiered,
                 'Rating': movie["ratings"]["percentage"] / 10.0,
                 'Votes': movie["ratings"]["votes"],
                 'Genre': " / ".join(movie["genres"]),
                 'Art(poster)': movie["images"]["poster"],
                 'Poster': movie["images"]["poster"],
                 'Art(fanart)': movie["images"]["fanart"],
                 'Fanart': movie["images"]["fanart"]}
        movies.append(movie)
        count += 1
        if count > 20:
            break
    return movies

def HandleTraktTVShowResult(results):
    count = 1
    shows = []
    for tvshow in results:
        try:
            premiered = str(datetime.datetime.fromtimestamp(int(tvshow["first_aired"])))[:10]
        except:
            premiered = ""
        banner = tvshow["images"]["banner"]
        fanart = tvshow["images"]["fanart"]
        if "banner.jpg" in banner:
            banner = ""
        if "fanart-dark.jpg" in fanart:
            fanart = ""
        show = {'Title': tvshow["title"],
                'Label': tvshow["title"],
                'TVShowTitle': tvshow["title"],
                'Runtime': tvshow["runtime"],
                'Duration': tvshow["runtime"],
                'Year': tvshow["year"],
                'Status': fetch(tvshow, "status"),
                'mpaa': tvshow["certification"],
                'Studio': tvshow["network"],
                'Plot': tvshow["overview"],
                'ID': tvshow["tvdb_id"],
                'IMDB_ID': tvshow["imdb_id"],
                'Path': 'plugin://script.extendedinfo.immersive/?info=extendedtvinfo&&imdbid=%s' % tvshow["imdb_id"],
                'AirDay': tvshow["air_day"],
                'AirShortTime': tvshow["air_time"],
                'Label2': tvshow["air_day"] + " " + tvshow["air_time"],
                'Premiered': premiered,
                'Country': tvshow["country"],
                'Rating': tvshow["ratings"]["percentage"] / 10.0,
                'Votes': tvshow["ratings"]["votes"],
                'Watchers': fetch(tvshow, "watchers"),
                'Genre': " / ".join(tvshow["genres"]),
                'Art(poster)': tvshow["images"]["poster"],
                'Poster': tvshow["images"]["poster"],
                'Art(banner)': banner,
                'Banner': banner,
                'Art(fanart)': fanart,
                'Fanart': fanart,
                'Thumb': tvshow["images"]["fanart"]}
        shows.append(show)
        count += 1
        if count > 20:
            break
    return shows
	
def HandleTraktCommentsResult(results):
    count = 1
    comments = []
    for comment in results:
        try:
            comment = {'Text': comment["text"],
                    'Type': comment["type"],
                    'Spoiler': comment["spoiler"],
                    'Likes': comment["likes"],
                    'Username': comment["user"]["username"],
                    'Avatar': comment["user"]["avatar"],
                    'Fullname': comment["user"]["full_name"],
                    'Gender': comment["user"]["gender"],
                    'Age': comment["user"]["age"],  
                    'Location': comment["user"]["location"]  }
            comments.append(comment)
        except Exception,e:
            log(e)          
        count += 1
        if count > 20:
            break
    return comments

def GetTrendingShows():
    url = 'shows/trending.json/%s' % trakt_key
    results = Get_JSON_response(base_url + url)
    if results is not None:
        return HandleTraktTVShowResult(results)

def GetTVShowInfo(id):
    url = 'show/summary.json/%s/%s' % (trakt_key, id)
    results = Get_JSON_response(base_url + url)
    if results is not None:
        return HandleTraktTVShowResult([results])

def GetTrendingMovies():
    url = 'movies/trending.json/%s' % trakt_key
    results = Get_JSON_response(base_url + url)
    if results is not None:
        return HandleTraktMovieResult(results)

def GetSimilarTrakt(mediatype, imdb_id):
    if imdb_id is not None:
        url = '%s/related.json/%s/%s/' % (mediatype, trakt_key, imdb_id)
        results = Get_JSON_response(base_url + url)
        if results is not None:
            if mediatype == "show":
                return HandleTraktTVShowResult(results)
            elif mediatype == "episode":
                return HandleTraktTVShowResult(results)
            elif mediatype == "movie":
                return HandleTraktMovieResult(results)
    else:
        Notify("Error when fetching info from Trakt.TV")
        return[]
		
def GetCommentsTrakt(mediatype,imdb_id):
    if imdb_id is not None:
        url = '%s/comments.json/%s/%s/' % (mediatype, trakt_key, imdb_id)
        results = Get_JSON_response(base_url + url)
        if results is not None:
            return HandleTraktCommentsResult(results)
    else:
        Notify("Error when fetching info from Trakt.TV")
        return[]
    
def GetEpisodeCommentsTrakt(slug,season,episode):
    try:
        url = 'show/episode/comments.json/%s/%s/%s/%s' % (trakt_key, slug, season, episode)
        results = Get_JSON_response(base_url + url)
        if results is not None:
            return HandleTraktCommentsResult(results)
    except:
        Notify("Error when fetching info from Trakt.TV")
        return[]
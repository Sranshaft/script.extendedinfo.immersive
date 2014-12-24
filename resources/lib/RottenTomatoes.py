from Utils import *

rottentomatoes_key = '63sbsudx936yedd2wdmt6tkn'
base_url = "http://api.rottentomatoes.com/api/public/v1.0/lists/"


def GetRottenTomatoesMovies(movietype):
    movies = []
    try:
        url = movietype + '.json?apikey=%s' % (rottentomatoes_key)
        results = Get_JSON_response(base_url + url)
    except:
        results = None
        Notify("Error when fetching RottenTomatoes data from net")
    count = 1
    if results is not None:
        for item in results["movies"]:
            if "alternate_ids" in item:
                imdbid = str(item["alternate_ids"]["imdb"])
            else:
                imdbid = ""
            poster = item["posters"]["original"].replace("tmb", "ori")
            movie = {'Title': item["title"],
                     'Art(poster)': item["posters"]["original"],
                     'imdbid': imdbid,
                     'Thumb': poster,
                     'Poster': poster,
                     'Runtime': item["runtime"],
                     'Duration': item["runtime"],
                     'Year': item["year"],
                     'path': "plugin://script.extendedinfo.immersive/?info=playtrailer&&imdbid=" + imdbid,
                     'Premiered': item["release_dates"]["theater"],
                     'mpaa': item["mpaa_rating"],
                     'Rating': item["ratings"]["audience_score"] / 10.0,
                     'Plot': item["synopsis"]}
            if imdbid:
                movies.append(movie)
            count += 1
            if count > 20:
                break
    return movies

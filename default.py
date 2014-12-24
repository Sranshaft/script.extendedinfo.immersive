import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import urlparse
import urllib

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_strings = addon.getLocalizedString
addon_path = addon.getAddonInfo('path').decode("utf-8")
addon_libs = xbmc.translatePath(os.path.join(addon_path, 'resources', 'lib')).decode("utf-8")
sys.path.append(addon_libs)

from LastFM import *
from MiscScraper import *
from TheAudioDB import *
from TheMovieDB import *
from Utils import *
from RottenTomatoes import *
from YouTube import *
from Trakt import *

homewindow = xbmcgui.Window(10000)
Addon_Data_Path = os.path.join(xbmc.translatePath("special://profile/addon_data/%s" % addon_id).decode("utf-8"))
Skin_Data_Path = os.path.join(xbmc.translatePath("special://profile/addon_data/%s" % xbmc.getSkinDir()).decode("utf-8"))

class Main:

    def __init__(self):
        log("version %s started" % addon_version)
        xbmc.executebuiltin('SetProperty(extendedinfo_running,True,home)')
        self._init_vars()
        self._parse_argv()
        # run in backend if parameter was set
        if self.infos:
            self._StartInfoActions()
        if self.control == "plugin":
            xbmcplugin.endOfDirectory(self.handle)
        xbmc.executebuiltin('ClearProperty(extendedinfo_running,home)')

    def _init_vars(self):
        self.window = xbmcgui.Window(10000)  # Home Window
        self.control = None
        self.cleared = False
        self.musicvideos = []
        self.movies = []
        self.infos = []
        self.AlbumName = None
        self.ArtistName = None
        self.TrackName = None
        self.UserName = None
        self.feed = None
        self.id = None
        self.dbid = None
        self.imdbid = None
        self.setid = None
        self.type = False
        self.hd = ""
        self.orderby = "relevance"
        self.time = "all_time"
        self.director = ""
        self.tag = ""
        self.name = ""
        self.path = ""
        self.tvshow = ""
        self.season = ""
        self.episode = ""
        self.writer = ""
        self.studio = ""
        self.lat = ""
        self.lon = ""
        self.infodialog = False
        self.limit = False
        self.location = ""
        self.distance = ""
        self.handle = None
        self.festivalsonly = False
        self.prop_prefix = ""
        self.Artist_mbid = None
        self.pluginmode = False

    def _parse_argv(self):
        if sys.argv[0] == 'plugin://script.extendedinfo.immersive/':
            self.pluginmode = True
            args = sys.argv[2][1:].split("&&")
            self.handle = int(sys.argv[1])
            self.control = "plugin"
            params = {}
        else:
            args = sys.argv
            try:
                params = dict(arg.split("=") for arg in sys.argv[1].split("&"))
            except:
                params = {}
        for arg in args:
            if arg == 'script.extendedinfo.immersive':
                continue
            param = arg.replace('"', '').replace("'", " ")
            log(param)
            if param.startswith('info='):
                self.infos.append(param[5:])
            elif param.startswith('type='):
                self.type = param[5:]
            elif param.startswith('tag='):
                self.tag = param[4:]
            elif param.startswith('studio='):
                self.studio = param[7:]
            elif param.startswith('orderby='):
                self.orderby = param[8:]
            elif param.startswith('time='):
                self.time = param[5:]
            elif param.startswith('director='):
                self.director = param[9:]
            elif param.startswith('writer='):
                self.writer = param[7:]
            elif param.startswith('lat='):
                self.lat = param[4:]
            elif param.startswith('lon='):
                self.lon = param[4:]
            elif param.startswith('location='):
                self.location = param[9:]
            elif param.startswith('distance='):
                self.distance = param[9:]
            elif param.startswith('festivalsonly='):
                self.festivalsonly = param[14:]
            elif param.startswith('feed='):
                self.feed = param[5:]
            elif param.startswith('name='):
                self.name = param[5:]
            elif param.startswith('path='):
                self.path = param[5:]
            elif param.startswith('id='):
                self.id = param[3:]
            elif param.startswith('infodialog='):
                if param[11:].lower() == "true":
                    self.infodialog = True
            elif param.startswith('dbid='):
                self.dbid = param[5:]
            elif param.startswith('imdbid='):
                self.imdbid = param[7:]
            elif param.startswith('setid='):
                self.setid = param[6:]
            elif param.startswith('hd='):
                self.hd = param[3:]
            elif param.startswith('tvshow='):
                self.tvshow = param[7:]
            elif param.startswith('season='):
                self.season = param[7:]
            elif param.startswith('episode='):
                self.episode = param[8:]
            elif param.startswith('prefix='):
                self.prop_prefix = param[7:]
                if (not self.prop_prefix.endswith('.')) and (self.prop_prefix is not ""):
                    self.prop_prefix = self.prop_prefix + '.'
            elif param.startswith('artistname='):
                self.ArtistName = arg[11:].split(" feat. ")[0].strip()
                if self.ArtistName:
                    # todo: look up local mbid first -->xbmcid for parameter
                    self.Artist_mbid = GetMusicBrainzIdFromNet(self.ArtistName)
            elif param.startswith('albumname='):
                self.AlbumName = arg[10:].strip()
            elif param.startswith('trackname='):
                self.TrackName = arg[10:].strip()
            elif param.startswith('username='):
                self.UserName = arg[9:].strip()
            elif param.startswith('limit='):
                self.limit = int(arg[6:])
            elif param.startswith('window='):
                if arg[7:] == "currentdialog":
                    xbmc.sleep(300)
                    self.window = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
                elif arg[7:] == "current":
                    xbmc.sleep(300)
                    self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
                else:
                    self.window = xbmcgui.Window(int(arg[7:]))
            elif param.startswith('control='):
                self.control = int(arg[8:])

    def _StartInfoActions(self):
        for info in self.infos:

            # IMAGES #

            if info == 'xkcd':
                passListToSkin('XKCD', GetXKCDInfo(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'flickr':
                passListToSkin('Flickr', GetFlickrImages(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'cyanide':
                passListToSkin('CyanideHappiness', GetCandHInfo(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'dailybabes':
                passListToSkin('DailyBabes', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('DailyBabes', GetDailyBabes(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'dailybabe':
                passListToSkin('DailyBabe', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('DailyBabe', GetDailyBabes(single=True), self.prop_prefix, self.window, self.control, self.handle, self.limit)

            # AUDIODB #
			
            elif info == 'discography':
                passListToSkin('Discography', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                Discography = GetDiscography(self.ArtistName)
                if len(Discography) == 0:
                    Discography = GetArtistTopAlbums(self.Artist_mbid)
                passListToSkin('Discography', Discography, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'mostlovedtracks':
                passListToSkin('MostLovedTracks', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('MostLovedTracks', GetMostLovedTracks(self.ArtistName), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'artistdetails':
                passListToSkin('Discography', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('MusicVideos', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                ArtistDetails = GetArtistDetails(self.ArtistName)
                if "audiodbid" in ArtistDetails:
                    MusicVideos = GetMusicVideos(ArtistDetails["audiodbid"])
                    passListToSkin('MusicVideos', MusicVideos, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('Discography', GetDiscography(self.ArtistName), self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passDictToSkin(ArtistDetails, self.prop_prefix)
            elif info == 'albuminfo':
                if self.id:
                    AlbumDetails = GetAlbumDetails(self.id)
                    Trackinfo = GetTrackDetails(self.id)
                    passDictToSkin(AlbumDetails, self.prop_prefix)
                    passListToSkin('Trackinfo', Trackinfo, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'albumshouts':
                passListToSkin('Shout', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.ArtistName and self.AlbumName:
                    passListToSkin('Shout', GetAlbumShouts(self.ArtistName, self.AlbumName), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'artistshouts':
                passListToSkin('Shout', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.ArtistName:
                    passListToSkin('Shout', GetArtistShouts(self.ArtistName), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'topartists':
                passListToSkin('TopArtists', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('TopArtists', GetTopArtists(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'hypedartists':
                passListToSkin('HypedArtists', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('HypedArtists', GetHypedArtists(), self.prop_prefix, self.window, self.control, self.handle, self.limit)

            # LAST.FM #

            elif info == 'artistevents':
                passListToSkin('ArtistEvents', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.Artist_mbid:
                    passListToSkin('ArtistEvents', GetEvents(self.Artist_mbid), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'nearevents':
                passListToSkin('NearEvents', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('NearEvents', GetNearEvents(self.tag, self.festivalsonly, self.lat, self.lon, self.location, self.distance), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'venueevents':
                passListToSkin('VenueEvents', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.location:
                    self.id = GetVenueID(self.location)
                if self.id:
                    passListToSkin('VenueEvents', GetVenueEvents(self.id), self.prop_prefix, self.window, self.control, self.handle, self.limit)
                else:
                    Notify("Error", "Could not find venue")
            elif info == 'topartistsnearevents':
                passListToSkin('TopArtistsNearEvents', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                artists = GetXBMCArtists()
                events = GetArtistNearEvents(artists["result"]["artists"][0:49])
                passListToSkin('TopArtistsNearEvents', events, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'trackinfo':
                homewindow.setProperty('%sSummary' % self.prop_prefix, "")  # set properties
                if self.ArtistName and self.TrackName:
                    TrackInfo = GetTrackInfo(self.ArtistName, self.TrackName)
                    homewindow.setProperty('%sSummary' % self.prop_prefix, TrackInfo["summary"])  # set properties
            elif info == 'similarartists':
                passListToSkin('SimilarArtists', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.Artist_mbid:
                    passListToSkin('SimilarArtists', GetSimilarById(self.Artist_mbid), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'similarartistsinlibrary':
                passListToSkin('SimilarArtists', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.Artist_mbid:
                    passListToSkin('SimilarArtists', GetSimilarArtistsInLibrary(self.Artist_mbid), self.prop_prefix, self.window, self.control, self.handle, self.limit)

            # ROTTEN TOMATOES #

            elif info == 'intheaters':
                passListToSkin('InTheatersMovies', GetRottenTomatoesMovies("movies/in_theaters"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'boxoffice':
                passListToSkin('BoxOffice', GetRottenTomatoesMovies("movies/box_office"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'opening':
                passListToSkin('Opening', GetRottenTomatoesMovies("movies/opening"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'comingsoon':
                passListToSkin('ComingSoonMovies', GetRottenTomatoesMovies("movies/upcoming"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'toprentals':
                passListToSkin('TopRentals', GetRottenTomatoesMovies("dvds/top_rentals"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'currentdvdreleases':
                passListToSkin('CurrentDVDs', GetRottenTomatoesMovies("dvds/current_releases"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'newdvdreleases':
                passListToSkin('NewDVDs', GetRottenTomatoesMovies("dvds/new_releases"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'upcomingdvds':
                passListToSkin('UpcomingDVDs', GetRottenTomatoesMovies("dvds/upcoming"), self.prop_prefix, self.window, self.control, self.handle, self.limit)

            # THE MOVIEDB #

            elif info == 'incinemas':
                passListToSkin('InCinemasMovies', GetMovieDBMovies("now_playing"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'upcoming':
                passListToSkin('UpcomingMovies', GetMovieDBMovies("upcoming"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'topratedmovies':
                passListToSkin('TopRatedMovies', GetMovieDBMovies("top_rated"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'popularmovies':
                passListToSkin('PopularMovies', GetMovieDBMovies("popular"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'airingtodaytvshows':
                passListToSkin('AiringTodayTVShows', GetMovieDBTVShows("airing_today"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'onairtvshows':
                passListToSkin('OnAirTVShows', GetMovieDBTVShows("on_the_air"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'topratedtvshows':
                passListToSkin('TopRatedTVShows', GetMovieDBTVShows("top_rated"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'populartvshows':
                passListToSkin('PopularTVShows', GetMovieDBTVShows("popular"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'similarmovies':
                passListToSkin('SimilarMovies', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.id:
                    MovieId = self.id
                elif self.dbid and (int(self.dbid) > -1):
                    MovieId = GetImdbIDFromDatabase("movie", self.dbid)
                    log("IMDBId from local DB:" + str(MovieId))
                else:
                    MovieId = ""
                if MovieId:
                    passListToSkin('SimilarMovies', GetSimilarMovies(MovieId), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'studio':
                passListToSkin('StudioInfo', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.studio:
                    CompanyId = SearchforCompany(self.studio)
                    passListToSkin('StudioInfo', GetCompanyInfo(CompanyId), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'set':
                passListToSkin('MovieSetItems', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.dbid and not "show" in str(self.type):
                    name = GetMovieSetName(self.dbid)
                    if name:
                        self.setid = SearchForSet(name)
                if self.setid:
                    SetData, info = GetSetMovies(self.setid)
                    if SetData:
                        passListToSkin('MovieSetItems', SetData, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'movielists':
                passListToSkin('MovieLists', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.dbid:
                    movieid = GetImdbIDFromDatabase("movie", self.dbid)
                    log("MovieDB Id:" + str(movieid))
                    if movieid:
                        passListToSkin('MovieLists', GetMovieLists(movieid), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'keywords':
                passListToSkin('Keywords', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.dbid:
                    movieid = GetImdbIDFromDatabase("movie", self.dbid)
                    log("MovieDB Id:" + str(movieid))
                    if movieid:
                        passListToSkin('Keywords', GetMovieKeywords(movieid), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'popularpeople':
                passListToSkin('PopularPeople', GetPopularActorList(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'directormovies':
                passListToSkin('DirectorMovies', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.director:
                    directorid = GetPersonID(self.director)
                    if directorid:
                        passListToSkin('DirectorMovies', GetDirectorMovies(directorid), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'writermovies':
                passListToSkin('WriterMovies', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.writer and not self.writer.split(" / ")[0] == self.director.split(" / ")[0]:
                    writerid = GetPersonID(self.writer)
                    if writerid:
                        passListToSkin('WriterMovies', GetDirectorMovies(writerid), self.prop_prefix, self.window, self.control, self.handle, self.limit)

            # TRAKT.TV #

            elif info == 'similar':
                passListToSkin('SimilarTrakt', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                log("starting GetSimilarTrakt")
                if (self.id or self.dbid):
                    if self.dbid:
                        if self.type == "movie":
                            id = GetImdbIDFromDatabase("movie", self.dbid)
                        elif self.type == "show":
                            id = GetImdbIDFromDatabase("tvshow", self.dbid)
                        elif self.type == "episode":
                            id = GetImdbIDFromDatabasefromEpisode(self.dbid)
                    else:
                        id = self.id
                    passListToSkin('SimilarTrakt', GetSimilarTrakt(self.type, id), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'comments':
                passListToSkin('CommentsTrakt', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                log("starting GetCommentsTrakt")
                if (self.id or self.dbid):
                    if self.dbid:
                        if self.type == "movie":
                            id = GetImdbIDFromDatabase("movie", self.dbid)
                        else:
                            id = GetImdbIDFromDatabase("tvshow", self.dbid)
                    else:
                        id = self.id
                    if id == "":
                        log("Comments.ID: None")
                    else:						
                        passListToSkin('CommentsTrakt', GetCommentsTrakt(self.type,id), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'episodecomments':
                passListToSkin('EpisodeCommentsTrakt', None, self.prop_prefix)
                log("starting GetEpisodeCommentsTrakt")
                if self.type and self.tvshow and self.season and self.episode:
                    slug = ""
                    slug = self.tvshow.rstrip(" ").replace(" ", "-")
                    slug = slug.rstrip(" ").replace("(", "")
                    slug = slug.rstrip(" ").replace(")", "")
                    slug = slug.rstrip(" ").replace("!", "")
                    passListToSkin('EpisodeCommentsTrakt', GetEpisodeCommentsTrakt(slug,self.season,self.episode), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'airingshows':
                passListToSkin('AiringShows', GetTraktCalendarShows("shows"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'premiereshows':
                passListToSkin('PremiereShows', GetTraktCalendarShows("premieres"), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'trendingshows':
                passListToSkin('TrendingShows', GetTrendingShows(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'trendingmovies':
                passListToSkin('TrendingMovies', GetTrendingMovies(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            
            # YOUTUBE #

            elif info == 'youtubesearch':
                homewindow.setProperty('%sSearchValue' % self.prop_prefix, self.id)  # set properties
                passListToSkin('YoutubeSearch', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.id:
                    passListToSkin('YoutubeSearch', GetYoutubeSearchVideosV3(self.id, self.hd, self.orderby), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'youtubeplaylist':
                passListToSkin('YoutubePlaylist', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.id:
                    passListToSkin('YoutubePlaylist', GetYoutubePlaylistVideos(self.id), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'youtubeusersearch':
                passListToSkin('YoutubeUserSearch', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.id:
                    passListToSkin('YoutubeUserSearch', GetYoutubeUserVideos(self.id), self.prop_prefix, self.window, self.control, self.handle, self.limit)

            # UTILITIES #

            elif info == 'channels':
                channels = create_channel_list()
                # prettyprint(channels)
            elif info == 'favourites':
                if self.id:
                    favourites = GetFavouriteswithType(self.id)
                else:
                    favourites = GetFavourites()
                    homewindow.setProperty('favourite.count', str(len(favourites)))
                    if len(favourites) > 0:
                        homewindow.setProperty('favourite.1.name', favourites[-1]["Label"])
                passListToSkin('Favourites', favourites, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'json':
                passListToSkin('RSS', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                videos = GetYoutubeVideos(self.feed, self.prop_prefix)
                passListToSkin('RSS', videos, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'similarlocal' and self.dbid:
                passListToSkin('SimilarLocalMovies', None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                passListToSkin('SimilarLocalMovies', GetSimilarMoviesInLibrary(self.dbid), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'iconpanel':
                passListToSkin('IconPanel', GetIconPanel(1), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'weather':
                passListToSkin('WeatherImages', GetWeatherImages(), self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'updatexbmcdatabasewithartistmbidbg':
                SetMusicBrainzIDsForAllArtists(False, False)
            elif info == 'setfocus':
                self.control = ""  # workaround to avoid breaking PlayMedia
                xbmc.executebuiltin("SetFocus(22222)")
            elif info == 'playliststats':
                GetPlaylistStats(self.id)
            elif info == "sortletters":
                listitems = GetSortLetters(self.path, self.id)
                passListToSkin('SortLetters', listitems, self.prop_prefix, self.window, self.control, self.handle, self.limit)
            elif info == 'slideshow':
                windowid = xbmcgui.getCurrentWindowId()
                Window = xbmcgui.Window(windowid)
                focusid = Window.getFocusId()
                itemlist = Window.getFocus()
                numitems = itemlist.getSelectedPosition()
                log("items:" + str(numitems))
                for i in range(0, numitems):
                    Notify(item.getProperty("Image"))
            elif info == 'action':
                xbmc.executebuiltin(self.id)
            elif info == "youtubevideo":
                if self.id:
                    PlayTrailer(self.id)
                    self.control = ""  # workaround to avoid breaking PlayMedia
            elif info == 'playtrailer':
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                xbmc.sleep(500)
                if self.id:
                    MovieId = self.id
                elif self.dbid and (int(self.dbid) > -1):
                    MovieId = GetImdbIDFromDatabase("movie", self.dbid)
                    log("MovieDBID from local DB:" + str(MovieId))
                elif self.imdbid:
                    MovieId = GetMovieDBID(self.imdbid)
                else:
                    MovieId = ""
                if MovieId:
                    trailer = GetTrailer(MovieId)
                    xbmc.executebuiltin("Dialog.Close(busydialog)")
                    if trailer:
                        PlayTrailer(trailer)
                        self.control = ""  # workaround to avoid breaking PlayMedia
                    else:
                        Notify("Error", "No Trailer available")
            elif info == 'updatexbmcdatabasewithartistmbid':
                SetMusicBrainzIDsForAllArtists(True, False)

            # WINDOWS #

            elif info == 'extendedinfo':
                from DialogVideoInfo import DialogVideoInfo
                if self.handle:
                    xbmcplugin.endOfDirectory(self.handle)
                dialog = DialogVideoInfo(u'%s-DialogVideoInfo.xml' % addon_id, addon_path, id=self.id, dbid=self.dbid, imdbid=self.imdbid, name=self.name)
                dialog.doModal()
            elif info == 'extendedactorinfo':
                from DialogActorInfo import DialogActorInfo
                log('Looking for window: %s-DialogInfo.xml' % (addon_id))
                dialog = DialogActorInfo(u'%s-DialogInfo.xml' % addon_id, addon_path, id=self.id, name=self.name)
                dialog.doModal()
            elif info == 'extendedtvinfo':
                from DialogTVShowInfo import DialogTVShowInfo
                if self.handle:
                    xbmcplugin.endOfDirectory(self.handle)
                dialog = DialogTVShowInfo(u'%s-DialogVideoInfo.xml' % addon_id, addon_path, id=self.id, dbid=self.dbid, imdbid=self.imdbid, name=self.name)
                dialog.doModal()
            elif info == 'extendedseasoninfo':
                passListToSkin("SeasonVideos", None, self.prop_prefix, self.window, self.control, self.handle, self.limit)
                if self.tvshow and self.season:
                    from DialogSeasonInfo import DialogSeasonInfo
                    dialog = DialogSeasonInfo(u'%s-DialogVideoInfo.xml' % addon_name, addon_path, tvshow=self.tvshow, season=self.season)
                    dialog.doModal()

if (__name__ == "__main__"):
    Main()
log('finished')

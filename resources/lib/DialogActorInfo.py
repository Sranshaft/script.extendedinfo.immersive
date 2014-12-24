import xbmc
import xbmcaddon
import xbmcgui
from Utils import *
from TheMovieDB import *
from YouTube import *
import DialogVideoInfo
import DialogTVShowInfo
homewindow = xbmcgui.Window(10000)

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_strings = addon.getLocalizedString
addon_path = addon.getAddonInfo('path').decode("utf-8")


class DialogActorInfo(xbmcgui.WindowXMLDialog):
    ACTION_PREVIOUS_MENU = [92, 9]
    ACTION_EXIT_SCRIPT = [13, 10]

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.movieplayer = VideoPlayer(popstack=True)
        self.id = kwargs.get('id')
        if not self.id:
            name = kwargs.get('name')
            name = name.decode("utf-8")
            name = name.split(xbmc.getLocalizedString(20347))
            name = name[0].strip().encode("utf-8")
            names = name.split(" / ")
            if len(names) > 1:
                Dialog = xbmcgui.Dialog()
                ret = Dialog.select("Actor Info", names)
                if ret == -1:
                    return False
                name = names[ret]
            self.id = GetPersonID(name)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        self.person = None
        self.movie_roles = None
        self.tvshow_roles = None
        self.images = None
        if self.id:
            self.person = GetExtendedActorInfo(self.id)
            db_movies = 0
            for item in self.person["movie_roles"]:
                if "DBID" in item:
                    db_movies += 1
            self.person["general"]["DBMovies"] = str(db_movies)
            self.person["general"]["TotalMovies"] = str(len(self.person["movie_roles"]))
            self.youtube_vids = GetYoutubeSearchVideosV3(self.person["general"]["name"],limit="25")
        else:
            Notify("No ID found")
            self.close()
        xbmc.executebuiltin("Dialog.Close(busydialog)")

    def onInit(self):
        windowid = xbmcgui.getCurrentWindowDialogId()
        passDictToSkin(self.person["general"], "actor.", False, False, windowid)
        self.getControl(150).addItems(CreateListItems(self.person["movie_roles"], 0))
        self.getControl(250).addItems(CreateListItems(self.person["tvshow_roles"], 0))
        self.getControl(350).addItems(CreateListItems(self.youtube_vids, 0))
        self.getControl(450).addItems(CreateListItems(self.person["images"], 0))
        self.getControl(550).addItems(CreateListItems(self.person["movie_crew_roles"], 0))
        self.getControl(650).addItems(CreateListItems(self.person["tvshow_crew_roles"], 0))
        self.getControl(750).addItems(CreateListItems(self.person["tagged_images"], 0))
        # self.getControl(150).addItems(tvshow_listitems)

    def setControls(self):
        pass

    def onAction(self, action):
        if action in self.ACTION_PREVIOUS_MENU:
            self.close()
            PopWindowStack()
        elif action in self.ACTION_EXIT_SCRIPT:
            self.close()

    def onClick(self, controlID):
        if controlID == 132:
            text = self.person["general"]["description"] + "[CR]" + self.person["general"]["biography"]
            w = TextViewer_Dialog('DialogTextViewer.xml', addon_path, header="Overview", text=text)
            w.doModal()
        elif controlID in [150, 550]:
            listitem = self.getControl(controlID).getSelectedItem()
            AddToWindowStack(self)
            dialog = DialogVideoInfo.DialogVideoInfo(u'%s-DialogVideoInfo.xml' % addon_id, addon_path, id=listitem.getProperty("id"), dbid=listitem.getProperty("dbid"))
            self.close()
            dialog.doModal()
        elif controlID in [250, 650]:
            listitem = self.getControl(controlID).getSelectedItem()
            options = ["Show actor TV Show appearances", "Show TV Show Info"]
            selection = xbmcgui.Dialog().select("Choose Option", options)
            if selection == 0:
                GetCreditInfo(listitem.getProperty("credit_id"))
            if selection == 1:
                AddToWindowStack(self)
                dialog = DialogTVShowInfo.DialogTVShowInfo(u'%s-DialogVideoInfo.xml' % addon_id, addon_path, id=listitem.getProperty("id"), dbid=listitem.getProperty("dbid"))
                self.close()
                dialog.doModal()
        elif controlID == 350:
            listitem = self.getControl(controlID).getSelectedItem()
            AddToWindowStack(self)
            self.close()
            self.movieplayer.playYoutubeVideo(listitem.getProperty("youtube_id"), listitem, True)
            self.movieplayer.WaitForVideoEnd()
            PopWindowStack()
        elif controlID in [450, 750]:
            image = self.getControl(controlID).getSelectedItem().getProperty("Poster")
            dialog = SlideShow(u'%s-SlideShow.xml' % addon_id, addon_path, image=image)
            dialog.doModal()

    def onFocus(self, controlID):
        pass

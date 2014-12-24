import xbmc
import xbmcaddon
import xbmcgui
from Utils import *
from TheMovieDB import *
from YouTube import *
import DialogActorInfo
import DialogVideoList
homewindow = xbmcgui.Window(10000)

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_strings = addon.getLocalizedString
addon_path = addon.getAddonInfo('path').decode("utf-8")


class DialogSeasonInfo(xbmcgui.WindowXMLDialog):
    ACTION_PREVIOUS_MENU = [92, 9]
    ACTION_EXIT_SCRIPT = [13, 10]

    def __init__(self, *args, **kwargs):
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        xbmcgui.WindowXMLDialog.__init__(self)
        self.tmdb_id = kwargs.get('id')
        self.season = kwargs.get('season')
        self.showname = kwargs.get('tvshow')
        self.logged_in = checkLogin()
        prettyprint(kwargs)
        if self.tmdb_id or (self.season and self.showname):
            self.season = GetExtendedSeasonInfo(self.tmdb_id, self.showname, self.season)
            if not self.season:
                self.close()
            search_string = "%s %s tv" % (self.season["general"]["TVShowTitle"], self.season["general"]["Title"])
            self.youtube_vids = GetYoutubeSearchVideosV3(search_string, "", "relevance", 15)
        else:
            Notify("No ID found")
            self.close()
        xbmc.executebuiltin("Dialog.Close(busydialog)")

    def onInit(self):
        windowid = xbmcgui.getCurrentWindowDialogId()
        xbmcgui.Window(windowid).setProperty("tmdb_logged_in", self.logged_in)
        passDictToSkin(self.season["general"], "movie.", False, False, windowid)
        self.getControl(50).addItems(CreateListItems(self.season["actors"], 0))
        self.getControl(350).addItems(CreateListItems(self.youtube_vids, 0))
        self.getControl(750).addItems(CreateListItems(self.season["crew"], 0))
        self.getControl(1150).addItems(CreateListItems(self.season["videos"], 0))
        self.getControl(1250).addItems(CreateListItems(self.season["images"], 0))
        self.getControl(1350).addItems(CreateListItems(self.season["backdrops"], 0))

    def onAction(self, action):
        if action in self.ACTION_PREVIOUS_MENU:
            self.close()
            PopWindowStack()
        elif action in self.ACTION_EXIT_SCRIPT:
            self.close()

    def onClick(self, controlID):
        if controlID in [50, 750]:
            actorid = self.getControl(controlID).getSelectedItem().getProperty("id")
            AddToWindowStack(self)
            dialog = DialogActorInfo.DialogActorInfo(u'%s-DialogInfo.xml' % addon_id, addon_path, id=actorid)
            self.close()
            dialog.doModal()
        elif controlID in [350, 1150]:
            listitem = self.getControl(controlID).getSelectedItem()
            AddToWindowStack(self)
            self.close()
            PlayTrailer(listitem.getProperty("youtube_id"))
            WaitForVideoEnd()
            PopWindowStack()
        elif controlID in [1250, 1350]:
            image = self.getControl(controlID).getSelectedItem().getProperty("Poster")
            dialog = SlideShow(u'%s-SlideShow.xml' % addon_id, addon_path, image=image)
            dialog.doModal()
        elif controlID == 132:
            w = TextViewer_Dialog('DialogTextViewer.xml', addon_path, header="Overview", text=self.season["general"]["Plot"])
            w.doModal()


    def onFocus(self, controlID):
        pass

    def OpenVideoList(self, listitems):
        AddToWindowStack(self)
        self.close()
        dialog = DialogVideoList.DialogVideoList(u'%s-VideoList.xml' % addon_id, addon_path, listitems=listitems)
        dialog.doModal()


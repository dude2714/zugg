# -*- coding: utf-8 -*-

"""
    Exodus Add-on
    ///Updated for ThePromise///

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import sys,re,random,datetime,time
import importlib
import simplejson as json

import six
from six.moves import urllib_parse, zip, reduce

from resources.lib.modules import trakt
from resources.lib.modules import tvmaze
from resources.lib.modules import cache
from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import debrid
from resources.lib.modules import workers
from resources.lib.modules import source_utils
from resources.lib.modules import log_utils
#from resources.lib.modules import thexem

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

try: import resolveurl
except: pass

log_utils.log('TPDBG sources.py loaded (popup counters build)', 1)

from kodi_six import xbmc


class sources:
    def __init__(self):
        self.getConstants()
        self.sources = []
        self.f_out_sources = []
        self.content = None
        self.unfiltered = False
        self.duration = ''


    def play(self, title, year, imdb, tmdb, season, episode, tvshowtitle, premiered, meta, select, unfiltered):
        try:
            self.content = 'episode' if tvshowtitle else 'movie'
            self.unfiltered = unfiltered

            url = None

            #log_utils.log('meta: ' + repr(meta))

            try: meta = json.loads(meta)
            except: meta = {}

            if not meta: # played through library
                try:
                    if self.content == 'episode':
                        meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "year", "thumbnail", "file", "runtime"]}, "id": 1}' % (year, str(int(year)+1), str(int(year)-1)))
                        meta = six.ensure_text(meta, errors='ignore')
                        meta = json.loads(meta)['result']['tvshows']
                        #log_utils.log('meta0: ' + repr(meta))

                        t = self.getTitle(tvshowtitle)
                        meta = [i for i in meta if year == str(i['year']) and t == self.getTitle(i['title'])][0]

                        tvshowid = meta['tvshowid']

                        meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params":{ "tvshowid": %d, "filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["title", "season", "episode", "showtitle", "firstaired", "runtime", "rating", "director", "writer", "plot", "thumbnail", "file"]}, "id": 1}' % (tvshowid, season, episode))
                        meta = six.ensure_text(meta, errors='ignore')
                        meta = json.loads(meta)['result']['episodes'][0]

                    else:
                        meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "originaltitle", "year", "genre", "studio", "country", "runtime", "rating", "votes", "mpaa", "director", "writer", "plot", "plotoutline", "tagline", "thumbnail", "file"]}, "id": 1}' % (year, str(int(year)+1), str(int(year)-1)))
                        meta = six.ensure_text(meta, errors='ignore')
                        meta = json.loads(meta)['result']['movies']
                        t = self.getTitle(title)
                        meta = [i for i in meta if year == str(i['year']) and (t == self.getTitle(i['title']) or t == self.getTitle(i['originaltitle']))][0]

                    for k, v in six.iteritems(meta):
                        if type(v) == list:
                            try: meta[k] = str(' / '.join([six.ensure_str(i, errors='ignore') for i in v]))
                            except: meta[k] = ''
                        else:
                            try: meta[k] = str(six.ensure_str(v, errors='ignore'))
                            except: meta[k] = str(v)

                    #log_utils.log('meta: ' + repr(meta))
                except:
                    log_utils.log('Getting meta from lib failed', 1)
                    meta = {}

            try: self.duration = meta['duration']
            except: self.duration = str(meta.get('runtime', 0))
            if not self.duration or self.duration == '0':
                self.duration = '2700' if self.content == 'episode' else '7200'
            #log_utils.log('play_duration: ' + repr(duration))

            items = self.getSources(title, year, imdb, tmdb, season, episode, tvshowtitle, premiered)
            items = items or []

            select = control.setting('hosts.mode') if select == None else select

            title = tvshowtitle or title
            title = self.getTitle(title)

            if len(items) == 0:
                self.url = 'close://'
                return

            if len(items) > 0:

                if select == '1' and 'plugin' in control.infoLabel('Container.PluginName'):
                    control.window.clearProperty(self.itemProperty)
                    control.window.setProperty(self.itemProperty, json.dumps(items))

                    control.window.clearProperty(self.metaProperty)
                    control.window.setProperty(self.metaProperty, json.dumps(meta))

                    control.sleep(200)

                    return control.execute('Container.Update(%s?action=addItem&title=%s)' % (sys.argv[0], urllib_parse.quote_plus(title)))

                elif select == '0' or select == '1':
                    url = self.sourcesDialog(items)

                else:
                    url = self.sourcesDirect(items)


            if url == 'close://' or url == None:
                self.url = url
                return self.errorForSources()

            from resources.lib.modules.player import player
            player().run(title, year, season, episode, imdb, tmdb, url, meta)
        except:
            log_utils.log('sources_play_fail', 1)
            pass


    def addItem(self, title):

        def sourcesDirMeta(metadata):
            if metadata == None: return metadata
            allowed = ['icon', 'poster', 'fanart', 'thumb', 'clearlogo', 'clearart', 'discart', 'title', 'year', 'tvshowtitle', 'season', 'episode', 'rating', 'plot', 'trailer', 'mediatype']
            return {k: v for k, v in six.iteritems(metadata) if k in allowed}

        control.playlist.clear()
        items = control.window.getProperty(self.itemProperty)
        items = json.loads(items)

        if items == None or len(items) == 0: control.idle() ; sys.exit()

        meta = control.window.getProperty(self.metaProperty)
        meta = json.loads(meta)
        meta = sourcesDirMeta(meta)

        sysaddon = sys.argv[0]

        syshandle = int(sys.argv[1])

        downloads = True if control.setting('downloads') == 'true' and not (control.setting('movie.download.path') == '' or control.setting('tv.download.path') == '') else False

        listMeta = control.setting('source.list.meta')

        systitle = sysname = urllib_parse.quote_plus(title)

        if 'tvshowtitle' in meta and 'season' in meta and 'episode' in meta:
            sysname += urllib_parse.quote_plus(' S%02dE%02d' % (int(meta['season']), int(meta['episode'])))
        elif 'year' in meta:
            sysname += urllib_parse.quote_plus(' (%s)' % meta['year'])


        poster = meta.get('poster') or control.addonPoster()
        if control.setting('fanart') == 'true':
            fanart = meta.get('fanart') or control.addonFanart()
        else:
            fanart = control.addonFanart()
        thumb = meta.get('thumb') or poster or fanart
        clearlogo = meta.get('clearlogo', '') or ''
        clearart = meta.get('clearart', '') or ''
        discart = meta.get('discart', '') or ''

        #banner = meta['banner'] if 'banner' in meta else '0'
        #if banner == '0': banner = poster
        #if banner == '0': banner = control.addonBanner()

        sysimage = urllib_parse.quote_plus(six.ensure_str(poster))

        downloadMenu = control.lang(32403)


        for i in range(len(items)):
            try:
                label = str(items[i]['label'])

                syssource = urllib_parse.quote_plus(json.dumps([items[i]]))

                sysurl = '%s?action=playItem&title=%s&source=%s' % (sysaddon, systitle, syssource)

                cm = []

                if items[i].get('pack'):
                    cm.append(('[I]Browse pack[/I]', 'RunPlugin(%s?action=browseItem&title=%s&source=%s)' % (sysaddon, systitle, syssource)))

                if downloads == True:
                    cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&source=%s)' % (sysaddon, sysname, sysimage, syssource)))

                try: item = control.item(label=label, offscreen=True)
                except: item = control.item(label=label)
                item.addContextMenuItems(cm)

                if listMeta == 'true':
                    item.setArt({'thumb': thumb, 'icon': thumb, 'poster': poster, 'fanart': fanart, 'clearlogo': clearlogo, 'clearart': clearart, 'discart': discart})
                    video_streaminfo = {'codec': 'h264'}
                    item.addStreamInfo('video', video_streaminfo)
                    item.setInfo(type='video', infoLabels=control.metadataClean(meta))

                else:
                    item.setArt({'thumb': thumb})
                    item.setInfo(type='video', infoLabels={})

                control.addItem(handle=syshandle, url=sysurl, listitem=item, isFolder=False)
            except:
                pass

        control.content(syshandle, 'files')
        control.directory(syshandle, cacheToDisc=True)


    def playItem(self, title, source, browse=False):
        try:
            meta = control.window.getProperty(self.metaProperty)
            meta = json.loads(meta)

            year = meta['year'] if 'year' in meta else None
            season = meta['season'] if 'season' in meta else None
            episode = meta['episode'] if 'episode' in meta else None

            imdb = meta['imdb'] if 'imdb' in meta else None
            tvdb = meta['tvdb'] if 'tvdb' in meta else None
            tmdb = meta['tmdb'] if 'tmdb' in meta else None


            if browse:
                try:
                    self.url, name = self.sourcesResolve(json.loads(source)[0], browse=True)
                    name = cleantitle.get_title(name.split('/')[-1], sep=' ')

                    try:
                        s_e = re.findall(r"(?:\w\s*|^)(\d+)\s*(?:e|x|episode)\s*(\d+)\s+", name, flags=re.I|re.S)[0]
                        season, episode = str(int(s_e[0])), str(int(s_e[1]))
                        meta.update({'season': season, 'episode': episode, 'title': name, 'plot': name})
                    except:
                        meta.update({'title': name, 'plot': name})

                    from resources.lib.modules.player import player
                    player().run(title, year, season, episode, imdb, tmdb, self.url, meta)
                    return self.url
                except:
                    return self.errorForSources()


            next = [] ; prev = [] ; total = []

            for i in range(1,1000):
                try:
                    u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
                    if u in total: raise Exception()
                    total.append(u)
                    u = dict(urllib_parse.parse_qsl(u.replace('?','')))
                    u = json.loads(u['source'])[0]
                    next.append(u)
                except:
                    break
            for i in range(-1000,0)[::-1]:
                try:
                    u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
                    if u in total: raise Exception()
                    total.append(u)
                    u = dict(urllib_parse.parse_qsl(u.replace('?','')))
                    u = json.loads(u['source'])[0]
                    prev.append(u)
                except:
                    break

            items = json.loads(source)
            items = [i for i in items+next+prev][:40]

            header = control.addonInfo('name') + ': Resolving...'

            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(header, '')
            #progressDialog.update(0)

            block = None

            for i in range(len(items)):
                try:
                    label = re.sub(' {2,}', ' ', str(items[i]['label']))
                    try:
                        if progressDialog.iscanceled(): break
                        progressDialog.update(int((100 / float(len(items))) * i), label)
                    except:
                        progressDialog.update(int((100 / float(len(items))) * i), str(header) + '[CR]' + label)

                    if items[i]['source'] == block: raise Exception()

                    w = workers.Thread(self.sourcesResolve, items[i])
                    w.start()

                    #offset = 60 * 2 if items[i].get('source') in self.hostcapDict else 0

                    if items[i].get('source').lower() in self.hostcapDict:
                        offset = 60 * 2
                    elif 'torrent' in items[i].get('source').lower():
                        offset = 60 * 2
                    else:
                        offset = 0

                    m = ''

                    for x in range(3600):
                        try:
                            if control.monitor.abortRequested(): return sys.exit()
                            if progressDialog.iscanceled(): return progressDialog.close()
                        except:
                            pass

                        k = control.condVisibility('Window.IsActive(virtualkeyboard)')
                        if k: m += '1'; m = m[-1]
                        if (w.is_alive() == False or x > 30 + offset) and not k: break
                        k = control.condVisibility('Window.IsActive(yesnoDialog)')
                        if k: m += '1'; m = m[-1]
                        if (w.is_alive() == False or x > 30 + offset) and not k: break
                        time.sleep(0.5)


                    for x in range(30):
                        try:
                            if control.monitor.abortRequested(): return sys.exit()
                            if progressDialog.iscanceled(): return progressDialog.close()
                        except:
                            pass

                        if m == '': break
                        if w.is_alive() == False: break
                        time.sleep(0.5)


                    if w.is_alive() == True: block = items[i]['source']

                    if not self.url: raise Exception()

                    try: progressDialog.close()
                    except: pass

                    control.sleep(200)
                    control.execute('Dialog.Close(virtualkeyboard)')
                    control.execute('Dialog.Close(yesnoDialog)')

                    from resources.lib.modules.player import player
                    player().run(title, year, season, episode, imdb, tmdb, self.url, meta)

                    return self.url
                except:
                    pass

            try: progressDialog.close()
            except: pass
            del progressDialog

            self.errorForSources()
        except:
            log_utils.log('playItem', 1)
            pass


    def getSources(self, title, year, imdb, tmdb, season, episode, tvshowtitle, premiered):
        progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
        if progressDialog == control.progressDialogBG:
            control.idle()

        progressDialog.create(self.module_name)
        #progressDialog.update(0)

        self.prepareSources()

        sourceDict = self.sourceDict

        progressDialog.update(0, control.lang(32600))

        if self.content == 'movie':
            sourceDict = [(i[0], i[1], getattr(i[1], 'movie', None)) for i in sourceDict]
            #genres = trakt.getGenre('movie', 'imdb', imdb)
        else:
            sourceDict = [(i[0], i[1], getattr(i[1], 'tvshow', None)) for i in sourceDict]
            #genres = trakt.getGenre('show', 'tmdb', tmdb)

        sourceDict = [(i[0], i[1], i[2]) for i in sourceDict if not hasattr(i[1], 'genre_filter') or not i[1].genre_filter]# or any(x in i[1].genre_filter for x in genres)]
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] == None]

        language = self.getLanguage()
        sourceDict = [(i[0], i[1], i[1].language) for i in sourceDict]
        sourceDict = [(i[0], i[1]) for i in sourceDict if any(x in i[2] for x in language)]

        try: sourceDict = [(i[0], i[1], control.setting('provider.' + i[0])) for i in sourceDict]
        except: sourceDict = [(i[0], i[1], 'true') for i in sourceDict]
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] == 'false']

        # if control.setting('cf.disable') == 'true':
            # sourceDict = [(i[0], i[1]) for i in sourceDict if not any(x in i[0].lower() for x in self.sourcecfDict)]

        sourceDict = [(i[0], i[1], i[1].priority) for i in sourceDict]

        random.shuffle(sourceDict)
        sourceDict = sorted(sourceDict, key=lambda i: i[2])

        threads = []

        if self.content == 'movie':
            #title = self.getTitle(title)
            title, year = cleantitle.scene_title(title, year)
            localtitle = cache.get(self.getLocalTitle, 168, title, imdb)
            aliases = cache.get(self.getAliasTitles, 168, imdb, localtitle)
            log_utils.log('Scrape - movtitle: '+title+' | localtitle: '+localtitle+' | year: '+year+' | aliases: '+repr(aliases))
            for i in sourceDict: threads.append(workers.Thread(self.getMovieSource, title, localtitle, aliases, year, imdb, i[0], i[1]))
        else:
            #tvshowtitle = self.getTitle(tvshowtitle)
            tvshowtitle, year, season, episode = cleantitle.scene_tvtitle(tvshowtitle, year, season, episode)
            localtvshowtitle = cache.get(self.getLocalTitle, 168, tvshowtitle, imdb)
            aliases = cache.get(self.getAliasTitles, 168, imdb, localtvshowtitle)
            log_utils.log('Scrape - tvtitle: '+tvshowtitle+' | localtitle: '+localtvshowtitle+' | year: '+year+' | season: '+season+' | episode: '+episode+' | aliases: '+repr(aliases))
            #Disabled on 11/11/17 due to hang. Should be checked in the future and possible enabled again.
            #season, episode = thexem.get_scene_episode_number(tvdb, season, episode)
            for i in sourceDict: threads.append(workers.Thread(self.getEpisodeSource, title, year, imdb, tmdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, i[0], i[1]))

        s = [i[0] + (i[1],) for i in zip(sourceDict, threads)]
        s = [(i[3].getName(), i[0], i[2]) for i in s]

        # mainsourceDict = [i[0] for i in s if i[2] == 0]
        sourcelabelDict = dict([(i[0], i[1].upper()) for i in s])

        [i.start() for i in threads]

        max_quality = control.setting('hosts.quality') or '0' if not self.unfiltered else '0'
        max_quality = int(max_quality)
        min_quality = control.setting('min.quality') or '3' if not self.unfiltered else '3'
        min_quality = int(min_quality)

        pre_emp = control.setting('preemptive.termination') if not self.unfiltered else 'false'
        pre_emp_limit = int(control.setting('preemptive.limit'))

        try: timeout = int(control.setting('scrapers.timeout.1')) if not self.unfiltered else 60
        except: timeout = 40

        start_time = time.time()
        end_time = start_time + timeout

        string1 = control.lang(32404)
        string2 = control.lang(32405)
        string3 = control.lang(32406)
        string4 = control.lang(32601)
        string5 = control.lang(32602)
        string6 = control.lang(32606)
        string7 = control.lang(32607)

        source_4k = source_1080 = source_720 = source_sd = source_filtered_out = total = 0
        source_4k_raw = 0
        debrid_total = non_debrid_total = raw_total = 0
        direct_total = 0

        line1 = line2 = line3 = ""

        total_format = '[COLOR %s][B]%s[/B][/COLOR]'
        pdiag_line_nd = '[COLOR deepskyblue][B]ND:%s[/B][/COLOR] | [COLOR red][B]D:%s[/B][/COLOR] | [COLOR lime][B]DIR:%s[/B][/COLOR] | S:%s'
        pdiag_line_q = '4K:%s [raw:%s] | 1080:%s | 720:%s | SD:%s | T:%s | F:%s'

        for i in range(0, 4 * timeout):

            try:

                if control.monitor.abortRequested():
                    return sys.exit()
                try:
                    if progressDialog.iscanceled():
                        break
                except:
                    pass
                try:
                    if progressDialog.isFinished():
                        break
                except:
                    pass

                if self.sources:
                    raw_total = len(self.sources)

                    source_4k_raw = len([
                        e for e in self.sources
                        if ('4k' in str(e.get('quality', '')).lower() or '2160' in str(e.get('quality', '')).lower() or 'uhd' in str(e.get('quality', '')).lower())
                    ])

                    # Debrid candidate detection is display-only and should reflect what can be routed via debrid.
                    def _is_debrid_candidate(src_item):
                        src_name = (src_item.get('source') or '').lower()
                        provider_name = (src_item.get('provider') or '').lower()
                        src_url = src_item.get('url') or ''
                        return (
                            src_item.get('debridonly', False)
                            or src_name in self.hostprDict
                            or 'magnet:' in src_url
                            or provider_name in ['furk', 'easynews']
                        )

                    debrid_total = len([e for e in self.sources if _is_debrid_candidate(e)]) if debrid.status() else 0
                    non_debrid_total = max(0, raw_total - debrid_total)
                    direct_total = len([e for e in self.sources if e.get('direct') is True or e.get('local') is True or e.get('official') is True])

                    self.sourcesFilter()

                    if min_quality == 0:
                        source_4k = len([e for e in self.sources if e['quality'] == '4k'])
                    elif min_quality == 1:
                        source_1080 = len([e for e in self.sources if e['quality'] == '1080p'])
                        if max_quality == 0:
                            source_4k = len([e for e in self.sources if e['quality'] == '4k'])
                    elif min_quality == 2:
                        source_720 = len([e for e in self.sources if e['quality'] == '720p'])
                        if max_quality == 0:
                            source_4k = len([e for e in self.sources if e['quality'] == '4k'])
                            source_1080 = len([e for e in self.sources if e['quality'] == '1080p'])
                        elif max_quality == 1:
                            source_1080 = len([e for e in self.sources if e['quality'] == '1080p'])
                    elif min_quality == 3:
                        source_sd = len([e for e in self.sources if e['quality'] in ['sd', 'scr', 'cam']])
                        if max_quality == 0:
                            source_4k = len([e for e in self.sources if e['quality'] == '4k'])
                            source_1080 = len([e for e in self.sources if e['quality'] == '1080p'])
                            source_720 = len([e for e in self.sources if e['quality'] == '720p'])
                        elif max_quality == 1:
                            source_1080 = len([e for e in self.sources if e['quality'] == '1080p'])
                            source_720 = len([e for e in self.sources if e['quality'] == '720p'])
                        elif max_quality == 2:
                            source_720 = len([e for e in self.sources if e['quality'] == '720p'])

                    total = source_4k + source_1080 + source_720 + source_sd
                    source_filtered_out = len([e for e in self.f_out_sources])

                    if pre_emp == 'true':
                        if max_quality == 0:
                            if source_4k >= pre_emp_limit:
                                break
                        elif max_quality == 1:
                            if source_1080 >= pre_emp_limit:
                                break
                        elif max_quality == 2:
                            if source_720 >= pre_emp_limit:
                                break
                        elif max_quality == 3:
                            if source_sd >= pre_emp_limit:
                                break

                source_4k_label = total_format % ('red', source_4k) if source_4k == 0 else total_format % ('lime', source_4k)
                source_4k_raw_label = total_format % ('red', source_4k_raw) if source_4k_raw == 0 else total_format % ('yellow', source_4k_raw)
                source_1080_label = total_format % ('red', source_1080) if source_1080 == 0 else total_format % ('lime', source_1080)
                source_720_label = total_format % ('red', source_720) if source_720 == 0 else total_format % ('lime', source_720)
                source_sd_label = total_format % ('red', source_sd) if source_sd == 0 else total_format % ('lime', source_sd)
                source_total_label = total_format % ('red', total) if total == 0 else total_format % ('lime', total)
                source_filtered_out_label = total_format % ('red', source_filtered_out)
                non_debrid_label = total_format % ('lime', non_debrid_total) if non_debrid_total > 0 else total_format % ('red', non_debrid_total)
                debrid_label = total_format % ('lime', debrid_total) if debrid_total > 0 else total_format % ('red', debrid_total)
                direct_label = total_format % ('lime', direct_total) if direct_total > 0 else total_format % ('red', direct_total)
                raw_total_label = total_format % ('lime', raw_total) if raw_total > 0 else total_format % ('red', raw_total)

                # if (i / 2) < timeout:
                try:
                    # mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True and x.getName() in mainsourceDict]
                    info = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True]
                    # if i >= timeout and len(mainleft) == 0 and len(self.sources) >= 100 * len(info): break # improve responsiveness
                    line1 = pdiag_line_q % (source_4k_label, source_4k_raw_label, source_1080_label, source_720_label, source_sd_label, source_total_label, source_filtered_out_label)
                    line2 = pdiag_line_nd % (non_debrid_label, debrid_label, direct_label, raw_total_label)

                    if len(info) > 6:
                        line3 = string3 % (str(len(info)))
                    elif len(info) > 0:
                        line3 = string3 % (', '.join(info))
                    else:
                        self.last_scrape_counts = {
                            'non_debrid': non_debrid_total,
                            'debrid': debrid_total,
                            'direct': direct_total,
                            'total': raw_total,
                            'filtered': source_filtered_out,
                        }
                        log_utils.log('Scrape counts - ND:{non_debrid} D:{debrid} DIR:{direct} T:{total} F:{filtered}'.format(**self.last_scrape_counts))
                        line3 = 'PROMISE CUSTOM: No Streams Available.'
                        if not progressDialog == control.progressDialogBG:
                            progressDialog.update(max(1, percent), line1 + '[CR]' + line2 + '[CR]' + line3)
                        else:
                            progressDialog.update(max(1, percent), self.module_name, line1 + ' | ' + line2 + '[CR]' + line3)
                        break
                    # percent = int(100 * float(i) / (2 * timeout) + 0.5)
                    current_time = time.time()
                    current_progress = current_time - start_time
                    percent = int((current_progress / float(timeout)) * 100)
                    if not progressDialog == control.progressDialogBG:
                        progressDialog.update(max(1, percent), line1 + '[CR]' + line2 + '[CR]' + line3)
                    else:
                        progressDialog.update(max(1, percent), self.module_name, line1 + ' | ' + line2 + '[CR]' + line3)
                    self.last_scrape_counts = {
                        'non_debrid': non_debrid_total,
                        'debrid': debrid_total,
                        'direct': direct_total,
                        'total': raw_total,
                        'filtered': source_filtered_out,
                    }
                    # if len(mainleft) == 0: break
                    if end_time < current_time: break
                except:
                    log_utils.log('Source fetching dialog exception', 1)
                    break
                # else: # old implementation that makes "priority: 0" scrapers to ignore the timeout setting
                    # try:
                        # mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True and x.getName() in mainsourceDict]
                        # info = mainleft
                        # if len(info) > 6: line3 = 'Waiting for: %s' % (str(len(info)))
                        # elif len(info) > 0: line3 = 'Waiting for: %s' % (', '.join(info))
                        # else: break
                        # percent = int(100 * float(i) / (2 * timeout) + 0.5) % 100
                        # if not progressDialog == control.progressDialogBG: progressDialog.update(max(1, percent), line1 + '[CR]' + line3)
                        # else: progressDialog.update(max(1, percent), line1 + '[CR]' + line3)
                    # except Exception as e:
                        # log_utils.log('Exception Raised: %s' % str(e))
                        # break

                #time.sleep(0.25)
                control.sleep(250)
            except:
                log_utils.log('sourcefail', 1)
                pass

        if progressDialog == control.progressDialogBG:
            progressDialog.close()
            self.sourcesFilter(sort=True)
        else:
            self.sourcesFilter(sort=True)
            progressDialog.close()

        if pre_emp == 'true': # don't know why pre-emp needs 2nd pass filtering/sorting, but it does
            self.sourcesFilter(sort=True)

        if not getattr(self, 'last_scrape_counts', None):
            self.last_scrape_counts = {
                'non_debrid': non_debrid_total,
                'debrid': debrid_total,
                'direct': direct_total,
                'total': raw_total,
                'filtered': source_filtered_out,
            }

        log_utils.log('Scrape counts - ND:{non_debrid} D:{debrid} DIR:{direct} T:{total} F:{filtered}'.format(**self.last_scrape_counts))

        del progressDialog
        del threads

        control.idle()

        if not self.sources:
            self.errorForSources()

        return self.sources


    def prepareSources(self):
        try:
            control.makeFile(control.dataPath)

            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
            dbcur.execute("CREATE TABLE IF NOT EXISTS rel_url (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""rel_url TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
            dbcur.execute("CREATE TABLE IF NOT EXISTS rel_src (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""hosts TEXT, ""added TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
        except:
            pass


    def _is_class_provider(self, call):
        return isinstance(call, type)


    def _provider_instance(self, call):
        return call() if self._is_class_provider(call) else call


    def _build_external_movie_data(self, title, aliases, year, imdb):
        return {
            'title': title,
            'aliases': aliases or [],
            'year': year,
            'imdb': imdb
        }


    def _build_external_episode_data(self, title, tvshowtitle, aliases, year, imdb, season, episode):
        return {
            'title': title,
            'tvshowtitle': tvshowtitle,
            'aliases': aliases or [],
            'year': year,
            'imdb': imdb,
            'season': season,
            'episode': episode
        }


    def _call_provider_sources(self, call, url_data):
        provider = self._provider_instance(call)
        try:
            return provider.sources(url_data, self.hostDict, self.hostprDict)
        except TypeError:
            return provider.sources(url_data, self.hostDict)


    def getMovieSource(self, title, localtitle, aliases, year, imdb, source, call):

        try:
            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
        except:
            pass

        ''' Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. '''
        if imdb == '0':
            try:
                dbcur.execute("DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
                dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
                dbcon.commit()
            except:
                pass
        ''' END '''

        try:
            sources = []
            dbcur.execute("SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            match = dbcur.fetchone()
            t1 = int(re.sub('[^0-9]', '', str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            update = abs(t2 - t1) > 60
            if update == False:
                sources = eval(six.ensure_str(match[4]))
                return self.sources.extend(sources)
        except:
            pass

        try:
            url = None
            dbcur.execute("SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            url = dbcur.fetchone()
            url = eval(six.ensure_str(url[4]))
        except:
            pass

        try:
            if url == None: url = call.movie(imdb, title, localtitle, aliases, year)
            if url == None: raise Exception()
            dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
            dbcon.commit()
        except:
            if self._is_class_provider(call):
                try:
                    url = self._build_external_movie_data(title, aliases, year, imdb)
                    dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
                    dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
                    dbcon.commit()
                except:
                    pass

        try:
            sources = []
            sources = self._call_provider_sources(call, url)
            if sources == None or sources == []: raise Exception()
            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            for i in sources: i.update({'provider': source})
            self.sources.extend(sources)
            dbcur.execute("DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            dbcon.commit()
        except:
            pass


    def getEpisodeSource(self, title, year, imdb, tmdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, source, call):
        try:
            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
        except:
            pass

        try:
            sources = []
            dbcur.execute("SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            match = dbcur.fetchone()
            t1 = int(re.sub('[^0-9]', '', str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            update = abs(t2 - t1) > 60
            if update == False:
                sources = eval(six.ensure_str(match[4]))
                return self.sources.extend(sources)
        except:
            pass

        try:
            url = None
            dbcur.execute("SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            url = dbcur.fetchone()
            url = eval(six.ensure_str(url[4]))
        except:
            pass

        try:
            if url == None: url = call.tvshow(imdb, tmdb, tvshowtitle, localtvshowtitle, aliases, year)
            if url == None: raise Exception()
            dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
            dbcon.commit()
        except:
            if self._is_class_provider(call):
                try:
                    url = self._build_external_episode_data(title, tvshowtitle, aliases, year, imdb, season, episode)
                    dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
                    dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
                    dbcon.commit()
                except:
                    pass

        try:
            ep_url = None
            dbcur.execute("SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            ep_url = dbcur.fetchone()
            ep_url = eval(six.ensure_str(ep_url[4]))
        except:
            pass

        try:
            if url == None: raise Exception()
            if ep_url == None and not self._is_class_provider(call): ep_url = call.episode(url, imdb, tmdb, title, premiered, season, episode)
            elif ep_url == None and self._is_class_provider(call): ep_url = url
            if ep_url == None: raise Exception()
            dbcur.execute("DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(ep_url)))
            dbcon.commit()
        except:
            pass

        try:
            sources = []
            sources = self._call_provider_sources(call, ep_url)
            if sources == None or sources == []: raise Exception()
            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            for i in sources: i.update({'provider': source})
            self.sources.extend(sources)
            dbcur.execute("DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, season, episode))
            dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(sources), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            dbcon.commit()
        except:
            pass


    def alterSources(self, url, meta):

        try:
            if control.setting('hosts.mode') == '2': url += '&select=1'
            else: url += '&select=2'
            control.execute('RunPlugin(%s)' % url)
        except:
            pass


    def clearSources(self):
        try:
            control.idle()

            yes = control.yesnoDialog(control.lang(32407))
            if not yes: return

            control.makeFile(control.dataPath)
            dbcon = database.connect(control.providercacheFile)
            dbcur = dbcon.cursor()
            dbcur.execute("DROP TABLE IF EXISTS rel_src")
            dbcur.execute("DROP TABLE IF EXISTS rel_url")
            dbcur.execute("VACUUM")
            dbcon.commit()

            control.infoDialog(control.lang(32408), sound=True, icon='INFO')
        except:
            pass


    def uniqueSourcesGen(self, sources):
        uniqueURLs = set()
        for source in sources:
            url = source.get('url')
            if isinstance(url, six.string_types):
                if 'magnet:' in url:
                    url = url[:60].lower()
                    #url = re.findall(u'btih:(\w{40})', url)[0]
                if url not in uniqueURLs:
                    uniqueURLs.add(url)
                    yield source # Yield the unique source.
                else:
                    pass # Ignore duped sources.
            else:
                yield source # Always yield non-string url sources.


    def sourcesProcessTorrents(self, torrent_sources):#adjusted Fen code
        try:
            from resources.lib.modules import debridcheck
            DBCheck = debridcheck.DebridCheck()

            def _debrid_bucket(value):
                name = (value or '').lower().replace('-', '').replace('.', '').replace(' ', '')
                if 'realdebrid' in name:
                    return 'rd'
                if 'alldebrid' in name:
                    return 'ad'
                if 'premiumize' in name:
                    return 'pm'
                if 'debridlink' in name:
                    return 'dl'
                return ''

            hashList = []
            cachedTorrents = []
            uncachedTorrents = []

            for i in torrent_sources:
                try:
                    r = re.findall(r'btih:(\w{40})', str(i['url']))[0]
                    if r:
                        infoHash = r.lower()
                        i['info_hash'] = infoHash
                        hashList.append(infoHash)
                except:
                    torrent_sources.remove(i)

            torrent_sources = [i for i in torrent_sources if 'info_hash' in i]
            if len(torrent_sources) == 0:
                return torrent_sources

            hashList = list(set(hashList))
            cachedRDHashes, cachedADHashes, cachedPMHashes, cachedDLHashes = DBCheck.run(hashList)

            #cached
            cachedRDSources = [dict(i.items()) for i in torrent_sources if (any(v in i.get('info_hash') for v in cachedRDHashes) and _debrid_bucket(i.get('debrid', '')) == 'rd')]
            cachedTorrents.extend(cachedRDSources)
            cachedADSources = [dict(i.items()) for i in torrent_sources if (any(v in i.get('info_hash') for v in cachedADHashes) and _debrid_bucket(i.get('debrid', '')) == 'ad')]
            cachedTorrents.extend(cachedADSources)
            cachedPMSources = [dict(i.items()) for i in torrent_sources if (any(v in i.get('info_hash') for v in cachedPMHashes) and _debrid_bucket(i.get('debrid', '')) == 'pm')]
            cachedTorrents.extend(cachedPMSources)
            cachedDLSources = [dict(i.items()) for i in torrent_sources if (any(v in i.get('info_hash') for v in cachedDLHashes) and _debrid_bucket(i.get('debrid', '')) == 'dl')]
            cachedTorrents.extend(cachedDLSources)
            for i in cachedTorrents: i.update({'source': 'cached torrent'})

            #uncached
            uncachedRDSources = [dict(i.items()) for i in torrent_sources if (not any(v in i.get('info_hash') for v in cachedRDHashes) and _debrid_bucket(i.get('debrid', '')) == 'rd')]
            uncachedTorrents.extend(uncachedRDSources)
            uncachedADSources = [dict(i.items()) for i in torrent_sources if (not any(v in i.get('info_hash') for v in cachedADHashes) and _debrid_bucket(i.get('debrid', '')) == 'ad')]
            uncachedTorrents.extend(uncachedADSources)
            uncachedPMSources = [dict(i.items()) for i in torrent_sources if (not any(v in i.get('info_hash') for v in cachedPMHashes) and _debrid_bucket(i.get('debrid', '')) == 'pm')]
            uncachedTorrents.extend(uncachedPMSources)
            uncachedDLSources = [dict(i.items()) for i in torrent_sources if (not any(v in i.get('info_hash') for v in cachedDLHashes) and _debrid_bucket(i.get('debrid', '')) == 'dl')]
            uncachedTorrents.extend(uncachedDLSources)
            for i in uncachedTorrents: i.update({'source': 'uncached torrent'})

            return cachedTorrents + uncachedTorrents
        except:
            log_utils.log('torrent_check', 1)
            control.infoDialog('Error Processing Torrents')
            return torrent_sources


    def sourcesFilter(self, sort=False):

        self.sources = [i for i in self.sources if not i['source'].lower() in self.hostblockDict]

        for s in self.sources:
            q = str(s.get('quality', 'sd')).lower()
            search_blob = ' '.join([
                str(s.get('quality', '')),
                str(s.get('name', '')),
                str(s.get('url', '')),
                str(s.get('info', ''))
            ]).lower()
            if '4k' in q or '2160' in q or 'uhd' in q or any(token in search_blob for token in [' 2160', '2160p', ' 4k', '4k ', 'uhd']):
                q = '4k'
            elif q == 'hd':
                q = '720p'
            s.update({'quality': q})
            if self.content == 'episode' and s['quality'] in ['scr', 'cam']:
                s.update({'quality': 'sd'})

        if self.unfiltered:
            if sort:
                self.sourcesSort()
            return self.sources

        max_quality = control.setting('hosts.quality') or '0'
        max_quality = int(max_quality)
        min_quality = control.setting('min.quality') or '3'
        min_quality = int(min_quality)
        remove_cam = control.setting('remove.cam') or 'false'

        size_filters = control.setting('size.filters') or 'false'
        min_size_gb = control.setting('min.size.gb') or 0
        min_size_gb = float(min_size_gb)
        max_size_gb = control.setting('max.size.gb') or 20
        max_size_gb = float(max_size_gb)

        debrid_only = control.setting('debrid.only') or 'false'

        remove_captcha = control.setting('remove.captcha') or 'false'

        remove_hevc = control.setting('remove.hevc') or 'false'

        remove_dv = control.setting('remove.dv') or 'false'

        remove_dups = control.setting('remove.dups') or 'true'

        stotal = self.sources

        for i in self.sources:
            if i['quality'] == '4k':
                i.update({'q_filter': 0})
            elif i['quality'] == '1080p':
                i.update({'q_filter': 1})
            elif i['quality'] == '720p':
                i.update({'q_filter': 2})
            else:
                i.update({'q_filter': 3})

            if size_filters == 'true':
                if 'size' in i and not i['size'] in [0.0, 0, None] and not 'pack' in i:
                    gb_per_hour = (i['size'] * 3600) / int(self.duration)
                else:
                    gb_per_hour = min_size_gb + 0.25
                i.update({'gb_per_hour': gb_per_hour})

        self.sources = [i for i in self.sources if max_quality <= i.get('q_filter', 3) <= min_quality]

        if remove_cam == 'true':
            self.sources = [i for i in self.sources if not i['quality'] in ['scr', 'cam']]

        if size_filters == 'true':
            self.sources = [i for i in self.sources if min_size_gb <= i['gb_per_hour'] <= max_size_gb]

        if debrid_only == 'true' and debrid.status():
            self.sources = [i for i in self.sources if (i['source'].lower() in self.hostprDict or 'torrent' in i['source'].lower()) or i['provider'] in ['furk', 'easynews']]

        try:
            if remove_dups == 'true' and len(self.sources) > 1:
                self.sources = list(self.uniqueSourcesGen(self.sources))
        except:
            log_utils.log('DUP - Exception', 1)
            pass

        if remove_hevc == 'true':
            self.sources = [i for i in self.sources if not any(x in i['url'] for x in ['hevc', 'h265', 'x265', 'h.265', 'x.265', 'HEVC', 'H265', 'X265', 'H.265', 'X.265']) and not any(
                                                       x in i.get('name', '').lower() for x in ['hevc', 'h265', 'x265', 'h.265', 'x.265'])]

        if remove_dv == 'true':
            self.sources = [i for i in self.sources if not any(x in i.get('name', '').lower() for x in ['.dv.', '.dolby.vision.', '.dolbyvision.', '.dovi.'])]

        if remove_captcha == 'true':
            self.sources = [i for i in self.sources if not (i['source'].lower() in self.hostcapDict and not 'debrid' in i)]

        if not self.sources and stotal:
            log_utils.log('Strict source filters removed all sources, using fallback source set')
            self.sources = [dict(i.items()) for i in stotal]

        filtered_out = [i for i in stotal if not i in self.sources]
        self.f_out_sources.extend(filtered_out)

        if sort:
            self.sourcesSort()


    def sourcesSort(self):

        main_sort = control.setting('main.sort') or '0'
        debrid_only = control.setting('debrid.only') or 'false'

        size_sort = control.setting('torr.sort.size') or 'true'

        sort_provider = control.setting('hosts.sort.provider') or 'true'

        check_torr_cache = control.setting('check.torr.cache') or 'true'

        remove_uncached = control.setting('remove.uncached') or 'false'

        autoplay_on = control.setting('hosts.mode') == '2'

        torrent_resolvers = ['Real-Debrid', 'AllDebrid', 'Premiumize.me', 'Debrid-Link.fr', 'Linksnappy']
        torrent_pack_resolvers = cache_check_resolvers = ['Real-Debrid', 'AllDebrid', 'Premiumize.me', 'Debrid-Link.fr']

        random.shuffle(self.sources)

        local = [i for i in self.sources if 'local' in i and i['local'] == True]
        for i in local: i.update({'language': self._getPrimaryLang() or 'en'})
        self.sources = [i for i in self.sources if not i in local]

        multi = [i['language'] for i in self.sources]
        multi = [x for y,x in enumerate(multi) if x not in multi[:y]]
        multi = True if len(multi) > 1 else False

        if sort_provider == 'true':
            self.sources = sorted(self.sources, key=lambda k: k['provider'])

        if size_sort == 'true':
            self.sources = sorted(self.sources, key=lambda k: k.get('size', 0.0), reverse=True)

        pre_debrid_filter_sources = [dict(i.items()) for i in self.sources]
        filter = []

        filter += [dict(list(i.items()) + [('debrid', 'un')]) for i in self.sources if i['provider'] == 'easynews']
        filter += [dict(list(i.items()) + [('debrid', 'furk')]) for i in self.sources if i['provider'] == 'furk']

        for d in debrid.debrid_resolvers:
            valid_hoster = set([i['source'] for i in self.sources])
            valid_hoster = [i for i in valid_hoster if d.valid_url('', i)]

            torrentSources = [i for i in self.sources if 'magnet:' in i['url']
                              and d.name in torrent_resolvers
                              and not (i.get('pack') and d.name not in torrent_pack_resolvers)]
            if torrentSources:
                for i in torrentSources:
                    i.update({'debrid': d.name})
                if check_torr_cache == 'true' and d.name in cache_check_resolvers:
                    checkedTorrentSources = self.sourcesProcessTorrents(torrentSources)
                    cached = [dict(i.items()) for i in checkedTorrentSources if i['source'] == 'cached torrent']
                    filter += cached
                    filter += [dict(i.items()) for i in checkedTorrentSources if i['source'].lower() == 'torrent']
                    if (remove_uncached == 'false' or self.unfiltered):
                        filter += [dict(i.items()) for i in checkedTorrentSources if i['source'] == 'uncached torrent']
                else:
                    filter += [dict(i.items()) for i in torrentSources]
            filter += [dict(list(i.items()) + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

        filter += [i for i in self.sources if not i['source'].lower() in self.hostprDict and i.get('debridonly', False) == False]

        # Keep one plain hoster fallback copy so non-debrid links remain visible when requested.
        if debrid_only != 'true':
            plain_hoster_fallback = [
                dict(i.items()) for i in pre_debrid_filter_sources
                if not i.get('debridonly', False)
                and i.get('provider') not in ['furk', 'easynews']
                and 'magnet:' not in str(i.get('url', ''))
            ]
            filter += plain_hoster_fallback

        self.sources = filter

        if not self.sources and pre_debrid_filter_sources:
            log_utils.log('Debrid/hoster sorting returned 0 sources, using pre-filter source set fallback')
            self.sources = pre_debrid_filter_sources

        filter = []
        filter += [i for i in self.sources if i['quality'] == '4k']
        filter += [i for i in self.sources if i['quality'] == '1080p']
        filter += [i for i in self.sources if i['quality'] == '720p']
        filter += [i for i in self.sources if i['quality'] == 'sd']
        filter += [i for i in self.sources if i['quality'] in ['scr', 'cam']]
        self.sources = filter

        if main_sort == '1':
            self.sources = [i for i in self.sources if i.get('debrid', '')] + [i for i in self.sources if not i.get('debrid', '')]

        if multi == True:
            self.sources = [i for i in self.sources if not i['language'] == 'en'] + [i for i in self.sources if i['language'] == 'en']

        self.sources = local + [i for i in self.sources if i.get('official')] + [i for i in self.sources if not i.get('official')]

        # Keep non-debrid links as fallback entries at the end of the list.
        if main_sort == '1':
            debrid_sources = [i for i in self.sources if i.get('debrid', '')]
            non_debrid_sources = [i for i in self.sources if not i.get('debrid', '')]
            self.sources = debrid_sources + non_debrid_sources


        official_color = control.setting('official.identify') or '15'
        official_identify = self.getPremColor(official_color)

        prem_color = control.setting('prem.identify') or '20'
        prem_identify = 'red'
        non_prem_identify = 'deepskyblue'

        sec_color = control.setting('sec.identify') or '17'
        sec_identify = self.getPremColor(sec_color)

        double_line = control.setting('linesplit') == '1'
        simple = control.setting('linesplit') == '2'
        single_line = control.setting('linesplit') == '0'

        name_setting = control.setting('sources.name') == '0'

        for i in range(len(self.sources)):

            u = self.sources[i]['url']

            p = self.sources[i]['provider'].upper()

            q = self.sources[i]['quality'].upper()

            l = self.sources[i]['language'].upper()

            n = self.sources[i].get('name', '') or ''

            o = self.sources[i].get('official', False)

            s = self.sources[i]['source'].upper()
            if self.sources[i].get('pack'):
                s += ' (PACK)'
            if 'UNCACHED' in s:
                s = '[COLOR dimgrey]%s[/COLOR]' % s

            try: d = self.sources[i]['debrid'].upper()
            except: d = self.sources[i]['debrid'] = ''
            if d:
                if d == 'ALLDEBRID': d = 'AD'
                if d == 'DEBRID-LINK.FR': d = 'DL.FR'
                if d == 'LINKSNAPPY': d = 'LS'
                if d == 'MEGADEBRID': d = 'MD'
                if d == 'PREMIUMIZE.ME': d = 'PM'
                if d == 'REAL-DEBRID': d = 'RD'
                if d == 'ZEVERA': d = 'ZVR'

            t = ''
            if name_setting and n:
                t = n
            else:
                #f1 = self.sources[i].get('info', '') or ''
                f1 = ' / '.join(['%s' % info.strip() for info in self.sources[i].get('info', '').split('|')])
                f2 = '.'.join((n, u)) if n else u
                f2 = source_utils.getFileType(f2)
                t = ' / '.join((f1, f2))
            try: size_info = self.sources[i].get('info', '').split(' /')[0]
            except: size_info = ''
            if size_info and size_info.strip().lower().endswith('gb'):
                t = ' / '.join((size_info, t))
            t = t.strip(' /')
            if t:
                t = '[COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, t)

            if double_line:
                if o:
                    label = '[COLOR %s]%03d | %s | [B]%s[/B][/COLOR][CR] ' % (official_identify, int(i+1), p, s)

                elif d:
                    label = '[COLOR %s]%03d' % (prem_identify, int(i+1))
                    if multi == True and not l == 'EN':
                        label += ' | [B]%s[/B]' % l
                    label += ' | %s | [B]%s[/B] | %s | [B]%s[/B][/COLOR][CR]    %s' % (d, q, p, s, t)

                else:
                    label = '[COLOR %s]%03d' % (non_prem_identify, int(i+1))
                    if multi == True and not l == 'EN':
                        label += ' | [B]%s[/B]' % l
                    label += ' | [B]%s[/B] | %s | [B]%s[/B][/COLOR][CR]    %s' % (q, p, s, t)

            elif simple:
                if d:
                    label = '[COLOR %s]%03d' % (prem_identify, int(i+1))
                    if multi == True and not l == 'EN':
                        label += ' | [B]%s[/B]' % l
                    label += ' | %s | [B]%s[/B] | %s | [B]%s[/B][/COLOR]' % (d, q, p, s)
                else:
                    label = '[COLOR %s]%03d' % (non_prem_identify, int(i+1))
                    if multi == True and not l == 'EN':
                        label += ' | [B]%s[/B]' % l
                    label += ' | ND | [B]%s[/B] | %s | [B]%s[/B][/COLOR]' % (q, p, s)

            else:
                if o:
                    label = '[COLOR %s]%03d | %s | [B]%s[/B][/COLOR]' % (official_identify, int(i+1), p, s)

                elif d:
                    label = '[COLOR %s]%03d' % (prem_identify, int(i+1))
                    if multi == True and not l == 'EN':
                        label += ' | [B]%s[/B]' % l
                    label += ' | %s | [B]%s[/B] | %s | [B]%s[/B] | [/COLOR]%s' % (d, q, p, s, t)

                else:
                    label = '[COLOR %s]%03d' % (non_prem_identify, int(i+1))
                    if multi == True and not l == 'EN':
                        label += ' | [B]%s[/B]' % l
                    label += ' | [B]%s[/B] | %s | [B]%s[/B][/COLOR] | %s' % (q, p, s, t)

            label = label.replace(' |  |', ' |').replace('| 0 |', '|')

            # nasty
            if double_line and t:
                label_up, label_down = label.split('[CR]')
                label_up_clean = label_up.replace('[COLOR %s]' % prem_identify, '').replace('[/COLOR]', '').replace('[B]', '').replace('[/B]', '')
                label_down_clean = label_down.replace('[COLOR %s]' % sec_identify, '').replace('[/COLOR]', '').replace('[I]', '').replace('[/I]', '')
                if len(label_down_clean) > len(label_up_clean):
                    label_up += (len(label_down_clean) - len(label_up_clean)) * '  '
                    label = '[CR]'.join((label_up, label_down))

            self.sources[i]['label'] = label

        self.sources = [i for i in self.sources if 'label' in i]


    def sourcesResolve(self, item, info=False, browse=False):
        try:
            self.url = None
            name = ''

            u = url = item['url']

            d = item['debrid']
            direct = item['direct']
            local = item.get('local', False)
            pack = item.get('pack')

            provider = item['provider']
            call = [i[1] for i in self.sourceDict if i[0] == provider][0]
            provider_obj = self._provider_instance(call)
            if hasattr(provider_obj, 'resolve'):
                u = url = provider_obj.resolve(url)
            else:
                u = url

            if not url or (not '://' in url and not local and 'magnet:' not in url): raise Exception()

            # Some resolvers occasionally return bare plugin:// links with no addon id.
            # Kodi cannot play these and throws "Unable to find plugin".
            parsed_url = urllib_parse.urlparse(url)
            if parsed_url.scheme == 'plugin' and not parsed_url.netloc:
                raise Exception()

            if not local:
                url = url[8:] if url.startswith('stack:') else url

                urls = []
                for part in url.split(' , '):
                    u = part

                    if not d in ['', 'un', 'furk']:
                        if browse and pack:
                            url_list = debrid.resolver(part, d, from_pack=pack, return_list=True)
                            url_list = sorted(url_list, key=lambda k: k['name'])
                            select = control.selectDialog([i['name'] for i in url_list], item.get('name', 'File list:'))
                            if select == -1: return
                            part = url_list[select]['link']
                            name = url_list[select]['name']
                            pack = None
                        part = debrid.resolver(part, d, from_pack=pack)
                        if not part and d == 'Real-Debrid' and debrid.last_error_code in ['429', '451']:
                            self.rd_hard_stop = True
                            self.rd_hard_stop_reason = debrid.last_error_code
                            return

                    elif not direct == True:
                        hmf = resolveurl.HostedMediaFile(url=u, include_disabled=True, include_universal=False)
                        if hmf.valid_url() == True: part = hmf.resolve()

                    urls.append(part)

                url = 'stack://' + ' , '.join(urls) if len(urls) > 1 else urls[0]

            if not url: raise Exception()

            ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
            if ext == 'rar': raise Exception()

            try: headers = url.rsplit('|', 1)[1]
            except: headers = ''
            headers = urllib_parse.quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
            headers = dict(urllib_parse.parse_qsl(headers))

            # if url.startswith('http') and '.m3u8' in url:
                # try: result = client.request(url.split('|')[0], headers=headers, output='geturl', timeout='20')
                # except: result = None
                # if result == None: raise Exception()

            # elif url.startswith('http'):
                # try: result = client.request(url.split('|')[0], headers=headers, output='chunk', timeout='20')
                # except: result = None
                # if result == None: raise Exception()

            self.url = url

            if browse:
                return url, name
            return url
        except:
            log_utils.log('Resolve failure for provider: {} | url: {}'.format(item.get('provider', 'unknown'), item.get('url', '')), 1)
            if info == True: self.errorForSources()
            return


    def sourcesDialog(self, items):
        try:
            self.rd_hard_stop = False
            self.rd_hard_stop_reason = ''

            labels = [i['label'] for i in items]

            select = control.selectDialog(labels)
            if select == -1: return 'close://'

            next = [y for x,y in enumerate(items) if x >= select]
            prev = [y for x,y in enumerate(items) if x < select][::-1]

            items = [items[select]]
            items = [i for i in items+next+prev][:40]

            header = control.addonInfo('name') + ': Resolving...'

            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(header, '')
            #progressDialog.update(0)

            block = None

            for i in range(len(items)):
                try:
                    if self.rd_hard_stop:
                        break
                    if items[i]['source'] == block: raise Exception()

                    w = workers.Thread(self.sourcesResolve, items[i])
                    w.start()

                    label = re.sub(' {2,}', ' ', str(items[i]['label']))

                    try:
                        if progressDialog.iscanceled(): break
                        progressDialog.update(int((100 / float(len(items))) * i), label)
                    except:
                        progressDialog.update(int((100 / float(len(items))) * i), str(header) + '[CR]' + label)

                    if items[i].get('source').lower() in self.hostcapDict:
                        offset = 60 * 2
                    elif 'torrent' in items[i].get('source').lower():
                        offset = 60 * 2
                    else:
                        offset = 0

                    m = ''

                    for x in range(3600):
                        try:
                            if control.monitor.abortRequested(): return sys.exit()
                            if progressDialog.iscanceled(): return progressDialog.close()
                        except:
                            pass

                        k = control.condVisibility('Window.IsActive(virtualkeyboard)')
                        if k: m += '1'; m = m[-1]
                        if (w.is_alive() == False or x > 30 + offset) and not k: break
                        k = control.condVisibility('Window.IsActive(yesnoDialog)')
                        if k: m += '1'; m = m[-1]
                        if (w.is_alive() == False or x > 30 + offset) and not k: break
                        time.sleep(0.5)


                    for x in range(30):
                        try:
                            if control.monitor.abortRequested(): return sys.exit()
                            if progressDialog.iscanceled(): return progressDialog.close()
                        except:
                            pass

                        if m == '': break
                        if w.is_alive() == False: break
                        time.sleep(0.5)


                    if w.is_alive() == True: block = items[i]['source']

                    if self.url == None: raise Exception()

                    self.selectedSource = items[i]['label']

                    try: progressDialog.close()
                    except: pass

                    control.execute('Dialog.Close(virtualkeyboard)')
                    control.execute('Dialog.Close(yesnoDialog)')
                    return self.url
                except:
                    pass

            try: progressDialog.close()
            except: pass
            del progressDialog

            if self.rd_hard_stop and self.rd_hard_stop_reason in ['429', '451']:
                if self.rd_hard_stop_reason == '429':
                    control.dialog.ok(control.addonInfo('name'), 'Real-Debrid temporarily rate-limited requests (429). Please wait 1-2 minutes and try again.')
                else:
                    control.dialog.ok(control.addonInfo('name'), 'Real-Debrid blocked these magnet transfers (451). Try a different source or a cached item.')

        except:
            try: progressDialog.close()
            except: pass
            del progressDialog
            log_utils.log('sourcesDialog', 1)


    def sourcesDirect(self, items):
        self.rd_hard_stop = False
        self.rd_hard_stop_reason = ''
        original_items = [dict(i.items()) for i in items]

        filter = [i for i in items if i['source'].lower() in self.hostcapDict and not i.get('debrid')]
        items = [i for i in items if not i in filter]

        filter = [i for i in items if i['source'].lower() in self.hostblockDict]# and not i.get('debrid')]
        items = [i for i in items if not i in filter]

        items = [i for i in items if ('autoplay' in i and i['autoplay'] == True) or not 'autoplay' in i]

        # In autoplay, prefer sources most likely to start quickly.
        if control.setting('hosts.mode') == '2':
            cached_torrents = [i for i in items if i.get('source', '').lower() == 'cached torrent']
            uncached_torrents = [i for i in items if 'uncached' in i.get('source', '').lower()]
            debrid_non_uncached = [
                i for i in items
                if i.get('debrid', '') and i.get('source', '').lower() != 'cached torrent' and 'uncached' not in i.get('source', '').lower()
            ]
            direct_sources = [i for i in items if i.get('direct') is True or i.get('local') is True or i.get('official') is True]
            non_debrid_sources = [i for i in items if not i.get('debrid', '') and i not in direct_sources]

            items = cached_torrents + uncached_torrents + debrid_non_uncached + direct_sources + non_debrid_sources

        if not items and original_items:
            log_utils.log('Autoplay prefilters removed all sources, using fallback direct source set')
            items = original_items

        u = None

        header = control.addonInfo('name') + ': Resolving...'

        try:
            control.sleep(1000)

            progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
            progressDialog.create(header, '')
            #progressDialog.update(0)
        except:
            pass

        for i in range(len(items)):
            if self.rd_hard_stop:
                break
            label = re.sub(' {2,}', ' ', str(items[i]['label']))
            try:
                if progressDialog.iscanceled(): break
                progressDialog.update(int((100 / float(len(items))) * i), label)
            except:
                progressDialog.update(int((100 / float(len(items))) * i), str(header) + '[CR]' + label)

            try:
                if control.monitor.abortRequested(): return sys.exit()

                url = self.sourcesResolve(items[i])
                if u == None: u = url
                if not url == None: break
            except:
                pass

        if self.rd_hard_stop and self.rd_hard_stop_reason in ['429', '451']:
            if self.rd_hard_stop_reason == '429':
                control.dialog.ok(control.addonInfo('name'), 'Real-Debrid temporarily rate-limited requests (429). Please wait 1-2 minutes and try again.')
            else:
                control.dialog.ok(control.addonInfo('name'), 'Real-Debrid blocked these magnet transfers (451). Try a different source or a cached item.')

        try: progressDialog.close()
        except: pass
        del progressDialog

        return u


    def errorForSources(self):
        counts = getattr(self, 'last_scrape_counts', None)
        if counts:
            message = 'PROMISE CUSTOM: No Streams Available.\nND:{nd} D:{d} DIR:{dir}\nT:{t} F:{f}'.format(
                nd=counts.get('non_debrid', 0),
                d=counts.get('debrid', 0),
                dir=counts.get('direct', 0),
                t=counts.get('total', 0),
                f=counts.get('filtered', 0),
            )
        else:
            message = 'PROMISE CUSTOM: No Streams Available.'
        control.dialog.ok(control.addonInfo('name'), message)


    def getLanguage(self):
        langDict = {'English': ['en'], 'Greek': ['el'], 'Greek+English': ['el', 'en'], 'French': ['fr'], 'French+English': ['fr', 'en'], 'German': ['de'], 'German+English': ['de','en'], 'Italian': ['it'], 'Italian+English': ['it', 'en'], 'Korean': ['ko'], 'Korean+English': ['ko', 'en'], 'Polish': ['pl'], 'Polish+English': ['pl', 'en'], 'Portuguese': ['pt'], 'Portuguese+English': ['pt', 'en'], 'Russian': ['ru'], 'Russian+English': ['ru', 'en'], 'Spanish': ['es'], 'Spanish+English': ['es', 'en']}
        name = control.setting('providers.lang')
        return langDict.get(name, ['en'])


    def getLocalTitle(self, title, imdb):
        lang = self._getPrimaryLang()
        if lang == 'en' or not lang:
            return title

        if self.content == 'movie':
            t = trakt.getMovieTranslation(imdb, lang)
        else:
            t = trakt.getTVShowTranslation(imdb, lang)

        return t or title


    def getAliasTitles(self, imdb, localtitle):
        lang = self._getPrimaryLang()
        if lang == 'el': # we need country code here, not lang
            lang = 'gr'

        try:
            t = trakt.getMovieAliases(imdb) if self.content == 'movie' else trakt.getTVShowAliases(imdb)
            t = [i for i in t if i.get('country', '').lower() in [lang, '', 'us']] # and i.get('title', '').lower() != localtitle.lower()]
            t = [i for n, i in enumerate(t) if i.get('title') not in [y.get('title') for y in t[n + 1:]]]
            return t
        except:
            return []


    def _getPrimaryLang(self):
        langDict = {'English': 'en', 'Greek': 'el', 'Greek+English': 'el', 'German': 'de', 'German+English': 'de', 'French': 'fr', 'French+English': 'fr', 'Portuguese': 'pt', 'Portuguese+English': 'pt', 'Polish': 'pl', 'Polish+English': 'pl', 'Korean': 'ko', 'Korean+English': 'ko', 'Russian': 'ru', 'Russian+English': 'ru', 'Spanish': 'es', 'Spanish+English': 'es', 'Italian': 'it', 'Italian+English': 'it'}
        name = control.setting('providers.lang')
        lang = langDict.get(name)
        return lang


    def getTitle(self, title):
        title = cleantitle.normalize(title)
        return title


    def getPremColor(self, n):
        if n == '0': n = 'blue'
        elif n == '1': n = 'red'
        elif n == '2': n = 'yellow'
        elif n == '3': n = 'deeppink'
        elif n == '4': n = 'cyan'
        elif n == '5': n = 'lawngreen'
        elif n == '6': n = 'gold'
        elif n == '7': n = 'magenta'
        elif n == '8': n = 'yellowgreen'
        elif n == '9': n = 'white'
        elif n == '10': n = 'black'
        elif n == '11': n = 'crimson'
        elif n == '12': n = 'goldenrod'
        elif n == '13': n = 'powderblue'
        elif n == '14': n = 'deepskyblue'
        elif n == '15': n = 'springgreen'
        elif n == '16': n = 'darkcyan'
        elif n == '17': n = 'aquamarine'
        elif n == '18': n = 'mediumturquoise'
        elif n == '19': n = 'khaki'
        elif n == '20': n = 'darkorange'
        elif n == '21': n = 'none'
        else: n = 'gold'
        return n


    def getConstants(self):
        self.itemProperty = 'plugin.video.thepromise.container.items'

        self.metaProperty = 'plugin.video.thepromise.container.meta'

        self.sourceFile = control.providercacheFile

        externalEnabled = control.setting('external.providers') or 'true'

        from resources.lib import sources
        self.sourceDict = sources.sources()
        self.module_name = 'ThePromise:'

        if externalEnabled == 'true':
            selected = control.setting('external.scraper.module') or '0'
            chains = {
                '0': [
                    ('promisescrapers', 'script.module.promisescrapers', 'PromiseScrapers'),
                    ('viperscrapers', 'script.module.viperscrapers', 'ViperScrapers'),
                    ('cocoscrapers', 'script.module.cocoscrapers', 'CocoScrapers'),
                    ('fenomscrapers', 'script.module.fenomscrapers', 'FenomScrapers')
                ],
                '1': [
                    ('viperscrapers', 'script.module.viperscrapers', 'ViperScrapers'),
                    ('promisescrapers', 'script.module.promisescrapers', 'PromiseScrapers'),
                    ('cocoscrapers', 'script.module.cocoscrapers', 'CocoScrapers'),
                    ('fenomscrapers', 'script.module.fenomscrapers', 'FenomScrapers')
                ],
                '2': [
                    ('cocoscrapers', 'script.module.cocoscrapers', 'CocoScrapers'),
                    ('viperscrapers', 'script.module.viperscrapers', 'ViperScrapers'),
                    ('promisescrapers', 'script.module.promisescrapers', 'PromiseScrapers'),
                    ('fenomscrapers', 'script.module.fenomscrapers', 'FenomScrapers')
                ],
                '3': [
                    ('fenomscrapers', 'script.module.fenomscrapers', 'FenomScrapers'),
                    ('viperscrapers', 'script.module.viperscrapers', 'ViperScrapers'),
                    ('cocoscrapers', 'script.module.cocoscrapers', 'CocoScrapers'),
                    ('promisescrapers', 'script.module.promisescrapers', 'PromiseScrapers')
                ]
            }
            load_chain = chains.get(selected, chains['0'])

            def _ensure_external_paths(addon_id):
                try:
                    paths = []

                    try:
                        addon_path = control.addon(addon_id).getAddonInfo('path')
                        addon_path = control.transPath(addon_path)
                        if addon_path:
                            paths.extend([addon_path, os.path.join(addon_path, 'lib')])
                    except:
                        pass

                    try:
                        addon_root = control.transPath('special://home/addons/%s' % addon_id)
                        addon_lib = control.transPath('special://home/addons/%s/lib' % addon_id)
                        paths.extend([addon_root, addon_lib])
                    except:
                        pass

                    for path in paths:
                        if path and path not in sys.path and os.path.exists(path):
                            sys.path.append(path)
                except:
                    pass

            loaded_modules = []
            for module_import, addon_id, label in load_chain:
                try:
                    _ensure_external_paths(addon_id)
                    scraper_module = importlib.import_module(module_import)
                    ext_sources = scraper_module.sources()
                    if not ext_sources:
                        continue

                    self.sourceDict += ext_sources

                    if not loaded_modules:
                        if addon_id == 'script.module.promisescrapers':
                            package_folder = control.addon(addon_id).getSetting('package.folder')
                            self.module_name = 'PromiseScrapers (%s set):' % package_folder if package_folder != 'Promisescrapers' else 'PromiseScrapers:'
                        elif addon_id == 'script.module.cocoscrapers':
                            self.module_name = 'CocoScrapers:'
                        elif addon_id == 'script.module.fenomscrapers':
                            self.module_name = 'FenomScrapers:'
                        else:
                            self.module_name = 'ViperScrapers:'

                    loaded_modules.append((label, len(ext_sources)))
                    log_utils.log('Loaded external scraper module: %s | providers: %s' % (label, len(ext_sources)))
                except Exception as exc:
                    log_utils.log('Failed loading external scraper module: %s | error: %s' % (label, exc), 1)
                    continue

            if loaded_modules:
                total_external = sum(i[1] for i in loaded_modules)
                active_modules = ', '.join(i[0] for i in loaded_modules)
                log_utils.log('External scraper modules active: %s | total providers: %s' % (active_modules, total_external))
            else:
                log_utils.log('No external scraper module loaded')

        self.hostblockDict = ['youtube.com', 'youtu.be', 'youtube-nocookie.com', 'zippyshare.com', 'facebook.com', 'twitch.tv']

        try:
            self.hostDict = resolveurl.relevant_resolvers(order_matters=True)
            self.hostDict = [i.domains for i in self.hostDict if not '*' in i.domains]
            self.hostDict = [i.lower() for i in reduce(lambda x, y: x+y, self.hostDict)]
            self.hostDict = [x for y,x in enumerate(self.hostDict) if x not in self.hostDict[:y]]
            self.hostDict = [i for i in self.hostDict if not i in self.hostblockDict]
        except:
            self.hostDict = []

        self.hostprDict = ['dailyuploads.net', 'ddl.to', 'ddownload.com', 'dropapk.to', 'drop.download', 'earn4files.com', 'fastclick.to', 'filefactory.com', 'hexupload.net',
                           'mega.io', 'mega.nz', 'multiup.org', 'nitroflare.com', 'nitro.download', 'oboom.com', 'rapidgator.asia', 'rapidgator.net', 'rg.to',
                           'rockfile.co', 'rockfile.eu', 'turbobit.net', 'ul.to', 'uploaded.net', 'uploaded.to', 'uploadgig.com', 'uploadrocket.net', 'usersdrive.com',
                           '1fichier.com', 'alterupload.com', 'cjoint.net', 'desfichiers.com', 'dfichiers.com', 'megadl.fr', 'mesfichiers.org', 'piecejointe.net', 'pjointe.com',
                           'tenvoi.com', 'dl4free.com']

        self.hostcapDict = ['openload.io', 'openload.co', 'oload.tv', 'oload.stream', 'oload.win', 'oload.download', 'oload.info', 'oload.icu', 'oload.fun', 'oload.life', 'openload.pw',
                            'vev.io', 'vidup.me', 'vidup.tv', 'vidup.io', 'vshare.io', 'vshare.eu', 'flashx.tv', 'flashx.to', 'flashx.sx', 'flashx.bz', 'flashx.cc',
                            'hugefiles.net', 'hugefiles.cc', 'thevideo.me', 'streamin.to', 'uptobox.com', 'uptostream.com', 'jetload.net', 'jetload.tv', 'jetload.to']

        # self.sourcecfDict = ['123123movies', '123movieshubz', 'extramovies', 'movie4kis', 'projectfree', 'rapidmoviez', 'rlsbb', 'scenerls', 'timewatch', 'tvmovieflix', '1337x', 'btdb', 'ytsam',
                             # 'animebase', 'filmpalast', 'hdfilme', 'iload', 'movietown', '1putlocker', 'animetoon', 'azmovie', 'cartoonhdto', 'cmoviestv', 'freefmovies', 'ganoolcam', 'projectfreetv', 'putlockeronl',
                             # 'sharemovies', 'solarmoviefree', 'tvbox', 'xwatchseries', '0day', '2ddl', 'doublr', 'pirateiro']


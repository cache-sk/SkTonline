# -*- coding: utf-8 -*-
# Module: default
# Author: cache
# Created on: 6.8.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys, os, io
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import traceback
import json
from bs4 import BeautifulSoup

try:
    from urllib import urlencode
    from urlparse import parse_qsl
    from xbmc import translatePath
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl
    from xbmcvfs import translatePath

_url = sys.argv[0]
_handle = int(sys.argv[1])

_addon = xbmcaddon.Addon()
_session = requests.Session()
_profile = translatePath( _addon.getAddonInfo('profile'))

_useLogin = "true" == _addon.getSetting("uselogin")

BASE_DOMAIN = 'online.sktorrent.eu'
BASE_URL = 'https://'+BASE_DOMAIN
HEADERS={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36', 'Referer': BASE_URL, 'Accept-Encoding': 'identity'}
DEFAULT_PARAMS = ['type=public','t=a']
SEARCH_DEFAULT_PARAMS = ['type=public','t=a','o=mr']
PAGE_PARAM = 'page'
SEARCH_PARAM = 'search_query'
FIRST_PAGE = 1
LAST_WATCHED = "last_watched"
SEARCH_HISTORY = 'search_history'
LAST_SEARCH = "last_search"
MAX_HISTORY_SIZE = 20

CATEGORIES = [
    {'msg':_addon.getLocalizedString(30201), 'url':'/videos'},
    {'msg':_addon.getLocalizedString(30202), 'url':'/videos/dokumenty-cz-sk-dabing'},
    {'msg':_addon.getLocalizedString(30203), 'url':'/videos/dokumenty-cz-sk-titulky'},
    {'msg':_addon.getLocalizedString(30204), 'url':'/videos/filmy'},
    {'msg':_addon.getLocalizedString(30205), 'url':'/videos/filmy-cz-sk'},
    {'msg':_addon.getLocalizedString(30206), 'url':'/videos/filmy-cz-sk-titulky'},
    {'msg':_addon.getLocalizedString(30207), 'url':'/videos/rozpravky-cz-sk-kreslene-animovane'},
    {'msg':_addon.getLocalizedString(30208), 'url':'/videos/hudba'},
    {'msg':_addon.getLocalizedString(30209), 'url':'/videos/ostatni'},
    {'msg':_addon.getLocalizedString(30210), 'url':'/videos/serialy-cz-sk'},
    {'msg':_addon.getLocalizedString(30211), 'url':'/videos/serialy-cz-sk-titulky'},
    {'msg':_addon.getLocalizedString(30212), 'url':'/videos/trailery'}]

LISTS = [
    {'msg':_addon.getLocalizedString(30301),'param':'o=bw'},
    {'msg':_addon.getLocalizedString(30302),'param':'o=mr'},
    {'msg':_addon.getLocalizedString(30303),'param':'o=mv'},
    {'msg':_addon.getLocalizedString(30304),'param':'o=md'},
    {'msg':_addon.getLocalizedString(30305),'param':'o=tr'},
    {'msg':_addon.getLocalizedString(30306),'param':'o=tf'},
    {'msg':_addon.getLocalizedString(30307),'param':'o=lg'}]

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs, 'utf-8'))

def validate_login():
    if _useLogin:
        avs = _addon.getSetting('AVS')
        if avs != '':
            _session.cookies.set('AVS', _addon.getSetting('AVS'), domain=BASE_DOMAIN)
        response = _session.get(BASE_URL+'/user', headers=HEADERS, allow_redirects=False)
        if response.is_redirect and 'Location' in response.headers and 'login' in response.headers['Location']:
            payload = {'username':_addon.getSetting('user'),'password':_addon.getSetting('password'),'submit_login':''}
            response = _session.post(BASE_URL+'/login', headers=HEADERS, data=payload, allow_redirects=False)
            if response.is_redirect:
                _addon.setSetting('AVS',_session.cookies.get_dict()['AVS'])
            else:
                message = _addon.getLocalizedString(30991)
                if sys.version_info[0] <3:
                    import unicodedata
                    message = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore')
                raise Exception(message)

def check_profile():
    if not os.path.exists(_profile):
        os.makedirs(_profile)

def load_last_watched():
    check_profile()
    last_watched = []
    fname = os.path.join(_profile, LAST_WATCHED)
    try:
        with io.open(fname, 'r', encoding='utf8') as file:
            last_data = file.read()
            last_watched = json.loads(last_data)
    except Exception as e:
        xbmc.log('Can\'t load '+LAST_WATCHED+'\n'+str(e),level=xbmc.LOGINFO)
        traceback.print_exc()
    return last_watched

def store_last_watched(href, title, img):
    last_watched = load_last_watched()
    fname = os.path.join(_profile, LAST_WATCHED)
    tpl = {'href':href,'title':title,'img':img}
    if tpl in last_watched:
        last_watched.remove(tpl)
    last_watched = [tpl] + last_watched
    last_watched = last_watched[:MAX_HISTORY_SIZE]
    try:
        with io.open(fname, 'w', encoding='utf8') as file:
            try:
                dump = json.dumps(last_watched).decode('utf8')
            except AttributeError:
                dump = json.dumps(last_watched)
            file.write(dump)
    except Exception as e:
        xbmc.log('Can\'t write '+LAST_WATCHED+'\n'+str(e),level=xbmc.LOGINFO)
        traceback.print_exc()

def load_search():
    history = []
    try:
        if not os.path.exists(_profile):
            os.makedirs(_profile)
    except Exception as e:
        traceback.print_exc()
    
    try:
        with io.open(os.path.join(_profile, SEARCH_HISTORY), 'r', encoding='utf8') as file:
            fdata = file.read()
            try:
                history = json.loads(fdata, "utf-8")
            except TypeError:
                history = json.loads(fdata)
    except Exception as e:
        traceback.print_exc()

    return history
    
def store_search(what):
    if what:
        history = load_search()

        if what in history:
            history.remove(what)

        history = [what] + history
        
        history = history[:MAX_HISTORY_SIZE]

        try:
            with io.open(os.path.join(_profile, SEARCH_HISTORY), 'w', encoding='utf8') as file:
                try:
                    data = json.dumps(history).decode('utf8')
                except AttributeError:
                    data = json.dumps(history)
                file.write(data)
        except Exception as e:
            traceback.print_exc()

def list_categories():
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30000))
    for category in CATEGORIES:
        list_item = xbmcgui.ListItem(label=category['msg'])
        list_item.setInfo('video', {'title': category['msg'],
                                    'genre': category['msg']})
        list_item.setArt({'icon': 'DefaultGenre.png'})
        link = get_url(action='lists', category=category['url'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30005))
    list_item.setInfo('video', {'title': _addon.getLocalizedString(30005),
                                'genre': _addon.getLocalizedString(30005)})
    list_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    link = get_url(search_menu='1')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    
    list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30008))
    list_item.setInfo('video', {'title': _addon.getLocalizedString(30008),
                                'genre': _addon.getLocalizedString(30008)})
    list_item.setArt({'icon': 'DefaultAddonsUpdates.png'})
    link = get_url(last='1')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    
    xbmcplugin.endOfDirectory(_handle)

def list_lists(category):
    catName = None
    for cat in CATEGORIES:
        if cat['url'] == category:
            catName = cat['msg']
            break
            
    if catName is not None:
        xbmcplugin.setPluginCategory(_handle, catName)

    for listt in LISTS:
        list_item = xbmcgui.ListItem(label=listt['msg'])
        list_item.setInfo('video', {'title': listt['msg'],
                                    'genre': listt['msg']})
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = get_url(category=category, order=listt['param'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def process_items(posts, less, more):
    if less is not None:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30003))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = less
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    for post in posts:
        links = post.select('a') 
        if len(links) > 0:
            #print(post)
            img = post.select('img')[0]['src']
            img = img.replace("1.jpg","default.jpg") # experimental - TODO Range:bytes=0-0 => 206 na overenie existencie?
            title_block = post.select('span')[0]
            title_link = links[0]
            href = title_link['href']
            name = title_block.string
            
            list_item = xbmcgui.ListItem(label=name)
            list_item.setInfo('video', {'title': name, 'plot': name})
            list_item.setArt({'thumb': img})
            list_item.setProperty('IsPlayable', 'true')
            link = get_url(href=href,title=name,img=img)
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    if more is not None:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30004))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = more
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

def list_videos(category,order,page=None):
    if page is not None:
        update = True
    else:
        update = False
        page = FIRST_PAGE
    catName = None
    for cat in CATEGORIES:
        if cat['url'] == category:
            catName = cat['msg']
            for lst in LISTS:
                if lst['param'] == order:
                    catName += ' \ ' + lst['msg']
                    break
            break

    if catName is not None:
        xbmcplugin.setPluginCategory(_handle, catName)

    try:
        validate_login()
        data_url = BASE_URL + category + '?' + '&'.join(DEFAULT_PARAMS) + '&' + order + '&' + PAGE_PARAM + '=' + str(page)
        data_raw = _session.get(data_url, headers=HEADERS)
        data_text = data_raw.text
        html = BeautifulSoup(data_text, 'html.parser')
        posts = html.find_all('div', {'class' : 'well well-sm'}, True)

        if page > FIRST_PAGE:
            less = get_url(category=category, order=order, page=page-1)
        else:
            less = None

        nextpage = html.find_all('a', {'class' : 'prevnext'}, True)

        if len(nextpage) > 0:
            more = get_url(category=category, order=order, page=page+1)
        else:
            more = None

        process_items(posts, less, more)

    except Exception as e:
        xbmc.log(str(e),level=xbmc.LOGINFO)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001) + "\n" + str(e))
        xbmcplugin.endOfDirectory(_handle)
        return

    xbmcplugin.endOfDirectory(_handle, updateListing=update)

def list_last_watched():
    xbmcplugin.setPluginCategory(_handle, (_addon.getLocalizedString(30008)))

    lw = load_last_watched()

    for last in lw:
        list_item = xbmcgui.ListItem(label=last["title"])
        list_item.setInfo('video', {'title': last["title"], 'plot': last["title"]})
        list_item.setArt({'thumb': last["img"]})
        list_item.setProperty('IsPlayable', 'true')
        link = get_url(href=last["href"],title=last["title"],img=last["img"])
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    xbmcplugin.endOfDirectory(_handle) #updateListing=update

def search_menu():
    xbmcplugin.setPluginCategory(_handle, (_addon.getLocalizedString(30005)))

    xbmcplugin.setSetting(_handle, LAST_SEARCH, "")

    list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30005))
    list_item.setInfo('video', {'title': _addon.getLocalizedString(30005),
                                'genre': _addon.getLocalizedString(30005)})
    list_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    link = get_url(search='1')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    history = load_search()
    
    for search in history:
        listitem = xbmcgui.ListItem(label=search)
        listitem.setArt({'icon': 'DefaultAddonsSearch.png'})
        #commands = []
        #commands.append(( _addon.getLocalizedString(30213), 'Container.Update(' + get_url(action='search',remove=search) + ')'))
        #listitem.addContextMenuItems(commands)
        xbmcplugin.addDirectoryItem(_handle, get_url(query=search), listitem, True)
    xbmcplugin.endOfDirectory(_handle)

def list_search(query=None, page=None):
    if page is not None:
        update = True
    else:
        update = False
        page = FIRST_PAGE
    xbmcplugin.setPluginCategory(_handle, (_addon.getLocalizedString(30005)))

    try:
        if query is None:
            last = xbmcplugin.getSetting(_handle, LAST_SEARCH)
            if "" != last:
                query = last

        if query is None:
            kb = xbmc.Keyboard('', _addon.getLocalizedString(30005))
            kb.doModal()
            if kb.isConfirmed():
                query = kb.getText()
                store_search(query)
                xbmcplugin.setSetting(_handle, LAST_SEARCH, query)
            else:
                query = ''

        if query:
            validate_login()
            data_url = BASE_URL + '/search/videos?' + '&'.join(SEARCH_DEFAULT_PARAMS) + '&' + urlencode({SEARCH_PARAM:query}, 'utf-8') + '&' + PAGE_PARAM + '=' + str(page)
            data_raw = _session.get(data_url, headers=HEADERS)
            data_text = data_raw.text
            html = BeautifulSoup(data_text, 'html.parser')
            posts = html.find_all('div', {'class' : 'well well-sm'}, True)

            if page > FIRST_PAGE:
                less = get_url(query=query, page=page-1)
            else:
                less = None

            nextpage = html.find_all('a', {'class' : 'prevnext'}, True)

            if len(nextpage) > 0:
                more = get_url(query=query, page=page+1)
            else:
                more = None

            process_items(posts, less, more)

    except Exception as e:
        xbmc.log(str(e),level=xbmc.LOGINFO)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001) + "\n" + str(e))
        xbmcplugin.endOfDirectory(_handle)
        return

    xbmcplugin.endOfDirectory(_handle, updateListing=update)

def streams_and_play(href,title,img):
    try:
        validate_login()
        data_url = BASE_URL + href
        data_raw = _session.get(data_url, headers=HEADERS)
        data_text = data_raw.text
        html = BeautifulSoup(data_text, 'html.parser')
        #title = html.select('h3')[0].string
        plot = html.find_all('div', {'class' : 'm-t-10 overflow-hidden'}, True)[0].string.strip()
        video = html.find_all('video', {'id' : 'video'}, True)[0]
        sources = video.select('source')

        cm = []
        for source in sources:
            cm.append(_addon.getLocalizedString(30006) + " " + source['label'])
        cm.append(_addon.getLocalizedString(30007))

        result = xbmcgui.Dialog().contextmenu(cm)
        if result == -1:
            xbmcplugin.setResolvedUrl(_handle, True, xbmcgui.ListItem())
            return
        elif result == len(sources):
            xbmcgui.Dialog().textviewer(title,plot)
            xbmcplugin.setResolvedUrl(_handle, True, xbmcgui.ListItem())
            return

        source = sources[result]
        list_item = xbmcgui.ListItem(label=source['label'], path=source['src'])
        list_item.setInfo('video', {'title': title, 'plot': plot})
        list_item.setArt({'thumb': video['poster']})
        list_item.setProperty('IsPlayable', 'true')
        link = source['src']
        
        store_last_watched(href, title, img)
        
        xbmcplugin.setResolvedUrl(_handle, True, list_item)
    except IndexError as e:
        xbmc.log(str(e),level=xbmc.LOGINFO)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001) + "\n" + str(e) + "\n" + _addon.getLocalizedString(30992))
        xbmcplugin.endOfDirectory(_handle)
        return
    except Exception as e:
        xbmc.log(str(e),level=xbmc.LOGINFO)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001) + "\n" + str(e))
        xbmcplugin.endOfDirectory(_handle)
        return
        
def router(paramstring):

    #_addon = xbmcaddon.Addon()
    #_session = requests.Session()
    #_profile = translatePath( _addon.getAddonInfo('profile'))
    #_useLogin = "true" == _addon.getSetting("uselogin")

    params = dict(parse_qsl(paramstring))
    if params:
        if 'href' in params:
            streams_and_play(params['href'],params['title'],params['img'])
        elif 'category' in params and 'order' in params and 'page' in params:
            list_videos(params['category'],params['order'],int(params['page']))
        elif 'category' in params and 'order' in params:
            list_videos(params['category'],params['order'])
        elif 'category' in params:
            list_lists(params['category'])
        elif 'query' in params and 'page' in params:
            list_search(params['query'], int(params['page']))
        elif 'query' in params:
            list_search(params['query'])
        elif 'search_menu' in params:
            search_menu()
        elif 'search' in params:
            list_search()
        elif 'last' in params:
            list_last_watched()
        else:
            list_categories()
    else:
        list_categories()

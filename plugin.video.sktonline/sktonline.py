# -*- coding: utf-8 -*-
# Module: default
# Author: cache
# Created on: 6.8.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import traceback
from bs4 import BeautifulSoup

try:
    from urllib import urlencode
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl

_url = sys.argv[0]
_handle = int(sys.argv[1])

_addon = xbmcaddon.Addon()
_session = requests.Session()

BASE_URL = 'https://online.sktorrent.eu'
HEADERS={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36', 'Referer': BASE_URL, 'Accept-Encoding': 'identity'}
DEFAULT_PARAMS = ['type=public','t=a']
SEARCH_DEFAULT_PARAMS = ['type=public','t=a','o=mr']
PAGE_PARAM = 'page'
SEARCH_PARAM = 'search_query'
FIRST_PAGE = 1

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
    link = get_url(search='1')
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
            print(post)
            img = post.select('img')[0]['src']
            title_block = post.select('span')[0]
            title_link = links[0]
            href = title_link['href']
            name = title_block.string
            
            list_item = xbmcgui.ListItem(label=name)
            list_item.setInfo('video', {'title': name, 'plot': name})
            list_item.setArt({'thumb': img})
            link = get_url(href=href)
            is_folder = True
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
        xbmc.log(str(e),level=xbmc.LOGNOTICE)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001), str(e))
        xbmcplugin.endOfDirectory(_handle)
        return

    xbmcplugin.endOfDirectory(_handle, updateListing=update)

def list_search(query=None, page=None):
    if page is not None:
        update = True
    else:
        update = False
        page = FIRST_PAGE
    xbmcplugin.setPluginCategory(_handle, (_addon.getLocalizedString(30005)))

    try:
        if query is None:
            kb = xbmc.Keyboard('', _addon.getLocalizedString(30005))
            kb.doModal()
            if kb.isConfirmed():
                query = kb.getText()
            else:
                query = ''

        if query:
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
        xbmc.log(str(e),level=xbmc.LOGNOTICE)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001), str(e))
        xbmcplugin.endOfDirectory(_handle)
        return

    xbmcplugin.endOfDirectory(_handle, updateListing=update)

def list_streams(href):
    try:
        data_url = BASE_URL + href
        data_raw = _session.get(data_url, headers=HEADERS)
        data_text = data_raw.text
        html = BeautifulSoup(data_text, 'html.parser')

        title = html.select('h3')[0].string
        xbmcplugin.setPluginCategory(_handle, title)

        plot = html.find_all('div', {'class' : 'm-t-10 overflow-hidden'}, True)[0].string

        video = html.find_all('video', {'id' : 'video'}, True)[0]
        sources = video.select('source')
        for source in sources:
            list_item = xbmcgui.ListItem(label=source['label'])
            list_item.setInfo('video', {'title': title, 'plot': plot})
            list_item.setArt({'thumb': video['poster']})
            list_item.setProperty('IsPlayable', 'true')
            link = source['src']
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    except Exception as e:
        xbmc.log(str(e),level=xbmc.LOGNOTICE)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getLocalizedString(30000), _addon.getLocalizedString(30001), str(e))
        xbmcplugin.endOfDirectory(_handle)
        return

    xbmcplugin.endOfDirectory(_handle)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if 'href' in params:
            list_streams(params['href'])
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
        elif 'search' in params:
            list_search()
        else:
            list_categories()
    else:
        list_categories()

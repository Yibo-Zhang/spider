#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from bs4 import BeautifulSoup
import requests
import re
import json
from urllib.request import urlretrieve
import sqlite3


class Instagram(object):
    def __init__(self, user_name):
        self.user_name = user_name
        self.homepage = 'https://www.instagram.com/' + user_name
        self.dir = './' + user_name

    def spider(self, base_url):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            #     'cookie': 'mid=W4VyZwALAAHeINz8GOIBiG_jFK5l; mcd=3; csrftoken=KFLY0ovWwChYoayK3OBZLvSuD1MUL04e; ds_user_id=8492674110; sessionid=IGSCee8a4ca969a6825088e207468e4cd6a8ca3941c48d10d4ac59713f257114e74b%3Acwt7nSRdUWOh00B4kIEo4ZVb4ddaZDgs%3A%7B%22_auth_user_id%22%3A8492674110%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22_auth_user_hash%22%3A%22%22%2C%22_platform%22%3A4%2C%22_token_ver%22%3A2%2C%22_token%22%3A%228492674110%3Avsy7NZ3ZPcKWXfPz356F6eXuSUYAePW8%3Ae8135a385c423477f4cc8642107dec4ecf3211270bb63eec0a99da5b47d7a5b7%22%2C%22last_refreshed%22%3A1535472763.3352122307%7D; csrftoken=KFLY0ovWwChYoayK3OBZLvSuD1MUL04e; rur=FRC; urlgen="{\"103.102.7.202\": 57695}:1furLR:EZ6OcQaIegf5GSdIydkTdaml6QU"'
        }
        html = requests.get(base_url, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        items = soup.find_all('script',
                              {
                                  'type': "text/javascript",
                              })
        pattern = "^window._sharedData[\s\S]*"
        for item in items:
            if (re.match(pattern, item.text, flags=0)):
                links = []
                js_data = json.loads(item.text[21:-1], encoding='utf-8')
                try:
                    edges = \
                        js_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]["edge_sidecar_to_children"][
                            "edges"]
                    for edge in edges:
                        url = edge['node']['display_resources'][2]['src']
                        links.append(url)
                except Exception:
                    url = js_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]['display_resources'][2][
                        'src']
                    # print(url)
                    links.append(url)
        return links

    def _create_folder(self):
        os.makedirs(self.dir, exist_ok=True)

    def dowload_img(self, base_url):
        image_links = self.spider(base_url)
        for link in image_links:
            name = link.split('/')[-1]
            urlretrieve(link, self.dir + '/%s.png' % name)

    def get_img_url(self):
        pass

    def has_next_page(self, xhr_link):
        # 因为默认载入是 十二个页面，这个 函数 是 请求 继续 载入 下个12个页面,这里我改成了40 直到完结
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            # 'cookie': 'mid=W4VyZwALAAHeINz8GOIBiG_jFK5l; mcd=3; csrftoken=KFLY0ovWwChYoayK3OBZLvSuD1MUL04e; ds_user_id=8492674110; sessionid=IGSCee8a4ca969a6825088e207468e4cd6a8ca3941c48d10d4ac59713f257114e74b%3Acwt7nSRdUWOh00B4kIEo4ZVb4ddaZDgs%3A%7B%22_auth_user_id%22%3A8492674110%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22_auth_user_hash%22%3A%22%22%2C%22_platform%22%3A4%2C%22_token_ver%22%3A2%2C%22_token%22%3A%228492674110%3Avsy7NZ3ZPcKWXfPz356F6eXuSUYAePW8%3Ae8135a385c423477f4cc8642107dec4ecf3211270bb63eec0a99da5b47d7a5b7%22%2C%22last_refreshed%22%3A1535472763.3352122307%7D; csrftoken=KFLY0ovWwChYoayK3OBZLvSuD1MUL04e; rur=FRC; urlgen="{\"103.102.7.202\": 57695}:1furLR:EZ6OcQaIegf5GSdIydkTdaml6QU"'
        }
        html = requests.get(xhr_link, headers=headers).text
        js_data = json.loads(html, encoding='utf-8')
        page_info = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']
        flag = page_info['has_next_page']
        cursor = page_info['end_cursor']
        edges = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        page_links = []
        for edge in edges:
            short_code = edge['node']['shortcode']
            page_link = 'https://www.instagram.com/p/' + short_code
            print(page_link)
            page_links.append(page_link)
        print(cursor, flag)
        flag, page_links = self.save_to_database(page_links)
        return cursor, flag, page_links

    def save_to_database(self, link_list):
        flag = False
        new_list = []
        try:
            conn = sqlite3.connect('instagram.db')
        except sqlite3.Error as e:
            print(e)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS %s
               (LINK        text);''' % self.user_name)
        for i in link_list:
            c.execute("SELECT * FROM %s WHERE LINK='%s' " % (self.user_name, i))
            entry = c.fetchone()
            if not entry:
                new_list.append(i)
                c.execute("INSERT INTO {} (LINK) VALUES ('{}')".format(self.user_name, i))
            else:
                print(entry)
        if len(new_list):
            flag = True
        conn.commit()
        conn.close()
        return flag, new_list

    def run(self):
        self._create_folder()
        # 将 homepage的 每个动态的网址 爬下来，以备 下载 图片用
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            #     'cookie': 'mid=W4VyZwALAAHeINz8GOIBiG_jFK5l; mcd=3; csrftoken=KFLY0ovWwChYoayK3OBZLvSuD1MUL04e; ds_user_id=8492674110; sessionid=IGSCee8a4ca969a6825088e207468e4cd6a8ca3941c48d10d4ac59713f257114e74b%3Acwt7nSRdUWOh00B4kIEo4ZVb4ddaZDgs%3A%7B%22_auth_user_id%22%3A8492674110%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22_auth_user_hash%22%3A%22%22%2C%22_platform%22%3A4%2C%22_token_ver%22%3A2%2C%22_token%22%3A%228492674110%3Avsy7NZ3ZPcKWXfPz356F6eXuSUYAePW8%3Ae8135a385c423477f4cc8642107dec4ecf3211270bb63eec0a99da5b47d7a5b7%22%2C%22last_refreshed%22%3A1535472763.3352122307%7D; csrftoken=KFLY0ovWwChYoayK3OBZLvSuD1MUL04e; rur=FRC; urlgen="{\"103.102.7.202\": 57695}:1furLR:EZ6OcQaIegf5GSdIydkTdaml6QU"'
        }
        html = requests.get(self.homepage, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        items = soup.find_all('script',
                              {
                                  'type': "text/javascript",
                              })
        pattern = "^window._sharedData[\s\S]*"
        page_links = []
        for item in items:
            if (re.match(pattern, item.text, flags=0)):
                js_data = json.loads(item.text[21:-1], encoding='utf-8')
                edges = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"][
                    "edges"]
                for edge in edges:
                    shortcode = edge['node']['shortcode']
                    base_url = 'https://www.instagram.com/p/' + shortcode
                    print(base_url)
                    ###################################################################################### download image
                    ## download
                    self.dowload_img(base_url)
                ######################################################################################
                page_info = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"][
                    'page_info']
                cursor = page_info['end_cursor']
                flag = page_info['has_next_page']
                id = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]['id']
                query_hash = 'f2405b236d85e8296cf30347c9f08c2a'
                # print(cursor,flag,id)
                try:
                    while flag:
                        xhr_link = 'https://www.instagram.com/graphql/query/?query_hash=%s&variables={"id":"%s","first":40,"after":"%s"}' % (
                            query_hash, id, cursor)
                        cursor, flag, page_links_sub = self.has_next_page(xhr_link)
                        page_links.extend(page_links_sub)
                        ###################################################################################### download image
                        for page_link_sub in page_links_sub:
                            self.dowload_img(page_link_sub)
                        ######################################################################################################
                except Exception as e:
                    print(e)
                    print('cursor is:' + cursor)
                finally:
                    print(page_links)
        print('FINISHED')
        return page_links


if __name__ == '__main__':
    name_list = ['nn_yun_s','la_vie_enrose__','hyunniestyle','ssovely1024','oxxooi','sexywht','kiligkira']
    user_name = 'la_vie_enrose__'
    for i in name_list:
        ins = Instagram(i)
        ins.run()
        print(i,'is finished')

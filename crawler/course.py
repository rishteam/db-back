import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from .parser import courseHTML_to_dict, get_courseList_link_from_home

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}

# TODO(roy4801): Grab years depends on one's year
ALL_YEAR = ['1081', '1072', '1071', '1062', '1061']

def get_formDataStr(login_res):
    soup = BeautifulSoup(login_res.text, 'html.parser')
    input_tag = soup.select('input#DSIDFormDataStr')
    if input_tag == []:
        return None
    fds_tag = input_tag[0]
    val = fds_tag['value']
    return val

def continue_last_session(r, formDataStr):
    url = 'https://stdntvpn.dev.fju.edu.tw/dana-na/auth/url_A1zClhwC7pm1Qoc7/login.cgi'
    cont_data = {'btnContinue': '%E7%B9%BC%E7%BA%8C%E5%B7%A5%E4%BD%9C%E9%9A%8E%E6%AE%B5', 'FormDataStr': formDataStr}
    res = r.post(url, data=cont_data, headers=headers, allow_redirects=True)
    return res

def login(r, user, passwd):
    url = 'https://stdntvpn.dev.fju.edu.tw/dana-na/auth/url_A1zClhwC7pm1Qoc7/login.cgi'
    login_data = {'tz_offset': '480',
                  'username': user,
                  'password': passwd,
                  'realm': 'Std-SSO',
                  'btnSubmit': '%E7%99%BB%E5%85%A5'}
    login_res = r.post(url, data=login_data,
                       headers=headers, allow_redirects=True)
    return login_res

def logout(r):
    url = 'https://stdntvpn.dev.fju.edu.tw/student/api/,DanaInfo=140.136.251.210+SSLVpnSignOut'
    logout_res = r.get(url, allow_redirects=True)
    return logout_res

# return if fail, home_res
def try_to_login(r, user, passwd):
    # login
    login_res = login(r, user, passwd)
    print('login = {}'.format(login_res.status_code))
    # go to fju web portal
    url = 'https://stdntvpn.dev.fju.edu.tw/student/Account/,DanaInfo=140.136.251.210,SSO=U+sslvpnPost'
    home_res = r.get(url, allow_redirects=True)
    print('home = {}'.format(home_res.status_code))
    # Not succeeded
    fail = False
    if home_res.status_code == 404 and login_res.status_code == 200:
        # Judge if login failed or last session
        fds = get_formDataStr(login_res)
        if fds == None:  # login failed
            fail = True
        else:  # last session
            home_res = continue_last_session(r, fds)
            print('cont = {}'.format(home_res.status_code))
    return fail, home_res

# returns a person's identity
# {
#   'DNP': 'D'/'N'/'P'  # 日間 / 夜間 / 進修
#   'grade': [一二三四]{1}[甲乙]{1}       # 年級
#   'd_abbr': '資工'    # 系所縮寫
#   'name': '鍾秉桓'
# }
def get_person_identity(r, user, passwd):
    # login
    fail, home_res = try_to_login(r, user, passwd)
    if fail:
        print('Failed to login')
        return None
    #
    url = get_courseList_link_from_home(home_res.text)
    res = r.get(url, headers=headers)
    # parse res
    info = {}
    targets = ['LabDayngt1', 'LabDptno1', 'LabStucna1']
    soup = BeautifulSoup(res.text, 'html.parser')
    for t in targets:
        text = soup.select('span#{}'.format(t))[0].contents[0].strip('\n \xa0')
        #
        if t == targets[0]:
            text = text[:1]
            if text == '日':
                info['DNP'] = 'D'
            elif text == '夜':
                info['DNP'] = 'N'
            elif text == '進':
                info['DNP'] = 'P'
        # TODO: Now only support Day. Need more info.
        elif t == targets[1]:
            dep = text[:2]
            gr = text[2:]
            info['d_abbr'] = dep
            info['grade'] = gr
        elif t == targets[2]:
            info['name'] = text
    # Logout
    logout_res = logout(r)
    print('log out = {}'.format(logout_res.status_code))

    return info

def get_total_point(r, user, passwd):
    pass

def get_course_list_HTML_by_year(r, year, course_res):
    assert year # Must Not None
    #
    post_url = 'https://stdntvpn.dev.fju.edu.tw/CheckSelList/,DanaInfo=estu.fju.edu.tw+HisListNew.aspx'
    soup = BeautifulSoup(course_res.text, 'html.parser')
    li_input = soup.find_all('input')
    for _ in range(2):
        li_input.pop()
    post_data = {}
    for it in li_input:
        post_data[it['id']] = it['value']
    post_data['__EVENTTARGET'] = 'DDL_YM'
    post_data['__EVENTARGUMENT'] = ''
    post_data['__LASTFOCUS'] = ''
    post_data['DDL_YM'] = year

    tmp = {
        'Referer': 'https://stdntvpn.dev.fju.edu.tw/CheckSelList/,DanaInfo=estu.fju.edu.tw+HisListNew.aspx',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    post_headers = {**headers, **tmp}
    course_year_res = r.post(post_url, data=post_data, headers=post_headers,
                             allow_redirects=True)
    return course_year_res.text

# year = ['1081', '1072' ...]
def get_course_list_HTML(r, user, passwd, year=None):
    fail, home_res = try_to_login(r, user, passwd)
    if fail:
        print('')
        return None

    # Get course list HTML
    url = get_courseList_link_from_home(home_res.text)
    course_res = r.get(url, allow_redirects=True)
    print('Course list = {}'.format(course_res.status_code))

    # Get course list HTML by list `year`
    if year == None:
        year = [ALL_YEAR[0]]
    elif not isinstance(year, list):
        raise ValueError('The argument `year` must be a list or None')
    res = {}
    for y in year:
        res[y] = get_course_list_HTML_by_year(r, y, course_res)

    # Logout
    logout_res = logout(r)
    print('log out = {}'.format(logout_res.status_code))

    return res

# return dict which key is semester (e.g. 1081)
# and value is the course list of that semester
# e.g.
#   {
#       '1081' : [{}, ...],
#       '1072' : [{}, ...],
#       ...
#   }
def get_course_list(user, passwd, req=None, year=None):
    # TODO: Keep this session
    r = req if req else requests.Session()

    if year == None:
        year = [ALL_YEAR[0]]
    elif not isinstance(year, list):
        raise ValueError('The argument `year` must be a list or None')
    # TODO: impl the parse and return them
    html_dic = get_course_list_HTML(r, user, passwd, year)
    for k, v in html_dic.items():
        html_dic[k] = courseHTML_to_dict(v)

    return html_dic

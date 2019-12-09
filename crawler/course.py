import requests
from bs4 import BeautifulSoup

from .parser import courseHTML_to_dict

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}

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

def get_current_course_list_HTML(r, user, passwd):
    fail, home_res = try_to_login(r, user, passwd)
    if fail:
        print('')
        return None
    # find the link to Course List
    soup = BeautifulSoup(home_res.text, 'html.parser')
    res = soup.select('a#systemID_15') # 選課清單
    # Get course list HTML
    url = res[0]['href']
    course_res = r.get(url, allow_redirects=True)
    print('Course list = {}'.format(course_res.status_code))

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
    post_data['DDL_YM'] = '1071'

    print(post_data)

    tmp = {
        'Referer': 'https://stdntvpn.dev.fju.edu.tw/CheckSelList/,DanaInfo=estu.fju.edu.tw+HisListNew.aspx',
        'Content-Type': 'application/x-www-form-urlencoded'
        # 'Content-Type': 'application/form-data'
    }
    post_headers = {**headers, **tmp}
    res = r.post(url, data=post_url, headers=post_headers,
                 allow_redirects=True)

    print(res.history[0].url)
    print(res.url)

    with open('/home/roy4801/Desktop/proj/database/login/1072_res_1.html', 'w') as f:
        f.write(BeautifulSoup(res.text, 'html.parser').prettify())

    # Logout
    logout_res = logout(r)
    print('log out = {}'.format(logout_res.status_code))

    return course_res.text

def get_currnet_course_list(user, passwd, req=None):
    # TODO: Keep this session
    r = req if req else requests.Session()
    html = get_current_course_list_HTML(r, user, passwd)
    return courseHTML_to_dict(html) if html != None else None

import requests
from bs4 import BeautifulSoup

from crawler.parser import courseHTML_to_dict

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}

def get_formDataStr(login_res):
    soup = BeautifulSoup(login_res.text, 'html.parser')
    fds_tag = soup.select('input#DSIDFormDataStr')[0]
    val = fds_tag['value']
    return val

def continue_last_session(r, formDataStr):
    url = 'https://stdntvpn.dev.fju.edu.tw/dana-na/auth/url_A1zClhwC7pm1Qoc7/login.cgi'
    cont_data = {'btnContinue': '%E7%B9%BC%E7%BA%8C%E5%B7%A5%E4%BD%9C%E9%9A%8E%E6%AE%B5', 'FormDataStr': formDataStr}
    res = r.post(url, data=cont_data, headers=headers, allow_redirects=True)
    return res

def get_current_course_list_HTML(r, user, passwd):
    # login
    url = 'https://stdntvpn.dev.fju.edu.tw/dana-na/auth/url_A1zClhwC7pm1Qoc7/login.cgi'
    login_data = {'tz_offset': '480',
                'username': user,
                'password': passwd,
                'realm': 'Std-SSO',
                'btnSubmit': '%E7%99%BB%E5%85%A5'}
    login_res = r.post(url, data=login_data, headers=headers, allow_redirects=True)
    print('login = {}'.format(login_res.status_code))
    # go to fju web portal
    url = 'https://stdntvpn.dev.fju.edu.tw/student/Account/,DanaInfo=140.136.251.210,SSO=U+sslvpnPost'
    home_res = r.get(url, allow_redirects=True)
    print('home = {}'.format(home_res.status_code))
    # if it has last session
    if home_res.status_code == 404 and login_res.status_code == 200:
        fds = get_formDataStr(login_res)
        home_res = continue_last_session(r, fds)
        print('cont = {}'.format(home_res.status_code))
    # find the link to Course List
    soup = BeautifulSoup(home_res.text, 'html.parser')
    res = soup.select('a#systemID_15') # 選課清單

    # Get course list HTML
    url = res[0]['href']
    course_res = r.get(url, allow_redirects=True)
    print('Course list = {}'.format(course_res.status_code))
    # Logout
    url = 'https://stdntvpn.dev.fju.edu.tw/student/api/,DanaInfo=140.136.251.210+SSLVpnSignOut'
    logout_res = r.get(url, allow_redirects=True)
    print('log out = {}'.format(logout_res.status_code))

    return course_res.text

def get_currnet_course_list(user, passwd):
    r = requests.Session()
    html = get_current_course_list_HTML(r, user, passwd)
    return courseHTML_to_dict(html)

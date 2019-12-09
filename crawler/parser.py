from bs4 import BeautifulSoup

th = [None, 'mark', 'year', 'sem', 'code', 'main_code', 'department', 'subject', 'point', 'cat', 'stu_cat', 'sem_th', 'teacher', 'which_day', 'week', 'period', 'classroom', 'cfield', 'note']
# for courseHTML_to_dict()
time_name = ['which_day', 'week', 'period', 'classroom']
last_name = ['cfield', 'note']

def courseHTML_to_dict(html):
    soup = BeautifulSoup(html, 'html.parser')
    course = soup.select('table#GV_NewSellist')[0]
    whole_table = course.find_all('tr', recursive=False)

    data_table = [whole_table[i] for i in range(1, len(whole_table))]

    course = []
    for row in data_table:
        dic = {}
        tds = row.find_all('td', recursive=False)
        for i in range(1, 13): # [1,12]
            dic[th[i]] = tds[i].contents[0].strip('\n \xa0')
        #
        dic['time'] = []
        idx = 13
        for i in range(3):
            dic['time'].append({})
            for j in range(4):
                content = tds[idx+4*i+j].contents[0].strip('\n \xa0')
                if content == '':
                    dic['time'].pop()
                    break
                # dic['time']    -> [{..}, ...]
                # dic['time'][i] -> {'which_day': xxx, ...}
                dic['time'][i][time_name[j]] = tds[idx+4*i+j].contents[0].strip('\n \xa0')
        #
        idx = 17
        for i in range(25, 27): # [25, 26]
            dic[th[idx-i+25]] = tds[i].contents[0].strip('\n \xa0')
        # print(dic)
        course.append(dic)
    return course

def courseHTML_to_dict_old(html):
    soup = BeautifulSoup(html, 'html.parser')
    res = soup.select('div#Panel2')

    b = res[0].select('b')
    ts = b[0].find_all('table', recursive=False)
    ts.pop()

    course = ts[0].find_all('tr', recursive=False)[4].select('table')[0]
    whole_table = course.find_all('tr', recursive=False)

    # Collect oly the course (ignore the table head)
    rt = []
    clist = []
    for i in range(1, len(whole_table)):
        clist.append(whole_table[i])

    # Get courses
    for it in clist:
        row = it.find_all('td', recursive=False)
        c = {}
        # the first 13 attributes
        for i in range(13):
            k, v = th[i], row[i].font.contents[0].strip('\xa0\n ')
    #        print('{} -> \'{}\''.format(k, v))
            if k != None:
                c[k] = v
        # time segment (4 attributes repeat 3 times)
        idx = 13
        time = []
        for a in range(3):
            p = {}
            for b in range(4):
                content = row[i+4*a+b].font.contents[0].strip('\xa0\n ')
                if content != '':
                    p[th[i+b]] = content
            if p != {}:
                time.append(p)
        # the last 2 attributes
        idx += 4
        for i in range(idx, idx+2):
            k, v = th[i], row[i+8].font.contents[0].strip('\xa0\n ')
            c[k] = v
        rt.append(c)
    return rt

# find the link to Course List
def get_courseList_link_from_home(html):
    soup = BeautifulSoup(html, 'html.parser')
    res = soup.select('a#systemID_15')  # 選課清單
    if res == []:
        raise RuntimeError('Cannot find any link to course list')
    return res[0]['href']

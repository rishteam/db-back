from . import parser, course

# import json
import hashlib
import requests
import json

testacc = [('406262515', 'aa987654321')
        , ('406262319', 'aa987654321')
        , ('406262084', 'aa987654321')]
CUR = 0

if __name__ == '__main__':
    r = requests.Session()

    info = course.get_person_identity(r, *testacc[1])
    print(info)
    # cur_hash = hashlib.md5(json_li).hexdigest()
    # print(cur_hash)

    # print(bytes(json.dumps(d), 'ascii').decode('unicode-escape'))

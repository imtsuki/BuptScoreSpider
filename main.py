#!/usr/bin/python
import io
import sys
import time
import json
import requests
import getopt
import getpass
from requests_html import HTML
from PIL import Image
import pytesseract
from json import encoder

encoder.FLOAT_REPR = lambda o: format(o, '.1f')

username = None
password = None
prefix = 'http://jwxt.bupt.edu.cn/'
cookies = None

json_filename = './out.json'
captcha_recognition = True


def recognize_captcha():
    captcha_response = requests.get(prefix + 'validateCodeAction.do?random=', cookies=cookies)
    captcha_origin = Image.open(io.BytesIO(captcha_response.content))
    result = ''
    if captcha_recognition:
        code = pytesseract.image_to_string(captcha_origin)
        if len(code) == 4:
            result = code
        captcha_grey = captcha_origin.convert('L')
        code_grey = pytesseract.image_to_string(captcha_grey)
        if len(code_grey) == 4:
            result = code_grey
        threshold = 140
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)
        captcha_binary = captcha_grey.point(table, '1')
        code_binary = pytesseract.image_to_string(captcha_binary)
        if len(code_binary) == 4:
            result = code_binary
    else:
        captcha_origin.show()
        result = input('验证码: ')
    return result


def login():
    success = False
    try_time = 0
    sleep_time = 0.05
    max_sleep_time = 0.8
    while not success:
        time.sleep(sleep_time)
        try_time += 1
        print('尝试登录:', try_time)
        code = recognize_captcha()
        if len(code) != 4:
            continue
        post_data = {'type': 'sso', 'zjh': username, 'mm': password, 'v_yzm': code}
        login_response = requests.post(prefix + 'jwLoginAction.do', data=post_data, cookies=cookies)
        if login_response.text.find('密码不正确') != -1:
            print('密码不正确. ')
            sys.exit(1)
        if login_response.text.find('证件号不存在') != -1:
            print('用户名不存在. ')
            sys.exit(1)
        if login_response.text.find('学分制综合教务') != -1:
            success = True
        if sleep_time < max_sleep_time:
            sleep_time *= 2
    print('登录成功. ')


def query(operation):
    query_response = requests.get(prefix + 'gradeLnAllAction.do?type=ln&oper=' + operation, cookies=cookies)
    html = HTML(html=query_response.text)
    query_response = requests.get(prefix + html.find('iframe', first=True).attrs['src'], cookies=cookies)
    return HTML(html=query_response.text)


def to_float(s):
    try:
        return float(s)
    except ValueError:
        return s


def parse_table_fa(table):
    keys = []
    for i in range(1, 9):
        keys.append(table.xpath('table[last()]/tr/td/table[1]/thead/tr/th[' + str(i) + ']')[0].text)
    result = []
    last_course = table.xpath('table[last()]/tr/td/table[1]/tr[last()]')[0]
    course_index = 1
    while True:
        current_course = table.xpath('table[last()]/tr/td/table[1]/tr[' + str(course_index) + ']')[0]
        values = []
        for i in range(1, 9):
            if i == 5 or i == 7:
                values.append(to_float(current_course.xpath('tr/td[' + str(i) + ']')[0].text))
            else:
                values.append(current_course.xpath('tr/td[' + str(i) + ']')[0].text)
        result.append(dict(zip(keys, values)))
        if current_course.element == last_course.element:
            break
        course_index += 1
    return result


def usage():
    print('使用帮助: ' + sys.argv[0] + ' [选项...] <用户名> <密码>')
    print(' -o, --output <file> 指定输出文件')
    print(' -c, --disable-captcha-recognition 手动输入验证码')
    print(' -h, --help          查看帮助')


if __name__ == '__main__':
    try:
        options, args = getopt.getopt(sys.argv[1:], 'hco:', ['help', 'disable-captcha-recognition', 'output='])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(1)

    for o, a in options:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-o', '--output'):
            json_filename = a
        elif o in ('-c', '--disable-captcha-recognition'):
            captcha_recognition = False

    if len(args) >= 2:
        username = args[0]
        password = args[1]
    elif len(args) == 1:
        username = args[0]
        password = getpass.getpass('密  码: ')
    else:
        username = input('用户名: ')
        password = getpass.getpass('密  码: ')
    try:
        response = requests.get(prefix)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    cookies = response.cookies
    login()
    '''
    qb              sx              fa              bjg
    全部及格成绩查询  按课程属性成绩查询 按方案成绩查询    不及格成绩查询
    '''
    json_data = parse_table_fa(query('fa'))

    with io.open(json_filename, 'w', encoding='utf8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    print('输出文件已写入 ' + json_filename + '.')

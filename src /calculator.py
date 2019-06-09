#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 13 21:31:32 2018

@author: Julius Song
"""

import requests
from bs4 import BeautifulSoup

import getpass


def getScoreList(student_id, password):
    '''Retrive and parse score page from student affiar office website.
    
    Args:
        student_id: A 'str' of student id.
        password: A 'str' of password.
        
    Returns:
        A soup object of parsed html page with all scores if no connection error, else None.
    '''
    
    try:
        login_url = 'https://login.bit.edu.cn/cas/login?service=http%3A%2F%2Fjwms.bit.edu.cn%2F'
        score_url = 'http://jwms.bit.edu.cn/jsxsd/kscj/cjcx_list'
        header = {'user-agent': 'Mozilla/5.0'} #Not necessary
        
        session = requests.Session()
        login_response = session.get(login_url, headers = header, timeout = 10)
        
        soup_login = BeautifulSoup(login_response.text, 'html.parser')
        
        lt = soup_login.find(name = 'input', attrs = {'name': 'lt'}).attrs['value']
        execution = soup_login.find(name = 'input', attrs = {'name': 'execution'}).attrs['value']
        eventid = soup_login.find(name = 'input', attrs = {'name': '_eventId'}).attrs['value']
        rmshown = soup_login.find(name = 'input', attrs = {'name': 'rmShown'}).attrs['value']
        
        payload = {'username': student_id, 'password': password, 'lt': lt, 'execution': execution, 
                   '_eventId': eventid, 'rmShown': rmshown}
        
        session.post(login_url, headers = header, data = payload, timeout = 10)
        score_response = session.get(score_url, headers = header, timeout = 10)
        
        return BeautifulSoup(score_response.text, 'html.parser')
    
    except:
        return 


def parseScoreInfo(intr, score):
    '''Parse score info.
    
    Args:
        intr: An intertor encoding score items of soup object.
        score: A 'list', score info of every term.
    '''
    
    for tr in intr:
        try:
            tds = tr('td')
            course_term = tds[1].text
            # term = actual term - 1
            term = (int(course_term[:4]) - admission_year)*2 + int(course_term[-1]) - 1
            course_info = {'score': float(tds[4].text), 'credit': float(tds[6].text)}
            score[term].append(course_info)
        except ValueError:
            mapping = {'优秀': 95, '良好': 85, '中等': 75, '合格': 60, '不合格': 0}
            if tds[4].text in mapping:
                course_info = {'score': float(mapping[tds[4].text]), 'credit': float(tds[6].text)}
                score[term].append(course_info)            
        except:
            continue


def calAverageScore(score, count, ave_all, credit):    
    '''Calculate average score of a certain term.
    
    Args:
        score: A 'list' containing score info of a term.
        count: An 'int', number of courses taken so far.
        ave_all: A 'float', all score*credit added.
        credit: A 'float', credit aquired so far.
        
    Returns:
        ave/cre_temp: A 'float', GPA of a term.
        count: An 'int', number of courses taken so far, including this term.
        ave_all: A 'float', all score*credit added, including this term.
        credit: A 'float', credit aquired so far, including this term.
    '''
    # score*credit added
    ave = 0
    # Course count of a term.
    count_temp = 0
    # Credit count of a term.
    cre_temp = 0
    
    for course in score:
        ave += course['score'] * course['credit']
        cre_temp += course['credit']
        count_temp += 1
        
    ave_all += ave
    count += count_temp
    credit += cre_temp
    
    try:
        return ave/cre_temp, count, ave_all, credit
    except:
        # If term not applicable.
        return 0, count, ave_all, credit


def calPercentage(score, grade):
    '''Calculate grade percentage.
    
    Args:
        score: A 'list' of course info.
        grade: A 'dict' of grade percentage.
    '''
    
    for course in score:
         grade['excellent'] += len(list(filter(lambda x: x>=90, [course['score']])))
         grade['good'] += len(list(filter(lambda x: 80<=x<90, [course['score']])))
         grade['fair'] += len(list(filter(lambda x: 70<=x<80, [course['score']])))
         grade['pass'] += len(list(filter(lambda x: 60<=x<70, [course['score']])))
         grade['fail'] += len(list(filter(lambda x: x<60, [course['score']])))


if __name__ == '__main__':
    
    # Print header.
    print('\n' + '*'*30 + '\n')
    print('BIT GPA Calculator')
    print('\n' + '*'*30)

    # Input student id & password.
    while True:
        student_id = input('\nStudent ID: ')
        print('\nReminder: password input is invisible.\n')
        password = getpass.getpass('Password: ')
        
        if len(student_id) == 10:
            break
        else:
            print('\nInvalid Student ID.')
            print('\n' + '-'*30)
            
    admission_year = int(student_id[2:6])
    
    # Retrive score page.
    soup_score = getScoreList(student_id, password)
    
    # Score details of 8 terms
    score = [[] for i in range(8)]
    # Average score of 8 terms each
    ave = [0 for i in range(8)]
    # Average score of all terms
    ave_all = 0 
    # Number of courses taken of 8 terms
    count = 0
    # Total credits acquired
    credit = 0 
    # Grade percentage
    grade = {'excellent': 0, 'good': 0, 'fair': 0, 'pass': 0, 'fail': 0}
    
    # Print segment.
    print('\n'+ '-'*30 + '\n')
    
    try:
        
        parseScoreInfo(soup_score.find('table', attrs = {'id': 'dataList'}).children, score)
        
        # Parse score of each term.
        for i in range(8):
            ave[i], count, ave_all, credit = calAverageScore(score[i], count, ave_all, credit)
            calPercentage(score[i], grade)
            
        ave_all /= credit
        
        # Display results.  
        print('GPA: {:.3f}\n'.format(ave_all))
        print('Credits acquired: {}\n'.format(credit))
        print('-'*30 + '\n')
        print('Grade percentage:\n')
        print('''Excellent (score>=90): {:.2%}
Good (80<=score<90): {:.2%}
Fair (70<=score<80): {:.2%}
Pass (60<=score<70): {:.2%}
Fail (score<60): {:.2%}\n'''.format(grade['excellent']/count, grade['good']/count, grade['fair']/count, 
                                grade['pass']/count, grade['fail']/count))
        print('-'*30 + '\n')
        print('GPA of each term as followed:\n')
        for i in range(8):
            if not len(score[i]) == 0:
                print('Term {}: {:.2f}'.format(i+1, ave[i]))
            
    except:
        print('Student id does not exist, incorrect password, or Internet connection error.')
    
    # Print tail.
    print('\n' + '*'*30 + '\n')
    print('repo: github.com/julius-song/BIT-GPA-Calculator' + '\n')

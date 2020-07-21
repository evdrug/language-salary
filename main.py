from itertools import count
import os
from itertools import count

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable

list_language = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'C',
    'Go',
]


def fetch_vacancies_hh_ru(language):
    params = {
        'specialization': 1.221,
        'period': 30,
        'per_page': 100,
        'area': 2,
        'text': f'Программист {language}',
    }
    url = 'https://api.hh.ru/vacancies/'
    items = []
    for page in count():
        params['page'] = page
        response = requests.get(url, headers={'User-Agent': 'test'}, params=params)
        response.raise_for_status()
        items += response.json()['items']
        if page + 1 >= response.json().get('pages'):
            break
    return items


def fetch_vacancies_sjob(language):
    params = {
        'town': 4,
        'catalogues': 48,
        'period': 30,
        'keywords[0][srws]': 1,
        'keywords[0][keys]': language,
    }

    headers = {
        'X-Api-App-Id': token
    }

    url = 'https://api.superjob.ru/2.0/vacancies/'

    items = []
    for page in count():
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        items += response.json().get('objects', [])
        if not response.json().get('more'):
            break
    return items


def get_average_salary(vacancies, func):
    salaries = []
    for vacancy in vacancies:
        average_salary = func(vacancy)
        if average_salary:
            salaries.append(average_salary)
    return {
        "vacancies_found": len(vacancies),
        "vacancies_processed": len(salaries),
        "average_salary": int(sum(salaries) / len(salaries)) if salaries else 0
    }


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    elif not salary_from:
        average = int(salary_to) * 0.8
    elif not salary_to:
        average = int(salary_from) * 1.2
    else:
        average = (int(salary_from) + int(salary_to)) / 2
    return int(average)


def predict_rub_salary_hh(vacancy):
    if not vacancy.get('salary') or vacancy['salary'].get('currency') != 'RUR':
        return None
    return predict_salary(vacancy['salary'].get('from'), vacancy['salary'].get('to'))


def predict_rub_salary_for_sj(vacancy):
    if vacancy.get('payment') is None or vacancy.get('currency') != 'rub':
        return None
    return predict_salary(vacancy.get('payment_from'), vacancy.get('payment_to'))


def generate_table_lang(title, data):
    header = ['Языки программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    rows_data = [[name, stat['vacancies_found'], stat['vacancies_processed'], stat['average_salary']]
                 for name, stat in data.items()]
    table_instance = AsciiTable([header] + rows_data, title)
    return table_instance.table


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('JOBS_TOKEN')
    try:
        hh = {language: get_average_salary(fetch_vacancies_hh_ru(language), predict_rub_salary_hh)
              for language in list_language}
    except requests.exceptions.HTTPError as e:
        print("Ошибка запроса HeadHunter", e)
    else:
        print(generate_table_lang('HeadHunter Moscow', hh))

    print()

    try:
        jb = {language: get_average_salary(fetch_vacancies_sjob(language), predict_rub_salary_for_sj)
              for language in list_language}
    except requests.exceptions.HTTPError as e:
        print("Ошибка запроса SuperJobs", e)
    else:
        print(generate_table_lang('SuperJob Moscow', jb))

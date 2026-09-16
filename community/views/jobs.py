import requests
from django.shortcuts import render
from ..models import Board  # 사이드바 메뉴 렌더링을 위해 Board 모델 불러오기

# 승인 전: True (더미 데이터) / 승인 후: False (실제 API)
USE_MOCK_DATA = True
SARAMIN_API_KEY = "YOUR_API_KEY_HERE"

def job_recommendations(request):
    keyword = request.GET.get('q', 'Python').strip()
    jobs = []

    if USE_MOCK_DATA:
        jobs = [
            {
                'title': '[국비추천] 백엔드 Python/Django 개발자 채용 (신입/경력)',
                'company': '(주)에이아이기술',
                'url': 'https://www.saramin.co.kr',
                'location': '서울 강남구',
                'job_type': '정규직',
                'experience': '신입/경력',
                'expiration_date': '2026-10-15',
            },
            {
                'title': 'React & Django 풀스택 개발자 모집',
                'company': '스타트업랩',
                'url': 'https://www.saramin.co.kr',
                'location': '경기 성남시 분당구',
                'job_type': '정규직',
                'experience': '경력무관',
                'expiration_date': '상시채용',
            },
            {
                'title': '웹 파이프라인 및 데이터 백엔드 엔진니어',
                'company': '데이터솔루션즈',
                'url': 'https://www.saramin.co.kr',
                'location': '서울 서초구',
                'job_type': '정규직',
                'experience': '신입',
                'expiration_date': '2026-09-30',
            },
        ]
    else:
        url = "https://oapi.saramin.co.kr/job-search"
        params = {
            'access-key': SARAMIN_API_KEY,
            'keywords': keyword,
            'count': 12,
            'sort': 'rc',
            'fields': 'expiration-date'
        }
        headers = {'Accept': 'application/json'}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                raw_jobs = data.get('jobs', {}).get('job', [])
                if isinstance(raw_jobs, dict):
                    raw_jobs = [raw_jobs]
                for item in raw_jobs:
                    jobs.append({
                        'title': item.get('position', {}).get('title'),
                        'company': item.get('company', {}).get('detail', {}).get('name'),
                        'url': item.get('url'),
                        'location': item.get('position', {}).get('location', {}).get('name'),
                        'job_type': item.get('position', {}).get('job-type', {}).get('name'),
                        'experience': item.get('position', {}).get('experience-level', {}).get('name'),
                        'expiration_date': item.get('expiration-timestamp'),
                    })
        except Exception as e:
            print(f"[API Error] {e}")

    # base.html 랜더링 시 필요한 사이드바 게시판 목록 데이터 동기화[cite: 11]
    nav_boards = Board.objects.all()

    return render(request, 'jobs/recommend_list.html', {
        'jobs': jobs,
        'keyword': keyword,
        'nav_current': 'jobs',
        'nav_boards': nav_boards,  # 사이드바 템플릿용 변수 추가
    })
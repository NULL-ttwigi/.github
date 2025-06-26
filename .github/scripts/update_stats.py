#!/usr/bin/env python3
import requests
import re
import os
from datetime import datetime, timedelta

# GitHub API 설정
GITHUB_TOKEN = os.getenv('CUSTOM_GITHUB_TOKEN')
if GITHUB_TOKEN:
    HEADERS = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
else:
    print("⚠️  CUSTOM_GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
    print("   로컬 테스트 시에는 GitHub API 호출이 제한될 수 있습니다.")
    HEADERS = {
        'Accept': 'application/vnd.github.v3+json'
    }

# 조직 및 멤버 정보
ORG_NAME = 'NULL-ttwigi'  
MEMBERS = {
    'girlwcode': '안예린',
    'heheelee': '이현희', 
    'mini-u': '유성민'
}
# 개인 티어 (수동 업데이트 필요)
TIERS = {
    'girlwcode': '-', 
    'heheelee': '-', 
    'mini-u': '-' 
}

# 문제 풀이 커밋 메시지 패턴
PROBLEM_SOLVE_PATTERNS = [
    r'\[BOJ-\d+\]',  # [BOJ-0001 or BOJ-1] 형태
    r'\[Programmers\]',  # [Programmers] 형태
    r'\[LC-\d+\]',  # [LC-0001 or LC-1] 형태
    r'\[SWEA\]',  # [SWEA] 형태
]

def is_problem_solve_commit(commit_message):
    """커밋 메시지가 문제 풀이인지 확인합니다."""
    for pattern in PROBLEM_SOLVE_PATTERNS:
        if re.search(pattern, commit_message, re.IGNORECASE):
            return True
    return False

def get_org_repos():
    """조직의 퍼블릭 레포지토리를 가져옵니다."""
    repos = []
    page = 1
    
    print(f"🔍 조직 '{ORG_NAME}'의 퍼블릭 레포지토리를 조회합니다...")
    
    while True:
        # type=public으로 설정하여 퍼블릭 레포지토리만 가져오기
        url = f'https://api.github.com/orgs/{ORG_NAME}/repos?type=public&page={page}&per_page=100'
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"❌ Error fetching repos: {response.status_code}")
            print(f"   URL: {url}")
            print(f"   Response: {response.text}")
            if response.status_code == 401:
                print("💡 해결방법: GitHub Personal Access Token이 필요합니다.")
                print("   1. GitHub Settings > Developer settings > Personal access tokens에서 토큰 생성")
                print("   2. 필요 권한: repo, read:org, user")
                print("   3. 환경변수 CUSTOM_GITHUB_TOKEN에 토큰 설정")
            break
            
        page_repos = response.json()
        if not page_repos:
            break
            
        repos.extend(page_repos)
        print(f"   📄 페이지 {page}: {len(page_repos)}개 레포지토리 발견")
        page += 1
    
    print(f"✅ 총 {len(repos)}개의 퍼블릭 레포지토리를 찾았습니다:")
    for repo in repos:
        owner = repo.get('owner', {}).get('login', 'unknown')
        name = repo.get('name', 'unknown')
        print(f"   - {owner}/{name} (🌐 public)")
    
    return repos

def get_user_repositories(username, org_repos):
    """해당 사용자의 레포지토리들을 식별합니다."""
    try:
        user_repos = []
        
        # 방법 1: 레포지토리 이름이 사용자명과 일치하는 것
        name_match_repos = [repo for repo in org_repos if repo.get('name') == username]
        user_repos.extend(name_match_repos)
        
        # 방법 2: 최초 커밋 작성자가 해당 사용자인 레포지토리
        for repo in org_repos:
            repo_name = repo.get('name')
            if repo_name in ['.github'] or repo in user_repos:  # 시스템 레포나 이미 추가된 레포는 제외
                continue
                
            try:
                # 최초 커밋 확인
                url = f'https://api.github.com/repos/{ORG_NAME}/{repo_name}/commits'
                params = {'per_page': 1, 'sha': 'main'}
                response = requests.get(url, headers=HEADERS, params=params)
                
                if response.status_code == 200:
                    commits = response.json()
                    if commits:
                        first_commit_author = commits[0].get('author', {}).get('login', '')
                        if first_commit_author == username:
                            user_repos.append(repo)
            except Exception as e:
                print(f"   {repo_name}: 최초 커밋 확인 실패 - {e}")
                continue
        
        print(f"🔍 {username}의 레포지토리 식별:")
        print(f"   이름 매칭: {[repo.get('name') for repo in name_match_repos]}")
        print(f"   최초 커밋 매칭: {[repo.get('name') for repo in user_repos if repo not in name_match_repos]}")
        print(f"   총 레포지토리: {[repo.get('name') for repo in user_repos]}")
        
        return user_repos
        
    except Exception as e:
        print(f"Error getting repositories for {username}: {e}")
        return []

def get_user_repos_count(username, user_repos):
    """해당 사용자의 레포지토리 개수를 반환합니다."""
    return len(user_repos)

def get_user_total_commits(username, user_repos):
    """해당 사용자의 레포지토리들에서 문제 풀이 커밋 수를 계산합니다."""
    try:
        total_commits = 0
        unique_commit_messages = set()  # 중복 커밋 메시지 방지
        
        for repo in user_repos:
            repo_name = repo['name']
            # 최근 1년간의 커밋 수를 가져옵니다
            since_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            url = f'https://api.github.com/repos/{ORG_NAME}/{repo_name}/commits'
            params = {
                'author': username,
                'since': since_date,
                'per_page': 100
            }
            
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code == 200:
                commits = response.json()
                problem_solve_count = 0
                
                for commit in commits:
                    commit_message = commit.get('commit', {}).get('message', '')
                    if is_problem_solve_commit(commit_message):
                        # 대소문자 구분 없이 공백 제거한 정규화된 메시지로 중복 체크
                        normalized_message = commit_message.lower().replace(' ', '')
                        if normalized_message not in unique_commit_messages:
                            unique_commit_messages.add(normalized_message)
                            problem_solve_count += 1
                        else:
                            print(f"   중복 커밋 메시지 제외: {commit_message}")
                
                total_commits += problem_solve_count
                print(f"   {repo_name}: {problem_solve_count}개 문제 풀이 커밋 (중복 제거 후)")
            else:
                print(f"   {repo_name}: 커밋 조회 실패 ({response.status_code})")
        
        print(f"📊 {username} 총 문제 풀이 커밋 수: {total_commits}개 (중복 제거 후)")
        return total_commits
        
    except Exception as e:
        print(f"Error getting total commits for {username}: {e}")
        return 0

def get_weekly_goal_achieved_weeks(username, user_repos):
    """사용자의 레포지토리들에서 주 3커밋 이상 달성한 주 수를 계산합니다."""
    try:
        print(f"🔍 {username}의 주간 목표 달성 계산:")
        print(f"   대상 레포지토리: {[repo.get('name') for repo in user_repos]}")
        
        # 주별로 그룹화 (중복 커밋 메시지 방지)
        weekly_commits = {}
        weekly_unique_messages = {}  # 주별 고유 커밋 메시지 추적
        
        for repo in user_repos:
            repo_name = repo['name']
            # 최근 1년간의 커밋 수를 가져옵니다
            since_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            url = f'https://api.github.com/repos/{ORG_NAME}/{repo_name}/commits'
            params = {
                'author': username,
                'since': since_date,
                'per_page': 100
            }
            
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code == 200:
                commits = response.json()
                
                for commit in commits:
                    commit_message = commit.get('commit', {}).get('message', '')
                    if is_problem_solve_commit(commit_message):
                        commit_date_str = commit.get('commit', {}).get('author', {}).get('date', '')[:10]
                        if commit_date_str:
                            commit_date = datetime.strptime(commit_date_str, '%Y-%m-%d')
                            week_key = commit_date.strftime('%Y-W%U')  # YYYY-WNN 형식 (주 번호)
                            
                            # 해당 주의 고유 커밋 메시지 집합 초기화
                            if week_key not in weekly_unique_messages:
                                weekly_unique_messages[week_key] = set()
                                weekly_commits[week_key] = 0
                            
                            # 대소문자 구분 없이 공백 제거한 정규화된 메시지로 중복 체크
                            normalized_message = commit_message.lower().replace(' ', '')
                            if normalized_message not in weekly_unique_messages[week_key]:
                                weekly_unique_messages[week_key].add(normalized_message)
                                weekly_commits[week_key] += 1
        
        # 주 3커밋 이상 달성한 주 수 계산
        achieved_weeks = 0
        for week, commit_count in weekly_commits.items():
            if commit_count >= 3:
                achieved_weeks += 1
        
        print(f"   주 3커밋 이상 달성: {achieved_weeks}주 (중복 제거 후)")
        return achieved_weeks
        
    except Exception as e:
        print(f"Error calculating weekly goals for {username}: {e}")
        return 0

def get_user_stats(username, org_repos):
    """조직 내에서 사용자의 퍼블릭 레포지토리 통계를 가져옵니다."""
    try:
        # 사용자 정보 가져오기
        user_url = f'https://api.github.com/users/{username}'
        user_response = requests.get(user_url, headers=HEADERS)
        user_data = user_response.json()
        
        # 먼저 해당 사용자의 레포지토리들을 식별
        user_repos = get_user_repositories(username, org_repos)
        
        # 식별된 레포지토리들을 기반으로 통계 계산
        repos_count = get_user_repos_count(username, user_repos)
        total_commits = get_user_total_commits(username, user_repos)
        weekly_goals = get_weekly_goal_achieved_weeks(username, user_repos)
        
        return {
            'name': MEMBERS[username],
            'username': username,
            'repos_count': repos_count,
            'total_commits': total_commits,
            'weekly_goals': weekly_goals,
            'created_at': user_data.get('created_at', '')
        }
    except Exception as e:
        print(f"Error getting stats for {username}: {e}")
        return {
            'name': MEMBERS[username],
            'username': username,
            'repos_count': 0,
            'total_commits': 0,
            'weekly_goals': 0,
            'created_at': ''
        }

def get_longest_streak_user(stats_data):
    """가장 긴 연속 풀이 주수를 달성한 사용자들을 찾습니다."""
    if not stats_data:
        return 0, "-"
    
    max_streak = 0
    max_streak_users = []
    
    # 최대 연속 풀이 주수 찾기
    for stats in stats_data:
        if stats['weekly_goals'] > max_streak:
            max_streak = stats['weekly_goals']
    
    # 최대 연속 풀이를 달성한 모든 사용자 찾기
    for stats in stats_data:
        if stats['weekly_goals'] == max_streak:
            max_streak_users.append(stats['name'])
    
    # 사용자 이름들을 쉼표로 구분하여 반환
    if max_streak_users:
        return max_streak, ", ".join(max_streak_users)
    else:
        return 0, "-"

def update_readme():
    """README.md 파일을 업데이트합니다."""
    readme_path = 'profile/README.md'
    
    print(f"📁 README 파일 경로: {readme_path}")
    print(f"📁 파일 존재 여부: {os.path.exists(readme_path)}")
    
    # 현재 README 읽기
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📖 README 파일 읽기 성공 (길이: {len(content)} 문자)")
    except Exception as e:
        print(f"❌ README 파일 읽기 실패: {e}")
        return
    
    # 조직 레포지토리 한 번만 조회
    org_repos = get_org_repos()
    
    # 멤버별 통계 수집
    stats_data = []
    for username in MEMBERS.keys():
        stats = get_user_stats(username, org_repos)
        stats_data.append(stats)
    
    # 성과 테이블 업데이트 (중앙 정렬 div 포함)
    stats_table = "<div align=\"center\">\n\n"
    stats_table += "### 📈 멤버별 성과\n"
    stats_table += "| 이름 | 🎯 해결 문제 | 📅 주 목표 달성 | 🏆 최고 티어 | 📁 개인 저장소 |\n"
    stats_table += "|------|-------------|---------------|-------------|------------------|\n"
    
    for stats in stats_data:
        # TIERS 상수에서 최고 티어 정보 가져오기
        tier = TIERS.get(stats['username'], '-')
        # 해당 사용자가 생성한 퍼블릭 레포지토리 수 표시
        repo_info = f"{stats['repos_count']}개"
        stats_table += f"| {stats['name']} | {stats['total_commits']}개 | {stats['weekly_goals']}주 | {tier} | {repo_info} |\n"
    
    stats_table += "\n</div>"
    
    # README에서 기존 성과 테이블을 찾아 교체 (div 구조 대응)
    pattern = r'<div align="center">\s*\n\s*### 📈 멤버별 성과.*?</div>'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, stats_table.rstrip(), content, flags=re.DOTALL)
    else:
        # 구버전 패턴도 시도
        old_pattern = r'### 📈 멤버별 성과\n.*?(?=\n### |$)'
        if re.search(old_pattern, content, re.DOTALL):
            content = re.sub(old_pattern, stats_table.rstrip(), content, flags=re.DOTALL)
        else:
            # 패턴을 찾지 못하면 적절한 위치에 추가
            content = content.replace('### 🏆 스터디 목표', f'{stats_table}\n### 🏆 스터디 목표')
    
    # 총 해결 문제와 최장 연속 풀이 계산
    total_problems = sum(stats['total_commits'] for stats in stats_data)
    max_streak_weeks, max_streak_users = get_longest_streak_user(stats_data)
    
    # 성과 기록 업데이트 (중앙 정렬 테이블)
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    performance_section = f"""## 🎉 성과 기록

<div align="center">

| 항목 | 현황 |
|---------|---------|
| **총 해결 문제** | {total_problems}개 |
| **현재 최장 연속 풀이** | {max_streak_weeks}주 (🏆 {max_streak_users}) |
| **마지막 업데이트** | {current_date} |

</div>
"""
    
    # README에서 기존 성과 기록을 찾아 교체 (div 구조 대응)
    pattern = r'## 🎉 성과 기록\s*\n\s*<div align="center">.*?</div>'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, performance_section.rstrip(), content, flags=re.DOTALL)
    else:
        # 구버전 패턴도 시도 (div 없는 버전)
        old_pattern = r'## 🎉 성과 기록\n.*?(?=\n\n## )'
        if re.search(old_pattern, content, re.DOTALL):
            content = re.sub(old_pattern, performance_section.rstrip(), content, flags=re.DOTALL)
        else:
            # 패턴을 찾지 못하면 적절한 위치에 추가
            content = content.replace('## 🤖 자동 통계 업데이트', f'{performance_section}\n\n## 🤖 자동 통계 업데이트')
    
    # 업데이트된 README 저장
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 README 파일 저장 성공 (길이: {len(content)} 문자)")
    except Exception as e:
        print(f"❌ README 파일 저장 실패: {e}")
        return
    
    print("✅ README가 성공적으로 업데이트되었습니다!")
    
    # 업데이트된 통계 요약 출력
    print(f"📊 업데이트 요약:")
    print(f"   - 멤버 수: {len(stats_data)}명")
    print(f"   - 총 해결 문제: {total_problems}개")
    print(f"   - 최장 연속 풀이: {max_streak_weeks}주 ({max_streak_users})")

if __name__ == "__main__":
    update_readme() 
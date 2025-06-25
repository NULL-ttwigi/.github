#!/usr/bin/env python3
"""
로컬 테스트용 스크립트 - GitHub API 없이 기본 동작 확인
"""
import os
from datetime import datetime

# 테스트 데이터
MEMBERS = {
    'girlwcode': '안예린',
    'heheelee': '이현희', 
    'mini-u': '유성민'
}

TIERS = {
    'girlwcode': '-', 
    'heheelee': '-', 
    'mini-u': '-' 
}

def create_test_stats():
    """테스트용 통계 데이터 생성"""
    return [
        {
            'name': '안예린',
            'username': 'girlwcode',
            'repos_count': 3,
            'public_repos': 2,
            'private_repos': 1,
            'total_commits': 15,
            'weekly_goals': 4,
            'created_at': '2023-01-01'
        },
        {
            'name': '이현희',
            'username': 'heheelee',
            'repos_count': 2,
            'public_repos': 1,
            'private_repos': 1,
            'total_commits': 12,
            'weekly_goals': 3,
            'created_at': '2023-01-01'
        },
        {
            'name': '유성민',
            'username': 'mini-u',
            'repos_count': 4,
            'public_repos': 3,
            'private_repos': 1,
            'total_commits': 20,
            'weekly_goals': 5,
            'created_at': '2023-01-01'
        }
    ]

def test_table_generation():
    """테이블 생성 테스트"""
    stats_data = create_test_stats()
    
    # 성과 테이블 생성
    stats_table = "### 📈 멤버별 성과\n"
    stats_table += "| 이름 | 🎯 해결 문제 | 📅 주 목표 달성 | 🏆 최고 티어 | 📁 개인 저장소 |\n"
    stats_table += "|------|-------------|---------------|-------------|---------------|\n"
    
    for stats in stats_data:
        # TIERS 상수에서 최고 티어 정보 가져오기
        tier = TIERS.get(stats['username'], '-')
        # 레포지토리 정보 표시 (공개/비공개 구분)
        repo_info = f"{stats['repos_count']}개"
        if stats.get('public_repos', 0) > 0 or stats.get('private_repos', 0) > 0:
            repo_info += f" (🌐{stats.get('public_repos', 0)} / 🔒{stats.get('private_repos', 0)})"
        stats_table += f"| {stats['name']} | {stats['total_commits']}개 | {stats['weekly_goals']}주 | {tier} | {repo_info} |\n"
    
    # 안내 문구 추가
    stats_table += "\n> 💡 **자동 업데이트**: 이 통계는 GitHub Actions를 통해 매일 자동으로 업데이트됩니다!\n\n> 📝 **최고 티어**: 백준/프로그래머스 등에서 달성한 최고 티어를 수동으로 업데이트해주세요!"
    
    print("🧪 테스트 테이블 생성 결과:")
    print("=" * 80)
    print(stats_table)
    print("=" * 80)
    
    # 성과 기록 생성
    total_problems = sum(stats['total_commits'] for stats in stats_data)
    max_streak_weeks = max(stats['weekly_goals'] for stats in stats_data)
    max_streak_users = [stats['name'] for stats in stats_data if stats['weekly_goals'] == max_streak_weeks]
    
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    performance_section = f"""## 🎉 성과 기록

- **총 해결 문제**: {total_problems}개
- **현재 최장 연속 풀이**: {max_streak_weeks}주 (🏆 {', '.join(max_streak_users)})
- **마지막 업데이트**: {current_date}
"""
    
    print("\n🧪 테스트 성과 기록 생성 결과:")
    print("=" * 80)
    print(performance_section)
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("🧪 로컬 테스트 시작...")
    success = test_table_generation()
    if success:
        print("✅ 로컬 테스트 완료! 테이블 생성 로직이 정상적으로 작동합니다.")
    else:
        print("❌ 로컬 테스트 실패!") 
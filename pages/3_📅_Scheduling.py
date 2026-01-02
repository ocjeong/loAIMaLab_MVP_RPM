import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.database import (
    get_request_data, get_test_items, 
    update_test_schedule
)
from modules.data_processing import calculate_schedule_dates
from modules.visualization import create_gantt_chart

# 페이지 설정
st.set_page_config(
    page_title="일정 관리",
    page_icon="📅",
    layout="wide"
)

# 세션 상태 확인
if 'current_user' not in st.session_state or st.session_state.current_user is None:
    st.error("❌ 먼저 사용자를 선택해주세요.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("app.py")
    st.stop()

if 'current_request' not in st.session_state or st.session_state.current_request is None:
    st.error("❌ 먼저 의뢰를 선택해주세요.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("app.py")
    st.stop()

# 메인 로직
def main():
    st.title("📅 시험 일정 관리")
    
    user_id = st.session_state.current_user
    request_id = st.session_state.current_request
    
    # 의뢰 데이터 조회
    request_data = get_request_data(request_id)
    
    if not request_data:
        st.error("❌ 의뢰 데이터를 찾을 수 없습니다.")
        if st.button("🏠 홈으로 돌아가기"):
            st.switch_page("app.py")
        st.stop()
    
    # 세션 정보 표시
    st.info(f"👤 사용자: {user_id} | 📋 의뢰: {request_id} - {request_data['client']}")
    
    # 시험 항목 조회
    test_items = get_test_items(request_id)
    
    if not test_items:
        st.warning("⚠️ 시험 항목이 없습니다.")
        if st.button("📊 계획서로 돌아가기"):
            st.switch_page("pages/2_📊_Planning.py")
        st.stop()
    
    # 시작일 설정
    st.markdown("---")
    st.subheader("📆 시험 시작일 설정")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        # 기본값: 오늘 또는 기존 시작일
        default_start = datetime.now()
        if test_items[0].get('start_date'):
            try:
                default_start = datetime.strptime(test_items[0]['start_date'], '%Y-%m-%d')
            except:
                pass
        
        start_date = st.date_input(
            "시험 시작일 (Day 0)",
            value=default_start,
            key="start_date_input"
        )
    
    with col2:
        # 총 소요 일수 계산
        total_duration = sum(item.get('test_duration', 0) for item in test_items if item.get('is_included', True))
        end_date = start_date + timedelta(days=total_duration)
        
        st.metric("총 소요 일수", f"{total_duration:.1f}일")
        st.metric("예상 종료일", end_date.strftime('%Y-%m-%d'))
    
    with col3:
        st.info("""
        💡 **일정 관리 팁**
        - 시작일을 변경하면 전체 일정이 자동 조정됩니다.
        - Gantt 차트에서 시각적으로 일정을 확인하세요.
        - 일정 저장 후 홈 화면에서 월간 일정을 확인할 수 있습니다.
        """)
    
    # 일정 계산
    scheduled_items = calculate_schedule_dates(test_items, datetime.combine(start_date, datetime.min.time()))
    
    # Gantt Chart
    st.markdown("---")
    st.subheader("📊 시험 일정 타임라인 (Gantt Chart)")
    
    try:
        fig = create_gantt_chart(scheduled_items, datetime.combine(start_date, datetime.min.time()))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 포함된 시험 항목이 없습니다.")
    except Exception as e:
        st.error(f"❌ 차트 생성 실패: {str(e)}")
    
    # 상세 일정 테이블
    st.markdown("---")
    st.subheader("📋 상세 일정 테이블")
    
    # 데이터프레임 생성
    schedule_data = []
    for idx, item in enumerate(scheduled_items):
        schedule_data.append({
            '순번': idx + 1,
            '시험명': item.get('test_name', ''),
            '분류': item.get('category', ''),
            '시료수': item.get('sample_count', 0),
            '소요일수': item.get('test_duration', 0),
            '시작일': item.get('start_date', ''),
            '종료일': item.get('end_date', ''),
            '장비': item.get('test_equipment', ''),
            '포함': item.get('is_included', True)
        })
    
    schedule_df = pd.DataFrame(schedule_data)
    
    # 편집 가능한 테이블
    edited_schedule_df = st.data_editor(
        schedule_df,
        column_config={
            "순번": st.column_config.NumberColumn("순번", disabled=True),
            "시험명": st.column_config.TextColumn("시험명", width="large"),
            "분류": st.column_config.TextColumn("분류", width="small"),
            "시료수": st.column_config.NumberColumn("시료수"),
            "소요일수": st.column_config.NumberColumn("소요일수", format="%.1f"),
            "시작일": st.column_config.TextColumn("시작일"),
            "종료일": st.column_config.TextColumn("종료일"),
            "장비": st.column_config.TextColumn("장비"),
            "포함": st.column_config.CheckboxColumn("포함", default=True)
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 일정 충돌 감지
    st.markdown("---")
    st.subheader("⚠️ 일정 충돌 감지")
    
    # 장비별 일정 확인
    equipment_schedule = {}
    conflicts = []
    
    for item in scheduled_items:
        equipment = item.get('test_equipment', '')
        if equipment and equipment != '':
            if equipment not in equipment_schedule:
                equipment_schedule[equipment] = []
            
            start = datetime.strptime(item['start_date'], '%Y-%m-%d')
            end = datetime.strptime(item['end_date'], '%Y-%m-%d')
            
            # 충돌 확인
            for existing in equipment_schedule[equipment]:
                existing_start = datetime.strptime(existing['start_date'], '%Y-%m-%d')
                existing_end = datetime.strptime(existing['end_date'], '%Y-%m-%d')
                
                if not (end <= existing_start or start >= existing_end):
                    conflicts.append({
                        'equipment': equipment,
                        'test1': item['test_name'],
                        'test2': existing['test_name'],
                        'period': f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"
                    })
            
            equipment_schedule[equipment].append(item)
    
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)}개의 장비 일정 충돌이 감지되었습니다!")
        
        conflict_df = pd.DataFrame(conflicts)
        st.dataframe(conflict_df, use_container_width=True)
    else:
        st.success("✅ 일정 충돌이 없습니다.")
    
    # 버튼 섹션
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if st.button("💾 일정 저장", type="primary", use_container_width=True):
            # 일정 데이터 업데이트
            update_data = []
            for idx, item in enumerate(scheduled_items):
                update_data.append({
                    'id': item.get('id'),
                    'start_date': item.get('start_date'),
                    'end_date': item.get('end_date'),
                    'priority_order': idx + 1,
                    'is_included': item.get('is_included', True)
                })
            
            update_test_schedule(request_id, update_data)
            
            st.success("✅ 일정이 저장되었습니다!")
            st.balloons()
    
    with col2:
        # CSV 다운로드
        csv_data = schedule_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv_data,
            file_name=f"일정_{request_id}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        if st.button("📊 계획서 보기", use_container_width=True):
            st.switch_page("pages/2_📊_Planning.py")
    
    with col4:
        if st.button("🏠 홈", use_container_width=True):
            st.switch_page("app.py")
    
    # 사이드바 - 일정 조정 옵션
    with st.sidebar:
        st.header("⚙️ 일정 조정")
        
        st.markdown("**일정 재계산**")
        
        if st.button("🔄 일정 재계산", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        st.header("📊 일정 통계")
        
        included_items = [item for item in test_items if item.get('is_included', True)]
        
        st.metric("포함된 시험", f"{len(included_items)} / {len(test_items)}")
        st.metric("총 소요 일수", f"{total_duration:.1f}일")
        
        # 분류별 소요 일수
        st.markdown("**분류별 소요 일수**")
        category_duration = {}
        for item in included_items:
            category = item.get('category', 'Other')
            duration = item.get('test_duration', 0)
            category_duration[category] = category_duration.get(category, 0) + duration
        
        for category, duration in sorted(category_duration.items()):
            st.write(f"- {category}: {duration:.1f}일")

if __name__ == "__main__":
    main()

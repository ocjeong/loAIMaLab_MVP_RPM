def page_user_selection():
    """3.1. 사용자 선택 화면"""
    st.title("👤 사용자 선택")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # 3.1.1. 사용자 선택 메뉴
        st.markdown("### 사용자 선택")
        
        users = db.get_all_users()
        user_names = [user['user_name'] for user in users]
        
        selected_user_name = st.selectbox(
            "사용자를 선택하세요",
            options=user_names,
            index=0 if user_names else None
        )
        
        if selected_user_name:
            selected_user = next(u for u in users if u['user_name'] == selected_user_name)
            st.session_state.current_user = selected_user
            db.update_user_last_access(selected_user['id'])
        
        # 사용자 추가
        st.markdown("#### 새 사용자 추가")
        new_user_name = st.text_input("사용자 이름")
        if st.button("➕ 사용자 추가", use_container_width=True):
            if new_user_name:
                db.add_user(new_user_name)
                st.success(f"✅ {new_user_name} 사용자가 추가되었습니다!")
                st.rerun()
            else:
                st.error("사용자 이름을 입력해주세요.")
        
        st.divider()
        
        # 3.1.3. 의뢰 선택 메뉴
        if st.session_state.current_user:
            st.markdown("### 기존 의뢰 선택")
            
            user_requests = db.get_user_requests(st.session_state.current_user['id'])
            
            if user_requests:
                request_options = {
                    f"{req['project']} ({req['client']})": req['id'] 
                    for req in user_requests
                }
                
                selected_request = st.selectbox(
                    "의뢰를 선택하세요",
                    options=list(request_options.keys())
                )
                
                if selected_request:
                    request_id = request_options[selected_request]
                    request_data = db.get_request_by_id(request_id)
                    st.session_state.current_request = request_data
                    
                    # 3.1.5. 의뢰 수정 버튼
                    if st.button("✏️ 의뢰 수정", use_container_width=True):
                        st.session_state.current_page = "test_spec_edit"
                        st.rerun()
            else:
                st.info("저장된 의뢰가 없습니다.")
        
        st.divider()
        
        # 3.1.4. 새 의뢰 버튼 (수정됨)
        st.markdown("### 새 의뢰 생성")
        
        # 샘플 파일 목록 가져오기
        from utils.helpers import get_sample_pdf_files, load_sample_pdf
        sample_files = get_sample_pdf_files()
        
        # 샘플 파일 선택 메뉴 (2개 이상 있을 때만 표시)
        selected_sample = None
        if sample_files:
            st.markdown("#### 📁 샘플 파일 선택")
            
            sample_options = ["직접 업로드"] + [f['display_name'] for f in sample_files]
            selected_option = st.selectbox(
                "샘플 파일을 선택하거나 직접 업로드하세요",
                options=sample_options,
                help="sample 폴더의 PDF 파일을 선택하거나 직접 파일을 업로드할 수 있습니다."
            )
            
            if selected_option != "직접 업로드":
                # 선택된 샘플 파일 찾기
                for sample in sample_files:
                    if sample['display_name'] == selected_option:
                        selected_sample = sample
                        st.info(f"📄 선택된 샘플: {selected_sample['name']}")
                        break
        
        # 파일 업로드 또는 샘플 사용
        uploaded_file = None
        
        if selected_sample:
            # 샘플 파일 사용
            st.markdown("#### 샘플 파일로 의뢰 생성")
            if st.button("🚀 샘플로 의뢰 생성", use_container_width=True, type="primary"):
                with st.spinner("샘플 문서를 분석하고 있습니다..."):
                    # 샘플 파일 로드
                    sample_file = load_sample_pdf(selected_sample['path'])
                    
                    if sample_file:
                        # 파일 처리 및 LLM 추출
                        extracted_data = llm_handler.extract_from_document(sample_file)
                        
                        if extracted_data:
                            # 표준화 적용
                            standardized_items = []
                            for item in extracted_data.get('test_items', []):
                                standardized_item = standardize_test_item(item, db)
                                standardized_items.append(standardized_item)
                            
                            # 새 의뢰 생성
                            request_id = db.create_request(
                                user_id=st.session_state.current_user['id'],
                                client=extracted_data.get('request_info', {}).get('client', ''),
                                project=extracted_data.get('request_info', {}).get('project', ''),
                                extracted_data=extracted_data.get('test_items', []),
                                final_data=standardized_items
                            )
                            
                            st.session_state.current_request = db.get_request_by_id(request_id)
                            st.success("✅ 샘플 의뢰가 생성되었습니다!")
                            st.session_state.current_page = "test_spec_edit"
                            st.rerun()
                        else:
                            st.error("문서 추출에 실패했습니다.")
                    else:
                        st.error("샘플 파일을 로드할 수 없습니다.")
        else:
            # 직접 파일 업로드
            st.markdown("#### 파일 직접 업로드")
            uploaded_file = st.file_uploader(
                "시험 규격 파일 업로드",
                type=['pdf', 'docx'],
                help="PDF 또는 DOCX 형식의 파일만 업로드 가능합니다."
            )
            
            if uploaded_file:
                if st.button("🚀 새 의뢰 생성", use_container_width=True, type="primary"):
                    with st.spinner("문서를 분석하고 있습니다..."):
                        # 파일 처리 및 LLM 추출
                        extracted_data = llm_handler.extract_from_document(uploaded_file)
                        
                        if extracted_data:
                            # 표준화 적용
                            standardized_items = []
                            for item in extracted_data.get('test_items', []):
                                standardized_item = standardize_test_item(item, db)
                                standardized_items.append(standardized_item)
                            
                            # 새 의뢰 생성
                            request_id = db.create_request(
                                user_id=st.session_state.current_user['id'],
                                client=extracted_data.get('request_info', {}).get('client', ''),
                                project=extracted_data.get('request_info', {}).get('project', ''),
                                extracted_data=extracted_data.get('test_items', []),
                                final_data=standardized_items
                            )
                            
                            st.session_state.current_request = db.get_request_by_id(request_id)
                            st.success("✅ 의뢰가 생성되었습니다!")
                            st.session_state.current_page = "test_spec_edit"
                            st.rerun()
                        else:
                            st.error("문서 추출에 실패했습니다.")
    
    with col2:
        # 3.1.2. 일정 확인 박스
        st.markdown("### 📅 시험 일정")
        
        if st.session_state.current_user:
            schedules = db.get_user_schedules(st.session_state.current_user['id'])
            
            if schedules:
                # 선택된 의뢰의 일정 또는 전체 일정 표시
                if st.session_state.current_request:
                    filtered_schedules = [
                        s for s in schedules 
                        if s.get('request_id') == st.session_state.current_request['id']
                    ]
                    st.markdown(f"**{st.session_state.current_request.get('project', '')} 의뢰 일정**")
                else:
                    filtered_schedules = schedules
                    st.markdown("**전체 시험 일정**")
                
                if filtered_schedules:
                    fig = schedule_manager.create_gantt_chart(filtered_schedules)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("표시할 일정이 없습니다.")
            else:
                st.info("저장된 일정이 없습니다.")
        else:
            st.warning("사용자를 선택해주세요.")

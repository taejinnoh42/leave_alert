import json
import os
import requests
import time
import sys
from playwright.sync_api import sync_playwright

# ==========================================
# 1. 기본 설정
# ==========================================
LOGIN_URL = "https://mgace-leave-manager-production.up.railway.app/login"
TEAMS_WEBHOOK_URL = "https://defaultaa8a2b8a92c048a082e87f593e87ad.ba.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/22/workflows/67be5de73751423aa4737e8487c5e38b/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dXmctChrXxu-OIUKRjSne88gztRXpDEtkTIi8p4V0IE"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "leave_state.json")

# ==========================================
# [수정됨] Teams 워크플로 규격에 맞춘 전송 함수
# ==========================================
def send_teams_alert(message):
    if TEAMS_WEBHOOK_URL == "여기에_TEAMS_웹훅_URL_입력":
        print("경고: Teams 웹훅 URL이 설정되지 않았습니다.")
        return
        
    # 워크플로가 안정적으로 수신하는 Adaptive Card 포맷
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Teams 알림 전송 실패: {e}")
        if hasattr(e, 'response') and getattr(e, 'response') is not None:
            print("상세 에러:", e.response.text)

def main():
    is_test_mode = len(sys.argv) > 1 and sys.argv[1].lower() == "test"

    with sync_playwright() as p:
        # 화면을 보면서 테스트하려면 False, 나중에 백그라운드에서 24시간 돌리려면 True로 변경하세요.
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()

        print("로그인 페이지 접속 중...")
        page.goto(LOGIN_URL)
        
        page.fill("input[name='name']", "임시관리자") 
        page.fill("input[name='birth_date']", "19000101") 
        
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        print("'연차승인' 메뉴로 이동 중...")
        page.locator("text=연차승인").click() 
        page.wait_for_load_state("networkidle") 

        print("'승인됨' 목록으로 이동 중...")
        page.locator("text=승인됨").click()
        
        try:
            page.wait_for_selector("table tbody tr", timeout=10000)
        except Exception:
            print("테이블 데이터를 불러오지 못했거나 내역이 없습니다.")
            browser.close()
            return
            
        print("데이터 수집 중...")
        current_data = []
        rows = page.query_selector_all("table tbody tr") 
        
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 6:
                name = cells[0].inner_text().strip()       
                department = cells[1].inner_text().strip() 
                leave_type = cells[2].inner_text().strip().replace('\n', ' ') 
                period = cells[3].inner_text().strip()     
                
                if department == "AD Data Intelligence":
                    item_key = f"{name}|{period}|{leave_type}"
                    current_data.append(item_key)

        browser.close()

        # ==========================================
        # 5. 테스트 모드 실행 로직
        # ==========================================
        if is_test_mode:
            print("\n🧪 [테스트 모드] 작동 중... 가장 최근 내역 1건만 전송합니다.")
            if current_data:
                test_item = current_data[0] 
                parts = test_item.split('|')
                if len(parts) >= 3:
                    alert_msg = f"🧪 [테스트 발송]\n부서: AD Data Intelligence\n이름: {parts[0]}님\n기간: {parts[1]}\n종류: {parts[2]}"
                else:
                    alert_msg = f"🧪 [테스트 발송] 데이터: {test_item}"
                print(alert_msg)
                send_teams_alert(alert_msg)
            else:
                print("해당 부서의 수집된 데이터가 없습니다.")
            return 

        # ==========================================
        # 6. 일반 모드: 상태 비교 및 알림 로직
        # ==========================================
        previous_data = []
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                previous_data = json.load(f)

        new_items = []
        for item in current_data:
            if item not in previous_data:
                new_items.append(item)

        if not new_items:
            print("AD Data Intelligence 부서의 새로운 승인 내역이 없습니다.")
            
        for item in new_items:
            parts = item.split('|')
            if len(parts) >= 3:
                name = parts[0]
                period = parts[1]
                leave_type = parts[2]
                alert_msg = f"🔔 [연차 승인 완료]\n부서: AD Data Intelligence\n이름: {name}님\n기간: {period}\n종류: {leave_type}"
            else:
                alert_msg = f"🔔 [연차 알림] 새로운 변동 발생: {item}"
            
            print(f"\n--- 새 알림 발송: {item} ---")
            send_teams_alert(alert_msg)
            time.sleep(2) 

        updated_history = previous_data.copy()
        updated_history.extend(new_items)
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_history, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
work1.py

Selenium script to automate login and user selection on
https://jeonbuk.insarang.go.kr/nexin/index.html
"""
from __future__ import annotations
import sys
import time
from typing import Optional
import os
import subprocess
import random
from datetime import datetime, timedelta
import json

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except Exception:
    EdgeChromiumDriverManager = None

from selenium.webdriver.remote.webdriver import WebDriver


# ==================== 설정 변수 ====================
# 사용자명 (title에서 검색할 이름)
USER_NAME = "오경준"

# 비밀번호
PASSWORD = "asdf6433!@"

# 업무 설명
WORK_DESCRIPTION = "열린시정 업무추진"

# 스케줄 설정 (랜덤 시간 범위, HH:MM 형식)
SCHEDULE_START_TIME = "23:10"  # 최소 시작 시각
SCHEDULE_END_TIME = "23:15"    # 최대 시작 시각
# ===================================================


# ==================== 설정 파일 관리 ====================
CONFIG_FILE = "config.json"


def load_config():
    """저장된 설정 파일 불러오기"""
    global USER_NAME, PASSWORD, WORK_DESCRIPTION
    global SCHEDULE_START_TIME, SCHEDULE_END_TIME
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                USER_NAME = config.get('USER_NAME', USER_NAME)
                PASSWORD = config.get('PASSWORD', PASSWORD)
                WORK_DESCRIPTION = config.get('WORK_DESCRIPTION', WORK_DESCRIPTION)
                SCHEDULE_START_TIME = config.get('SCHEDULE_START_TIME', SCHEDULE_START_TIME)
                SCHEDULE_END_TIME = config.get('SCHEDULE_END_TIME', SCHEDULE_END_TIME)
                print("✓ 저장된 설정을 불러왔습니다.")
        except Exception as e:
            print(f"설정 파일 로드 중 오류: {e}")


def save_config():
    """설정 파일 저장"""
    config = {
        'USER_NAME': USER_NAME,
        'PASSWORD': PASSWORD,
        'WORK_DESCRIPTION': WORK_DESCRIPTION,
        'SCHEDULE_START_TIME': SCHEDULE_START_TIME,
        'SCHEDULE_END_TIME': SCHEDULE_END_TIME,
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("✓ 설정이 저장되었습니다.")
    except Exception as e:
        print(f"설정 파일 저장 중 오류: {e}")


def input_config_settings():
    """설정값을 사용자로부터 입력받기"""
    global USER_NAME, PASSWORD, WORK_DESCRIPTION
    global SCHEDULE_START_TIME, SCHEDULE_END_TIME
    
    print("\n" + "=" * 60)
    print("변수 설정 모드")
    print("=" * 60)
    
    # 사용자명
    user_input = input(f"사용자명 (현재: {USER_NAME}): ").strip()
    if user_input:
        USER_NAME = user_input
    
    # 비밀번호
    user_input = input(f"비밀번호 (현재: {'*' * len(PASSWORD)}): ").strip()
    if user_input:
        PASSWORD = user_input
    
    # 업무 설명
    user_input = input(f"업무내용 (현재: {WORK_DESCRIPTION}): ").strip()
    if user_input:
        WORK_DESCRIPTION = user_input
    
    # 최소 시작 시각
    while True:
        user_input = input(f"최소 시작 시각 (HH:MM 형식, 현재: {SCHEDULE_START_TIME}): ").strip()
        if not user_input:
            break
        try:
            hour, minute = map(int, user_input.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                SCHEDULE_START_TIME = f"{hour:02d}:{minute:02d}"
                break
            print("올바른 시간을 입력하세요 (00:00 ~ 23:59)")
        except ValueError:
            print("올바른 형식으로 입력하세요 (HH:MM)")
    
    # 최대 시작 시각
    while True:
        user_input = input(f"최대 시작 시각 (HH:MM 형식, 현재: {SCHEDULE_END_TIME}): ").strip()
        if not user_input:
            break
        try:
            hour, minute = map(int, user_input.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                SCHEDULE_END_TIME = f"{hour:02d}:{minute:02d}"
                break
            print("올바른 시간을 입력하세요 (00:00 ~ 23:59)")
        except ValueError:
            print("올바른 형식으로 입력하세요 (HH:MM)")
    
    # 설정 저장
    save_config()
    print("=" * 60)
    print()

# ===================================================


def calculate_next_run_time():
    """Calculate the next run time between SCHEDULE_START_TIME and SCHEDULE_END_TIME."""
    now = datetime.now()
    
    # 시작 시각과 종료 시각을 시간:분으로 파싱
    start_h, start_m = map(int, SCHEDULE_START_TIME.split(":"))
    end_h, end_m = map(int, SCHEDULE_END_TIME.split(":"))
    
    # 분 단위로 변환하여 범위 계산
    start_total_minutes = start_h * 60 + start_m
    end_total_minutes = end_h * 60 + end_m
    
    # 랜덤 시간 생성
    random_total_minutes = random.randint(start_total_minutes, end_total_minutes)
    random_hour = random_total_minutes // 60
    random_minute = random_total_minutes % 60
    
    # Set target time to today at the random time
    target_time = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
    
    # If target time has already passed today, schedule for tomorrow
    if target_time <= now:
        target_time += timedelta(days=1)
    
    return target_time


def wait_for_scheduled_time(target_time):
    """Wait until the scheduled time arrives."""
    while True:
        now = datetime.now()
        if now >= target_time:
            break
        
        remaining = target_time - now
        remaining_seconds = int(remaining.total_seconds())
        
        # Calculate hours, minutes, seconds
        hours, remainder = divmod(remaining_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Display status on a single line, updating every 1 second
        status_msg = f"대기중... 남은시간 : {hours}시간 {minutes}분 {seconds:02d}초"
        print(status_msg, end='\r', flush=True)
        
        time.sleep(1)


def create_driver() -> WebDriver:
    """Create and configure Edge WebDriver."""
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    # # 빠른 시작을 위한 옵션들
    # options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-plugins")
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option("useAutomationExtension", False)

    try:
        print("Edge 브라우저 시작 중...")
        driver = webdriver.Edge(options=options)
        print("Edge 브라우저가 시작되었습니다.")
        # 페이지 로드 타임아웃 설정
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        return driver
    except Exception as e:
        print(f"에러: {e}")
        raise RuntimeError(
            "Edge 웹드라이버를 시작할 수 없습니다. msedgedriver가 PATH에 있는지 확인하세요."
        ) from e


def click_element_when_ready(driver: WebDriver, by, selector, timeout=15):
    """요소가 클릭 가능할 때까지 대기한 후 클릭합니다."""
    wait = WebDriverWait(driver, timeout)
    el = wait.until(EC.element_to_be_clickable((by, selector)))
    el.click()
    return el


# ==================== 원격 디버깅 지원 ====================
class _Tee:
    """print 출력을 콘솔과 로그 파일에 동시에 기록합니다."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


def setup_logging():
    """모든 stdout/stderr를 logs/run_날짜시간.log에도 기록합니다."""
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join("logs", f"run_{ts}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, log_file)
    sys.stderr = _Tee(sys.__stderr__, log_file)
    print(f"로그 파일: {log_path}")


def dump_state(driver, tag):
    """실패 지점의 증거(스크린샷 + 현재 프레임 HTML)를 logs 폴더에 저장합니다."""
    try:
        os.makedirs("logs", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join("logs", f"fail_{tag}_{ts}")
        try:
            driver.save_screenshot(f"{base}.png")
        except Exception as e:
            print(f"스크린샷 저장 실패: {e}")
        try:
            with open(f"{base}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as e:
            print(f"HTML 저장 실패: {e}")
        try:
            print(f"[진단] 현재 URL: {driver.current_url} / 창 개수: {len(driver.window_handles)}")
        except Exception:
            pass
        print(f"증거 저장 완료: {base}.png / {base}.html")
    except Exception as e:
        print(f"dump_state 오류: {e}")
# ========================================================


def main():
    driver = None
    try:
        print("Edge 웹드라이버를 생성하는 중...")
        driver = create_driver()
        print("웹드라이버가 생성되었습니다.")
    except Exception as e:
        print("웹드라이버 생성 중 오류 발생:")
        print(f"상세 오류: {e}")
        traceback.print_exc()
        return 99

    wait = WebDriverWait(driver, 15)

    try:
        try:
            print("페이지 로드 중...")
            driver.get("https://jeonbuk.insarang.go.kr/nexin/index.html")
            print("페이지 로드 완료")
        except TimeoutException:
            print("페이지 로드 타임아웃 - 계속 진행합니다.")
        except Exception as e:
            print("페이지 탐색 중 오류 발생:")
            print(f"상세 오류: {e}")
            traceback.print_exc()
            raise

        # 1) 로그인 버튼 클릭
        login_xpath = '//*[@id="mainframe.WorkFrame.form.divCenter.form.divLogin.form.btnLogin:icontext"]'
        print("로그인 버튼을 클릭합니다...")
        click_element_when_ready(driver, By.XPATH, login_xpath, timeout=10)
        print("로그인 버튼 클릭 완료. GPKI 인증 iframe(#dscert) 로드를 대기합니다...")

        # 2) #dscert iframe이 로드되고 전환 가능해질 때까지 대기 후 진입
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "dscert")))
            print("#dscert iframe 안으로 전환했습니다.")
        except TimeoutException:
            print("#dscert iframe을 찾지 못했습니다. 인증창이 뜨지 않은 것 같습니다.")
            dump_state(driver, "step2_no_iframe")
            return 2

        # 3) iframe 안에서 인증서 목록이 렌더링될 때까지 폴링하며 사용자 검색
        # (dscert iframe은 페이지 초기화 시 생성되지만, 인증서 목록은 GPKI 플러그인 응답 후 렌더링됨)
        name = USER_NAME
        print(f"iframe 안에서 제목에 '{name}'을(를) 포함하는 요소를 검색합니다 (최대 20초 폴링)...")
        matches = []
        search_deadline = time.time() + 20
        while time.time() < search_deadline:
            matches = driver.find_elements(By.XPATH, f"//*[contains(@title, \"{name}\")]")
            if matches:
                break
            time.sleep(0.5)

        if not matches:
            print("사용자를 찾지 못했습니다. iframe 내부 HTML과 스크린샷을 저장합니다.")
            dump_state(driver, "step3_user_not_found")
            driver.switch_to.default_content()
            return 3

        print(f"사용자 요소 {len(matches)}개를 찾았습니다.")

        # 선호하는 SPAN 매치를 찾고, 없으면 첫 번째 매치 사용
        target = None
        for m in matches:
            try:
                if m.tag_name.lower() == 'span':
                    target = m
                    break
            except Exception:
                continue
        if not target:
            target = matches[0]

        # 요소를 클릭합니다 (실패 시 재검색 후 JS 클릭으로 재시도)
        driver.execute_script("arguments[0].scrollIntoView(true);", target)
        try:
            target.click()
        except Exception as click_err:
            print(f"일반 클릭 실패({click_err}). 요소를 다시 찾아 JS 클릭을 시도합니다.")
            target = driver.find_element(By.XPATH, f"//*[contains(@title, \"{name}\")]")
            driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", target)
        print(f"사용자 요소를 클릭했습니다. (tag={target.tag_name})")

        # 5) 비밀번호를 #input_cert_pw에 입력 (같은 iframe 안)
        # GPKI가 사용자 클릭 직후 DOM을 재렌더링하므로 stale 발생 가능 -> 재시도 패턴 적용
        pw_ok = False
        for attempt in range(1, 4):
            try:
                pw_input = wait.until(EC.presence_of_element_located((By.ID, "input_cert_pw")))
                pw_input.clear()
                pw_input.send_keys(PASSWORD)
                entered_len = driver.execute_script("return arguments[0].value.length;", pw_input)
                if entered_len == len(PASSWORD):
                    print(f"비밀번호를 입력했습니다. (시도 {attempt}, 입력된 글자 수: {entered_len})")
                    pw_ok = True
                    break
                print(f"비밀번호 입력 검증 실패 (시도 {attempt}, 입력됨: {entered_len}자). 재시도합니다.")
            except Exception as e:
                print(f"비밀번호 입력 시도 {attempt} 실패 ({type(e).__name__}). 요소를 다시 찾습니다.")
                time.sleep(0.5)
        if not pw_ok:
            print("비밀번호 입력에 최종 실패했습니다.")
            dump_state(driver, "step4_pw_field")
            driver.switch_to.default_content()
            return 4

        # 6) 확인 버튼 클릭 (같은 iframe 안) - stale 대응 재시도
        confirm_xpath = '//*[@id="btn_confirm_iframe"]/span'
        confirm_ok = False
        for attempt in range(1, 4):
            try:
                click_element_when_ready(driver, By.XPATH, confirm_xpath, timeout=10)
                print(f"확인 버튼을 클릭했습니다. (시도 {attempt})")
                confirm_ok = True
                break
            except Exception as e:
                if isinstance(e, TimeoutException):
                    print("확인 버튼을 찾지 못했거나 클릭할 수 없습니다.")
                    break
                print(f"확인 버튼 클릭 시도 {attempt} 실패 ({type(e).__name__}). 재시도합니다.")
                time.sleep(0.5)
        if not confirm_ok:
            dump_state(driver, "step5_confirm_btn")
            driver.switch_to.default_content()
            return 5

        # 기본 문서로 복귀
        driver.switch_to.default_content()
        print("기본 문서로 복귀했습니다.")

        # 2초 대기
        time.sleep(3)

        # 팝업 창 처리
        original_window = driver.current_window_handle
        if len(driver.window_handles) > 1:
            print(f"여러 창이 감지되었습니다. 팝업 창으로 전환합니다...")
            for window in driver.window_handles:
                if window != original_window:
                    driver.switch_to.window(window)
                    time.sleep(1)
                    # 팝업 닫기 시도
                    try:
                        driver.close()
                    except Exception:
                        pass
            driver.switch_to.window(original_window)
            time.sleep(1)
            
        # 6) btnEndReg 클릭
        btn_end_reg_xpath = '//*[@id="mainframe.WorkFrame.form.divMain.form.divMain.form.divCont0.form.btnEndReg:icontext"]'
        try:
            # 프레임 전환 시도
            try:
                driver.switch_to.default_content()
                time.sleep(0.3)
            except:
                pass
            
            # 스크롤 및 대기 (presence 대기로 교체 - find_element는 NoSuchElementException을 던짐)
            btn_end = wait.until(EC.presence_of_element_located((By.XPATH, btn_end_reg_xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", btn_end)
            time.sleep(1)

            click_element_when_ready(driver, By.XPATH, btn_end_reg_xpath, timeout=10)
            print("btnEndReg를 클릭했습니다.")
        except TimeoutException:
            print("btnEndReg를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step6_btnEndReg")
            return 6

        # 7) btnWrkTimeData 클릭
        btn_wrk_time_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.form.divStep1.form.divDetail.form.btnWrkTimeData:icontext"]'
        try:
            click_element_when_ready(driver, By.XPATH, btn_wrk_time_xpath, timeout=10)
            print("btnWrkTimeData를 클릭했습니다.")
        except TimeoutException:
            print("btnWrkTimeData를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step7_btnWrkTimeData")
            return 7

        # 8) edtWrkDtlsCn에 텍스트 입력
        edt_wrk_dtls_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.tatAtdc03001P13.form.divSearch.form.edtWrkDtlsCn:input"]'
        try:
            edt_input = wait.until(EC.presence_of_element_located((By.XPATH, edt_wrk_dtls_xpath)))
            edt_input.clear()
            edt_input.send_keys(WORK_DESCRIPTION)
            print("edtWrkDtlsCn에 텍스트를 입력했습니다.")
        except TimeoutException:
            print("edtWrkDtlsCn을 찾지 못했습니다.")
            dump_state(driver, "step8_edtWrkDtlsCn")
            return 8

        # 9) btnCheck 클릭
        btn_check_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.tatAtdc03001P13.form.divSearch.form.btnCheck:icontext"]'
        try:
            click_element_when_ready(driver, By.XPATH, btn_check_xpath, timeout=10)
            print("btnCheck를 클릭했습니다.")
        except TimeoutException:
            print("btnCheck를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step9_btnCheck")
            return 9

        # 10) 경고창의 btnOk 클릭
        btn_ok_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.msgAlert.form.btnOk:icontext"]'
        try:
            click_element_when_ready(driver, By.XPATH, btn_ok_xpath, timeout=10)
            print("btnOk를 클릭했습니다.")
        except TimeoutException:
            print("btnOk를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step10_btnOk")
            return 10

        # 11) btnNextStep2 클릭
        btn_next_step2_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.form.divStep1.form.btnNextStep2:icontext"]'
        try:
            click_element_when_ready(driver, By.XPATH, btn_next_step2_xpath, timeout=10)
            print("btnNextStep2를 클릭했습니다.")
        except TimeoutException:
            print("btnNextStep2를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step11_btnNextStep2")
            return 11

        # 12) 2초 대기
        time.sleep(5)

        # captcha 인식 루프 (유효하지 않으면 재시도)
        max_retries = 3
        retry_count = 0
        captcha_success = False

        while retry_count < max_retries and not captcha_success:
            if retry_count > 0:
                print(f"\n재시도 {retry_count}/{max_retries}...")
                # 새로운 captcha를 가져오기 위해 새로고침 버튼 클릭
                btn_ch_refresh_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.form.divStep3.form.btnChRefresh:icontext"]'
                try:
                    click_element_when_ready(driver, By.XPATH, btn_ch_refresh_xpath, timeout=10)
                    print("btnChRefresh를 클릭했습니다.")
                    time.sleep(2)
                except TimeoutException:
                    print("btnChRefresh를 찾지 못했거나 클릭할 수 없습니다.")
                    dump_state(driver, "step16_btnChRefresh")
                    return 16

            # 13) 이미지 다운로드
            image_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.form.divStep3.form.divChCode.imagearea:image"]'
            try:
                # presence 대기로 교체 (find_element는 즉시 NoSuchElementException을 던져 except TimeoutException에 잡히지 않음)
                img_element = wait.until(EC.presence_of_element_located((By.XPATH, image_xpath)))
                img_src = img_element.get_attribute('src')
                
                if img_src:
                    # 데이터 URL 또는 일반 URL 처리
                    if img_src.startswith('data:'):
                        # 데이터 URL의 경우 base64 데이터 추출 및 저장
                        import base64
                        header, data = img_src.split(',')
                        img_data = base64.b64decode(data)
                        with open('target.png', 'wb') as f:
                            f.write(img_data)
                        print("이미지를 다운로드하여 target.png로 저장했습니다 (데이터 URL).")
                    else:
                        # 일반 URL의 경우 이미지 다운로드
                        import urllib.request
                        urllib.request.urlretrieve(img_src, 'target.png')
                        print("이미지를 다운로드하여 target.png로 저장했습니다.")
                else:
                    print("이미지 src 속성을 찾지 못했습니다.")
                    dump_state(driver, "step12_no_img_src")
                    return 12
            except TimeoutException:
                print("이미지 요소를 찾지 못했습니다.")
                dump_state(driver, "step13_no_image")
                return 13

            # 14) captcha 인식을 위해 capcrack 실행
            print("capcrack.py를 실행하여 captcha를 인식합니다...")
            try:
                # 작업 디렉토리를 현재 스크립트 디렉토리로 설정
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
                result = subprocess.run(
                    [sys.executable, "capcrack.py"],
                    cwd=script_dir,
                    capture_output=True,
                    timeout=60
                )
                
                # 인코딩 문제 처리 - cp949 또는 utf-8로 시도
                try:
                    capcrack_output = result.stdout.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        capcrack_output = result.stdout.decode('cp949')
                    except UnicodeDecodeError:
                        capcrack_output = result.stdout.decode('utf-8', errors='ignore')
                
                print(f"capcrack 출력: {capcrack_output}")
                
                # "인식 결과 : " 뒤의 숫자를 추출하여 결과 파싱
                if "인식 결과" in capcrack_output:
                    # "인식 결과 : " 뒤의 부분 찾기
                    parts = capcrack_output.split("인식 결과")
                    if len(parts) > 1:
                        result_text = parts[-1].strip()
                        # 콜론 뒤의 숫자만 추출
                        if ":" in result_text:
                            captcha_result = result_text.split(":", 1)[-1].strip()
                        else:
                            captcha_result = result_text.strip()
                        
                        print(f"인식된 captcha: {captcha_result}")
                        
                        # captcha 결과 검증
                        # 정확히 5자리 숫자여야 하고 [UNK]가 없어야 함
                        if "[UNK]" in captcha_result:
                            print("유효하지 않은 captcha: [UNK]가 포함됨. 재시도합니다...")
                            retry_count += 1
                            continue
                        elif not captcha_result.isdigit() or len(captcha_result) != 5:
                            print(f"유효하지 않은 captcha: 5자리 숫자가 필요한데 '{captcha_result}'를 받음. 재시도합니다...")
                            retry_count += 1
                            continue
                        else:
                            print(f"유효한 captcha 결과: {captcha_result}")
                            captcha_success = True
                    else:
                        print("capcrack 출력에서 captcha 결과를 파싱할 수 없습니다.")
                        dump_state(driver, "step14_parse_fail")
                        return 14
                else:
                    print("capcrack 출력에서 captcha 결과를 찾지 못했습니다.")
                    dump_state(driver, "step14_no_result")
                    return 14

            except subprocess.TimeoutExpired:
                print("capcrack.py가 타임아웃되었습니다.")
                dump_state(driver, "step14_capcrack_timeout")
                return 14
            except Exception as e:
                print(f"capcrack.py 실행 중 오류 발생: {e}")
                traceback.print_exc()
                dump_state(driver, "step14_capcrack_error")
                return 14

        if not captcha_success:
            print(f"{max_retries}회 재시도 후에도 captcha를 인식하지 못했습니다.")
            dump_state(driver, "step17_captcha_fail")
            return 17

        # 15) edtChNoCfm에 captcha 결과 입력
        edt_ch_no_cfm_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.form.divStep3.form.edtChNoCfm:input"]'
        try:
            ch_no_input = wait.until(EC.presence_of_element_located((By.XPATH, edt_ch_no_cfm_xpath)))
            # 화면에 보이도록 스크롤
            driver.execute_script("arguments[0].scrollIntoView(true);", ch_no_input)
            time.sleep(0.5)
            # 포커스를 위해 클릭
            try:
                ch_no_input.click()
            except:
                driver.execute_script("arguments[0].click();", ch_no_input)
            time.sleep(0.5)
            
            # Selenium의 send_keys를 사용하여 입력 (더 안정적)
            ch_no_input.clear()
            ch_no_input.send_keys(captcha_result)
            
            # 여러 이벤트를 발생시켜 웹사이트가 값 변경을 감지하도록 함
            driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
            """, ch_no_input)
            
            print(f"captcha 결과 '{captcha_result}'를 edtChNoCfm에 입력했습니다.")
            time.sleep(1)
            
            # 입력 값 확인
            input_value = driver.execute_script("return arguments[0].value;", ch_no_input)
            print(f"입력 확인: {input_value}")
            
        except TimeoutException:
            print("edtChNoCfm 입력 필드를 찾지 못했습니다.")
            dump_state(driver, "step18_edtChNoCfm")
            return 18

        time.sleep(2)
        # 16) Click btnCerNoCfm button 
        btn_cer_no_cfm_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P12.form.divStep3.form.btnCerNoCfm:icontext"]'
        try:
            click_element_when_ready(driver, By.XPATH, btn_cer_no_cfm_xpath, timeout=10)
            print("btnCerNoCfm을 클릭했습니다.")
            print("작업이 성공적으로 완료되었습니다.")
        except TimeoutException:
            print("btnCerNoCfm을 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step19_btnCerNoCfm")
        #     return 19
        time.sleep(3)

    except Exception:
        print("예상치 못한 오류가 발생했습니다. 증거를 저장합니다.")
        traceback.print_exc()
        if driver:
            dump_state(driver, "unexpected_error")
        return 97
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    # 로그 파일 기록 시작 (logs/run_날짜시간.log) - 콘솔 창을 닫아도 로그가 남음
    setup_logging()

    # 프로그램 시작 시 저장된 설정 불러오기
    load_config()
    
    print("=" * 60)
    print(f"{USER_NAME}님, {WORK_DESCRIPTION}")
    print("=" * 60)
    print(f"1. 랜덤 시간 실행 ({SCHEDULE_START_TIME} ~ {SCHEDULE_END_TIME})")
    print("2. 바로 실행 (TEST MODE)")
    print("3. 특정시간 실행")
    print("9. 환경설정")
    print("=" * 60)
    
    # 사용자 입력 받기
    while True:
        user_input = input("선택 (1, 2, 3 또는 9): ").strip()
        if user_input in ["1", "2", "3", "9"]:
            break
        print("올바른 선택을 입력하세요 (1, 2, 3 또는 9)")
    
    if user_input == "9":
        # 변수 설정 모드
        input_config_settings()
        print("설정 완료 후 프로그램을 다시 실행해주세요.")
        input("엔터를 누르세요...")
        sys.exit(0)
    elif user_input == "1":
        # 스케줄 계산 (랜덤)
        next_run_time = calculate_next_run_time()
        
        print("\n" + "=" * 60)
        print("작업 스케줄러 (랜덤 시간)")
        print("=" * 60)
        print(f"작업시간 : {next_run_time.strftime('%H:%M:%S')}")
        print(f"작업자 : {USER_NAME}")
        print(f"비밀번호 : {'*' * len(PASSWORD)}")
        print(f"업무내용 : {WORK_DESCRIPTION}")
        print("=" * 60)
        # 스케줄된 시간까지 대기
        wait_for_scheduled_time(next_run_time)
    elif user_input == "2":
        # 바로 시작
        print("\n" + "=" * 60)
        print("작업 시작 (테스트용)")
        print("=" * 60)
        print(f"작업자 : {USER_NAME}")
        print(f"비밀번호 : {'*' * len(PASSWORD)}")
        print(f"업무내용 : {WORK_DESCRIPTION}")
        print("=" * 60)
    else:
        # 특정 시간 입력
        while True:
            time_input = input("실행할 시간을 입력하세요 (HH:MM 형식, 예: 23:30): ").strip()
            try:
                hour, minute = map(int, time_input.split(":"))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    break
                print("올바른 시간을 입력하세요 (00:00 ~ 23:59)")
            except ValueError:
                print("올바른 형식으로 입력하세요 (HH:MM)")
        
        # 지정된 시간으로 설정
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 이미 지난 시간이면 내일로 설정
        if target_time <= now:
            target_time += timedelta(days=1)
        
        print("\n" + "=" * 60)
        print("작업 스케줄러 (특정 시간)")
        print("=" * 60)
        print(f"작업시간 : {target_time.strftime('%H:%M:%S')}")
        print(f"작업자 : {USER_NAME}")
        print(f"비밀번호 : {'*' * len(PASSWORD)}")
        print(f"업무내용 : {WORK_DESCRIPTION}")
        print("=" * 60)
        # 스케줄된 시간까지 대기
        wait_for_scheduled_time(target_time)
    
    print("\n작업을 시작합니다...")
    print("=" * 60)
    
    # 메인 작업 실행
    exit_code = main()
    
    # 작업 완료 후 사용자 입력 대기
    print("\n" + "=" * 60)
    print("작업이 완료되었습니다.")
    print("=" * 60)
    input("프로그램을 종료하려면 엔터를 누르세요...")
    
    raise SystemExit(exit_code)

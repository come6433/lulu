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
USER_NAME = "홍길동"

# 비밀번호
PASSWORD = "asdf6433!@"

# 업무 설명
WORK_DESCRIPTION = "열린시정 업무추진"

# 스케줄 설정 (랜덤 시간 범위, HH:MM 형식)
SCHEDULE_START_TIME = "23:10"  # 최소 시작 시각
SCHEDULE_END_TIME = "23:15"    # 최대 시작 시각

# 주말모드 설정
WEEKEND_START_TIME = "08:30"   # 주말 출근 시각 범위 시작
WEEKEND_START_END = "09:00"    # 주말 출근 시각 범위 끝
WORK_HOURS_MIN = 8.0           # 시작->종료 대기 최소 시간
WORK_HOURS_MAX = 9.0           # 시작->종료 대기 최대 시간
# ===================================================


# ==================== 설정 파일 관리 ====================
CONFIG_FILE = "config.json"


def load_config():
    """저장된 설정 파일 불러오기"""
    global USER_NAME, PASSWORD, WORK_DESCRIPTION
    global SCHEDULE_START_TIME, SCHEDULE_END_TIME
    global WEEKEND_START_TIME, WEEKEND_START_END, WORK_HOURS_MIN, WORK_HOURS_MAX

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                USER_NAME = config.get('USER_NAME', USER_NAME)
                PASSWORD = config.get('PASSWORD', PASSWORD)
                WORK_DESCRIPTION = config.get('WORK_DESCRIPTION', WORK_DESCRIPTION)
                SCHEDULE_START_TIME = config.get('SCHEDULE_START_TIME', SCHEDULE_START_TIME)
                SCHEDULE_END_TIME = config.get('SCHEDULE_END_TIME', SCHEDULE_END_TIME)
                WEEKEND_START_TIME = config.get('WEEKEND_START_TIME', WEEKEND_START_TIME)
                WEEKEND_START_END = config.get('WEEKEND_START_END', WEEKEND_START_END)
                WORK_HOURS_MIN = config.get('WORK_HOURS_MIN', WORK_HOURS_MIN)
                WORK_HOURS_MAX = config.get('WORK_HOURS_MAX', WORK_HOURS_MAX)
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
        'WEEKEND_START_TIME': WEEKEND_START_TIME,
        'WEEKEND_START_END': WEEKEND_START_END,
        'WORK_HOURS_MIN': WORK_HOURS_MIN,
        'WORK_HOURS_MAX': WORK_HOURS_MAX,
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
    global WEEKEND_START_TIME, WEEKEND_START_END, WORK_HOURS_MIN, WORK_HOURS_MAX

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
        user_input = input(f"평일 최소 시작 시각 (HH:MM 형식, 현재: {SCHEDULE_START_TIME}): ").strip()
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
        user_input = input(f"평일 최대 시작 시각 (HH:MM 형식, 현재: {SCHEDULE_END_TIME}): ").strip()
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

    # 주말 출근 시각 범위 시작
    while True:
        user_input = input(f"주말 출근 시각 범위 시작 (HH:MM 형식, 현재: {WEEKEND_START_TIME}): ").strip()
        if not user_input:
            break
        try:
            hour, minute = map(int, user_input.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                WEEKEND_START_TIME = f"{hour:02d}:{minute:02d}"
                break
            print("올바른 시간을 입력하세요 (00:00 ~ 23:59)")
        except ValueError:
            print("올바른 형식으로 입력하세요 (HH:MM)")

    # 주말 출근 시각 범위 끝
    while True:
        user_input = input(f"주말 출근 시각 범위 끝 (HH:MM 형식, 현재: {WEEKEND_START_END}): ").strip()
        if not user_input:
            break
        try:
            hour, minute = map(int, user_input.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                WEEKEND_START_END = f"{hour:02d}:{minute:02d}"
                break
            print("올바른 시간을 입력하세요 (00:00 ~ 23:59)")
        except ValueError:
            print("올바른 형식으로 입력하세요 (HH:MM)")

    # 근무시간 최소
    while True:
        user_input = input(f"근무시간 최소 (시간 단위, 현재: {WORK_HOURS_MIN}): ").strip()
        if not user_input:
            break
        try:
            val = float(user_input)
            if 0 <= val <= 24:
                WORK_HOURS_MIN = val
                break
            print("0~24 사이의 숫자를 입력하세요")
        except ValueError:
            print("올바른 숫자를 입력하세요")

    # 근무시간 최대
    while True:
        user_input = input(f"근무시간 최대 (시간 단위, 현재: {WORK_HOURS_MAX}): ").strip()
        if not user_input:
            break
        try:
            val = float(user_input)
            if 0 <= val <= 24:
                WORK_HOURS_MAX = val
                break
            print("0~24 사이의 숫자를 입력하세요")
        except ValueError:
            print("올바른 숫자를 입력하세요")

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


# ==================== 공통 함수 ====================

def login_and_auth(driver, wait):
    """로그인 버튼 클릭부터 GPKI 인증 완료까지. 성공 시 True, 실패 시 False."""
    try:
        print("페이지 로드 중...")
        driver.get("https://jeonbuk.insarang.go.kr/nexin/index.html")
        print("페이지 로드 완료")
    except TimeoutException:
        print("페이지 로드 타임아웃 - 계속 진행합니다.")
    except Exception as e:
        print(f"페이지 탐색 중 오류 발생: {e}")
        traceback.print_exc()
        return False

    # 1) 로그인 버튼 클릭
    login_xpath = '//*[@id="mainframe.WorkFrame.form.divCenter.form.divLogin.form.btnLogin:icontext"]'
    print("로그인 버튼을 클릭합니다...")
    try:
        click_element_when_ready(driver, By.XPATH, login_xpath, timeout=10)
    except TimeoutException:
        print("로그인 버튼을 찾지 못했습니다.")
        dump_state(driver, "login_btn_not_found")
        return False
    print("로그인 버튼 클릭 완료. GPKI 인증 iframe(#dscert) 로드를 대기합니다...")

    # 2) #dscert iframe 대기 후 진입
    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "dscert")))
        print("#dscert iframe 안으로 전환했습니다.")
    except TimeoutException:
        print("#dscert iframe을 찾지 못했습니다.")
        dump_state(driver, "step2_no_iframe")
        return False

    # 3) 사용자 검색 (폴링)
    name = USER_NAME
    print(f"iframe 안에서 제목에 '{name}'을(를) 포함하는 요소를 검색합니다 (최대 20초)...")
    matches = []
    search_deadline = time.time() + 20
    while time.time() < search_deadline:
        matches = driver.find_elements(By.XPATH, f"//*[contains(@title, \"{name}\")]")
        if matches:
            break
        time.sleep(0.5)

    if not matches:
        print("사용자를 찾지 못했습니다.")
        dump_state(driver, "step3_user_not_found")
        driver.switch_to.default_content()
        return False

    print(f"사용자 요소 {len(matches)}개를 찾았습니다.")

    # SPAN 선호
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

    # 클릭 (stale 대응)
    driver.execute_script("arguments[0].scrollIntoView(true);", target)
    try:
        target.click()
    except Exception as click_err:
        print(f"일반 클릭 실패({click_err}). JS 클릭 시도.")
        target = driver.find_element(By.XPATH, f"//*[contains(@title, \"{name}\")]")
        driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", target)
    print(f"사용자 요소를 클릭했습니다. (tag={target.tag_name})")

    # 4) 비밀번호 입력 (stale 대응 재시도)
    pw_ok = False
    for attempt in range(1, 4):
        try:
            pw_input = wait.until(EC.presence_of_element_located((By.ID, "input_cert_pw")))
            pw_input.clear()
            pw_input.send_keys(PASSWORD)
            entered_len = driver.execute_script("return arguments[0].value.length;", pw_input)
            if entered_len == len(PASSWORD):
                print(f"비밀번호를 입력했습니다. (시도 {attempt}, 글자 수: {entered_len})")
                pw_ok = True
                break
            print(f"비밀번호 입력 검증 실패 (시도 {attempt}, 입력됨: {entered_len}자). 재시도.")
        except Exception as e:
            print(f"비밀번호 입력 시도 {attempt} 실패 ({type(e).__name__}). 재시도.")
            time.sleep(0.5)
    if not pw_ok:
        print("비밀번호 입력에 최종 실패했습니다.")
        dump_state(driver, "step4_pw_field")
        driver.switch_to.default_content()
        return False

    # 5) 확인 버튼 클릭 (stale 대응 재시도)
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
            print(f"확인 버튼 클릭 시도 {attempt} 실패 ({type(e).__name__}). 재시도.")
            time.sleep(0.5)
    if not confirm_ok:
        dump_state(driver, "step5_confirm_btn")
        driver.switch_to.default_content()
        return False

    # 기본 문서로 복귀
    driver.switch_to.default_content()
    print("기본 문서로 복귀했습니다.")
    time.sleep(3)

    # 팝업 창 처리
    original_window = driver.current_window_handle
    if len(driver.window_handles) > 1:
        print("여러 창이 감지되었습니다. 팝업 창으로 전환합니다...")
        for window in driver.window_handles:
            if window != original_window:
                driver.switch_to.window(window)
                time.sleep(1)
                try:
                    driver.close()
                except Exception:
                    pass
        driver.switch_to.window(original_window)
        time.sleep(1)

    return True


def solve_captcha(driver, wait, prefix):
    """캡차 인식. prefix: 'tatAtdc03001P12' (종료) or 'tatAtdc03001P14' (시작). 성공 시 True."""
    max_retries = 3
    retry_count = 0
    captcha_success = False
    captcha_result = None

    while retry_count < max_retries and not captcha_success:
        if retry_count > 0:
            print(f"\n재시도 {retry_count}/{max_retries}...")
            btn_ch_refresh_xpath = f'//*[@id="mainframe.WorkFrame.{prefix}.form.divStep3.form.btnChRefresh:icontext"]'
            try:
                click_element_when_ready(driver, By.XPATH, btn_ch_refresh_xpath, timeout=10)
                print("btnChRefresh를 클릭했습니다.")
                time.sleep(2)
            except TimeoutException:
                print("btnChRefresh를 찾지 못했거나 클릭할 수 없습니다.")
                dump_state(driver, f"captcha_refresh_fail_{prefix}")
                return False

        # 이미지 다운로드
        image_xpath = f'//*[@id="mainframe.WorkFrame.{prefix}.form.divStep3.form.divChCode.imagearea:image"]'
        try:
            img_element = wait.until(EC.presence_of_element_located((By.XPATH, image_xpath)))
            img_src = img_element.get_attribute('src')
            if img_src:
                if img_src.startswith('data:'):
                    import base64
                    header, data = img_src.split(',')
                    img_data = base64.b64decode(data)
                    with open('target.png', 'wb') as f:
                        f.write(img_data)
                    print("이미지를 target.png로 저장했습니다 (데이터 URL).")
                else:
                    import urllib.request
                    urllib.request.urlretrieve(img_src, 'target.png')
                    print("이미지를 target.png로 저장했습니다.")
            else:
                print("이미지 src 속성을 찾지 못했습니다.")
                dump_state(driver, f"captcha_no_img_src_{prefix}")
                return False
        except TimeoutException:
            print("이미지 요소를 찾지 못했습니다.")
            dump_state(driver, f"captcha_no_image_{prefix}")
            return False

        # capcrack 실행
        print("capcrack.py를 실행하여 captcha를 인식합니다...")
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                [sys.executable, "capcrack.py"],
                cwd=script_dir,
                capture_output=True,
                timeout=60
            )
            try:
                capcrack_output = result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    capcrack_output = result.stdout.decode('cp949')
                except UnicodeDecodeError:
                    capcrack_output = result.stdout.decode('utf-8', errors='ignore')

            print(f"capcrack 출력: {capcrack_output}")

            if "인식 결과" in capcrack_output:
                parts = capcrack_output.split("인식 결과")
                if len(parts) > 1:
                    result_text = parts[-1].strip()
                    if ":" in result_text:
                        captcha_result = result_text.split(":", 1)[-1].strip()
                    else:
                        captcha_result = result_text.strip()

                    print(f"인식된 captcha: {captcha_result}")

                    if "[UNK]" in captcha_result:
                        print("유효하지 않은 captcha: [UNK]가 포함됨. 재시도...")
                        retry_count += 1
                        continue
                    elif not captcha_result.isdigit() or len(captcha_result) != 5:
                        print(f"유효하지 않은 captcha: 5자리 숫자 필요, '{captcha_result}' 받음. 재시도...")
                        retry_count += 1
                        continue
                    else:
                        print(f"유효한 captcha 결과: {captcha_result}")
                        captcha_success = True
                else:
                    print("capcrack 출력에서 captcha 결과를 파싱할 수 없습니다.")
                    dump_state(driver, f"captcha_parse_fail_{prefix}")
                    return False
            else:
                print("capcrack 출력에서 captcha 결과를 찾지 못했습니다.")
                dump_state(driver, f"captcha_no_result_{prefix}")
                return False

        except subprocess.TimeoutExpired:
            print("capcrack.py가 타임아웃되었습니다.")
            dump_state(driver, f"captcha_capcrack_timeout_{prefix}")
            return False
        except Exception as e:
            print(f"capcrack.py 실행 중 오류: {e}")
            traceback.print_exc()
            dump_state(driver, f"captcha_capcrack_error_{prefix}")
            return False

    if not captcha_success:
        print(f"{max_retries}회 재시도 후에도 captcha를 인식하지 못했습니다.")
        dump_state(driver, f"captcha_fail_{prefix}")
        return False

    # 입력 필드에 입력
    edt_ch_no_cfm_xpath = f'//*[@id="mainframe.WorkFrame.{prefix}.form.divStep3.form.edtChNoCfm:input"]'
    try:
        ch_no_input = wait.until(EC.presence_of_element_located((By.XPATH, edt_ch_no_cfm_xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", ch_no_input)
        time.sleep(0.5)
        try:
            ch_no_input.click()
        except:
            driver.execute_script("arguments[0].click();", ch_no_input)
        time.sleep(0.5)
        ch_no_input.clear()
        ch_no_input.send_keys(captcha_result)
        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
        """, ch_no_input)
        print(f"captcha 결과 '{captcha_result}'를 입력했습니다.")
        time.sleep(1)
        input_value = driver.execute_script("return arguments[0].value;", ch_no_input)
        print(f"입력 확인: {input_value}")
    except TimeoutException:
        print("captcha 입력 필드를 찾지 못했습니다.")
        dump_state(driver, f"captcha_input_not_found_{prefix}")
        return False

    time.sleep(2)
    # 확인 버튼 클릭
    btn_cer_no_cfm_xpath = f'//*[@id="mainframe.WorkFrame.{prefix}.form.divStep3.form.btnCerNoCfm:icontext"]'
    try:
        click_element_when_ready(driver, By.XPATH, btn_cer_no_cfm_xpath, timeout=10)
        print("captcha 확인 버튼을 클릭했습니다.")
        return True
    except TimeoutException:
        print("captcha 확인 버튼을 찾지 못했거나 클릭할 수 없습니다.")
        dump_state(driver, f"captcha_confirm_fail_{prefix}")
        return False


def run_end_cycle():
    """종료 사이클: 로그인 → btnEndReg → 근무내용 → 캡차(P12) → 완료. 성공 시 0."""
    driver = None
    try:
        print("Edge 웹드라이버를 생성하는 중...")
        driver = create_driver()
        print("웹드라이버가 생성되었습니다.")
    except Exception as e:
        print(f"웹드라이버 생성 중 오류: {e}")
        traceback.print_exc()
        return 99

    wait = WebDriverWait(driver, 15)

    try:
        if not login_and_auth(driver, wait):
            return 1

        # 6) btnEndReg 클릭
        btn_end_reg_xpath = '//*[@id="mainframe.WorkFrame.form.divMain.form.divMain.form.divCont0.form.btnEndReg:icontext"]'
        try:
            try:
                driver.switch_to.default_content()
                time.sleep(0.3)
            except:
                pass
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

        time.sleep(5)

        # 캡차 인식
        if not solve_captcha(driver, wait, "tatAtdc03001P12"):
            return 17

        print("종료 사이클이 성공적으로 완료되었습니다.")
        return 0

    except Exception:
        print("예상치 못한 오류가 발생했습니다. 증거를 저장합니다.")
        traceback.print_exc()
        if driver:
            dump_state(driver, "unexpected_error_end")
        return 97
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def run_start_cycle():
    """시작 사이클: 로그인 → btnStartReg → btnNextStep2(P14) → 캡차(P14) → 완료. 성공 시 0."""
    driver = None
    try:
        print("Edge 웹드라이버를 생성하는 중...")
        driver = create_driver()
        print("웹드라이버가 생성되었습니다.")
    except Exception as e:
        print(f"웹드라이버 생성 중 오류: {e}")
        traceback.print_exc()
        return 99

    wait = WebDriverWait(driver, 15)

    try:
        if not login_and_auth(driver, wait):
            return 1

        # btnStartReg 클릭
        btn_start_reg_xpath = '//*[@id="mainframe.WorkFrame.form.divMain.form.divMain.form.divCont0.form.btnStartReg:icontext"]'
        try:
            try:
                driver.switch_to.default_content()
                time.sleep(0.3)
            except:
                pass
            btn_start = wait.until(EC.presence_of_element_located((By.XPATH, btn_start_reg_xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", btn_start)
            time.sleep(1)
            click_element_when_ready(driver, By.XPATH, btn_start_reg_xpath, timeout=10)
            print("btnStartReg를 클릭했습니다.")
        except TimeoutException:
            print("btnStartReg를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step_start_btnStartReg")
            return 20

        # btnNextStep2 클릭 (P14)
        btn_next_step2_xpath = '//*[@id="mainframe.WorkFrame.tatAtdc03001P14.form.divStep1.form.btnNextStep2:icontext"]'
        try:
            click_element_when_ready(driver, By.XPATH, btn_next_step2_xpath, timeout=10)
            print("btnNextStep2(P14)를 클릭했습니다.")
        except TimeoutException:
            print("btnNextStep2(P14)를 찾지 못했거나 클릭할 수 없습니다.")
            dump_state(driver, "step_start_btnNextStep2")
            return 21

        time.sleep(5)

        # 캡차 인식 (P14)
        if not solve_captcha(driver, wait, "tatAtdc03001P14"):
            return 22

        print("시작 사이클이 성공적으로 완료되었습니다.")
        return 0

    except Exception:
        print("예상치 못한 오류가 발생했습니다. 증거를 저장합니다.")
        traceback.print_exc()
        if driver:
            dump_state(driver, "unexpected_error_start")
        return 97
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def wait_with_countdown(target_time, log_interval=300):
    """목표 시각까지 대기. 콘솔에는 1초마다 카운트다운, 로그에는 log_interval초마다만 기록."""
    last_log_time = 0
    while True:
        now = datetime.now()
        if now >= target_time:
            break
        remaining = target_time - now
        remaining_seconds = int(remaining.total_seconds())
        hours, remainder = divmod(remaining_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        status_msg = f"대기중... 남은시간 : {hours}시간 {minutes}분 {seconds:02d}초"
        print(status_msg, end='\r', flush=True)

        # 로그에는 일정 간격으로만 기록
        if time.time() - last_log_time >= log_interval:
            print(f"\n[로그] 대기 중... 목표: {target_time.strftime('%Y-%m-%d %H:%M:%S')}, 남은시간: {hours}시간 {minutes}분 {seconds}초")
            last_log_time = time.time()

        time.sleep(1)
    print()  # 카운트다운 줄 바꿈


def build_weekend_plan(day_choices):
    """요일 선택에 따른 실행 계획 생성. 반환: [(요일인덱스, 'end'|'full'), ...]
    요일인덱스: 0=월, 4=금, 5=토, 6=일
    """
    plan = []
    if 'fri' in day_choices:
        plan.append((4, 'end'))  # 금요일 종료만
    if 'sat' in day_choices:
        plan.append((5, 'full'))  # 토요일 시작+종료
    if 'sun' in day_choices:
        plan.append((6, 'full'))  # 일요일 시작+종료
    return plan


def main():
    """기존 호환용 - 종료 사이클만 실행."""
    return run_end_cycle()


if __name__ == "__main__":
    # 로그 파일 기록 시작 (logs/run_날짜시간.log) - 콘솔 창을 닫아도 로그가 남음
    setup_logging()

    # 프로그램 시작 시 저장된 설정 불러오기
    load_config()

    print("=" * 60)
    print(f"{USER_NAME}님, {WORK_DESCRIPTION}")
    print("=" * 60)
    print("1. TEST모드 (즉시실행, 종료만)")
    print("2. TEST모드 (즉시실행, 시작-종료)")
    print("3. 평일모드 (종료만, 랜덤시간)")
    print("4. 주말모드 (시작-종료)")
    print("9. 환경설정")
    print("=" * 60)

    # 사용자 입력 받기
    while True:
        user_input = input("선택 (1, 2, 3, 4 또는 9): ").strip()
        if user_input in ["1", "2", "3", "4", "9"]:
            break
        print("올바른 선택을 입력하세요 (1, 2, 3, 4 또는 9)")

    if user_input == "9":
        # 변수 설정 모드
        input_config_settings()
        print("설정 완료 후 프로그램을 다시 실행해주세요.")
        input("엔터를 누르세요...")
        sys.exit(0)

    elif user_input == "1":
        # TEST: 종료만 즉시 실행
        print("\n" + "=" * 60)
        print("TEST모드: 종료 사이클 즉시 실행")
        print("=" * 60)
        print(f"작업자 : {USER_NAME}")
        print(f"업무내용 : {WORK_DESCRIPTION}")
        print("=" * 60)
        exit_code = run_end_cycle()

    elif user_input == "2":
        # TEST: 시작-종료 즉시 실행 (대기시간 입력)
        print("\n" + "=" * 60)
        print("TEST모드: 시작-종료 사이클 즉시 실행")
        print("=" * 60)
        while True:
            wait_input = input("시작 후 종료까지 대기 시간 (분 단위, 예: 5): ").strip()
            try:
                wait_minutes = int(wait_input)
                if wait_minutes >= 0:
                    break
                print("0 이상의 숫자를 입력하세요.")
            except ValueError:
                print("올바른 숫자를 입력하세요.")
        print(f"작업자 : {USER_NAME}")
        print(f"업무내용 : {WORK_DESCRIPTION}")
        print(f"대기시간 : {wait_minutes}분")
        print("=" * 60)

        # 시작 사이클
        print("\n[1/2] 시작 사이클 실행...")
        start_result = run_start_cycle()
        if start_result != 0:
            print(f"시작 사이클 실패 (코드: {start_result})")
            exit_code = start_result
        else:
            print(f"\n{wait_minutes}분 대기 후 종료 사이클을 실행합니다...")
            time.sleep(wait_minutes * 60)
            print("\n[2/2] 종료 사이클 실행...")
            exit_code = run_end_cycle()

    elif user_input == "3":
        # 평일모드: 기존 랜덤 시간에 종료만
        next_run_time = calculate_next_run_time()
        print("\n" + "=" * 60)
        print("평일모드: 종료 사이클 (랜덤 시간)")
        print("=" * 60)
        print(f"작업시간 : {next_run_time.strftime('%H:%M:%S')}")
        print(f"작업자 : {USER_NAME}")
        print(f"업무내용 : {WORK_DESCRIPTION}")
        print("=" * 60)
        wait_with_countdown(next_run_time)
        exit_code = run_end_cycle()

    elif user_input == "4":
        # 주말모드: 요일 선택
        print("\n" + "=" * 60)
        print("주말모드: 시작-종료 사이클")
        print("=" * 60)
        print("실행할 요일을 선택하세요:")
        print("1. 토요일만")
        print("2. 일요일만")
        print("3. 토요일 + 일요일")
        print("4. 금요일 + 토요일")
        print("5. 금요일 + 일요일")
        print("6. 금요일 + 토요일 + 일요일")
        print("=" * 60)

        while True:
            day_input = input("선택 (1-6): ").strip()
            if day_input in ["1", "2", "3", "4", "5", "6"]:
                break
            print("올바른 선택을 입력하세요 (1-6)")

        day_map = {
            "1": ["sat"],
            "2": ["sun"],
            "3": ["sat", "sun"],
            "4": ["fri", "sat"],
            "5": ["fri", "sun"],
            "6": ["fri", "sat", "sun"],
        }
        selected_days = day_map[day_input]
        plan = build_weekend_plan(selected_days)

        print(f"\n선택된 요일: {', '.join(selected_days)}")
        print(f"주말 출근시각 범위: {WEEKEND_START_TIME} ~ {WEEKEND_START_END}")
        print(f"근무시간 범위: {WORK_HOURS_MIN} ~ {WORK_HOURS_MAX} 시간")
        print("=" * 60)

        today = datetime.now().weekday()  # 0=월, 4=금, 5=토, 6=일
        exit_code = 0

        for day_idx, cycle_type in plan:
            day_name = ["월", "화", "수", "목", "금", "토", "일"][day_idx]

            # 이미 지난 요일 스킵
            if day_idx < today:
                print(f"\n[스킵] {day_name}요일은 이미 지났습니다.")
                continue

            # 당일인 경우 시각 체크
            if day_idx == today:
                now = datetime.now()
                if cycle_type == 'end':
                    # 종료 시각이 이미 지났으면 스킵
                    end_h, end_m = map(int, SCHEDULE_END_TIME.split(":"))
                    end_time_today = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                    if now > end_time_today:
                        print(f"\n[스킵] {day_name}요일 종료 시각({SCHEDULE_END_TIME})이 이미 지났습니다.")
                        continue
                else:  # full
                    # 출근 시각이 이미 지났으면 즉시 실행
                    start_h, start_m = map(int, WEEKEND_START_TIME.split(":"))
                    start_time_today = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                    if now > start_time_today:
                        print(f"\n[즉시실행] {day_name}요일 출근 시각({WEEKEND_START_TIME})이 지났으므로 즉시 실행합니다.")

            # 다음 해당 요일까지 대기
            if day_idx > today:
                days_ahead = day_idx - today
                target_date = datetime.now() + timedelta(days=days_ahead)
            else:
                target_date = datetime.now()

            if cycle_type == 'end':
                # 금요일 종료 사이클
                end_h, end_m = map(int, SCHEDULE_START_TIME.split(":"))
                end_target = target_date.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                if day_idx == today and datetime.now() >= end_target:
                    # 이미 지났으면 즉시 실행
                    pass
                else:
                    print(f"\n{day_name}요일 종료 사이클 대기 중... 목표: {end_target.strftime('%Y-%m-%d %H:%M')}")
                    wait_with_countdown(end_target)

                print(f"\n[{day_name}요일] 종료 사이클 실행...")
                result = run_end_cycle()
                if result != 0:
                    print(f"{day_name}요일 종료 사이클 실패 (코드: {result})")
                    exit_code = result
                else:
                    print(f"{day_name}요일 종료 사이클 완료.")

            else:  # full (시작 + 종료)
                # 시작 사이클
                start_h, start_m = map(int, WEEKEND_START_TIME.split(":"))
                start_target = target_date.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                if day_idx == today and datetime.now() >= start_target:
                    pass  # 즉시 실행
                else:
                    print(f"\n{day_name}요일 시작 사이클 대기 중... 목표: {start_target.strftime('%Y-%m-%d %H:%M')}")
                    wait_with_countdown(start_target)

                print(f"\n[{day_name}요일] 시작 사이클 실행...")
                start_result = run_start_cycle()
                if start_result != 0:
                    print(f"{day_name}요일 시작 사이클 실패 (코드: {start_result}). 종료 사이클을 건너뜁니다.")
                    exit_code = start_result
                    continue

                # 근무시간 대기
                work_hours = random.uniform(WORK_HOURS_MIN, WORK_HOURS_MAX)
                work_seconds = int(work_hours * 3600)
                print(f"\n근무시간 대기: {work_hours:.2f}시간 ({work_seconds}초)")
                end_target = datetime.now() + timedelta(seconds=work_seconds)
                print(f"종료 사이클 예정 시각: {end_target.strftime('%Y-%m-%d %H:%M:%S')}")
                wait_with_countdown(end_target)

                print(f"\n[{day_name}요일] 종료 사이클 실행...")
                end_result = run_end_cycle()
                if end_result != 0:
                    print(f"{day_name}요일 종료 사이클 실패 (코드: {end_result})")
                    exit_code = end_result
                else:
                    print(f"{day_name}요일 시작-종료 사이클 완료.")

        print("\n" + "=" * 60)
        print("주말모드 전체 완료.")
        print("=" * 60)

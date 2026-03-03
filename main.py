import os

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# =============================
# KONFIGURASI
# =============================
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

URL_LOGIN = "https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F"
URL_DAFTAR_KULIAH = "https://ethol.pens.ac.id/mahasiswa/matakuliah"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def cek_semua_absen():
    logging.info("Menyiapkan Chrome headless...")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = None

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 60)

        logging.info("Membuka halaman login...")
        driver.get(URL_LOGIN)

        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "submit").click()

        logging.info("Menunggu login berhasil...")
        wait.until(EC.url_contains("ethol.pens.ac.id"))
        logging.info("Login berhasil")

        driver.get(URL_DAFTAR_KULIAH)
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
        ))

        logging.info("Mengambil daftar mata kuliah...")
        judul_matkul = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@class, 'card-title-mobile')]")
        ))

        nama_matkul_list = sorted(
            list({j.text.strip() for j in judul_matkul if j.text.strip()})
        )

        if not nama_matkul_list:
            logging.warning("Tidak ada mata kuliah ditemukan.")
            return

        logging.info(f"Ditemukan {len(nama_matkul_list)} mata kuliah")

        for nama_matkul in nama_matkul_list:
            logging.info(f"Mengecek: {nama_matkul}")

            try:
                driver.get(URL_DAFTAR_KULIAH)
                wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
                ))

                tombol_akses = wait.until(EC.element_to_be_clickable(
                    (By.XPATH,
                     f"//div[contains(@class,'card-matkul') and .//span[normalize-space()='{nama_matkul}']]//button[contains(.,'Akses Kuliah')]")
                ))

                driver.execute_script("arguments[0].click();", tombol_akses)

                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//button[normalize-space(span)='Aturan Presensi']")
                ))

                try:
                    tombol_presensi = driver.find_element(
                        By.XPATH,
                        "//button[normalize-space(span)='Presensi' and not(@disabled)]"
                    )

                    if tombol_presensi.is_displayed() and tombol_presensi.is_enabled():
                        tombol_presensi.click()
                        logging.warning(f"PRESENSI BERHASIL DIKLIK: {nama_matkul}")
                        return

                except NoSuchElementException:
                    logging.info("Presensi belum dibuka.")

            except TimeoutException:
                logging.warning("Timeout saat membuka mata kuliah.")

    except WebDriverException as e:
        logging.error(f"WebDriver error: {e}")

    finally:
        if driver:
            driver.quit()
            logging.info("Browser ditutup.")

# =============================
# ENTRY POINT
# =============================
if __name__ == "__main__":
    logging.info("Memulai pengecekan...")
    cek_semua_absen()
    logging.info("Selesai.")
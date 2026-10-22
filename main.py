import datetime
import os
import requests

# ดึงค่า Secrets จาก Environment Variables ของ GitHub
LINE_ACCESS_TOKEN = os.getenv("Vg6lnK+q5FteaOna1xpqQA9i9uEb/HXRj3tY3lWKRGb/TunJEzpBXYahlWe+FvI4dJtUQHqXTl5VPiCgp9sOMnwFSOsd0pSsl+TgE9dHXLAfEvroTPT/xe0w8D5ojFpCLeX2LK1s2SRH5bz0r23fYQdB04t89/1O/w1cDnyilFU=")
USER_ID = os.getenv("Ub9e1bb74f53b02db8fdd6590f8b8c26d")
WEATHER_API_KEY = os.getenv("f7fb6371cdfa8941b31a9920acb6569e")
CITY_NAME = "Pathum Thani"

WEEKLY_SCHEDULE = {
    0: ["10:00 - 12:00 น. | คลาสเรียนวิชาเช้า", "19:00 น. | ออกกำลังกาย / ทบทวนโค้ด"],
    1: ["09:00 - 16:00 น. | คลาสเรียนทั้งวัน", "20:00 น. | เคลียร์การบ้าน / ทำแล็บ"],
    2: ["13:00 - 16:00 น. | แล็บปฏิบัติการ", "21:00 น. | พักผ่อน / เล่นเกม"],
    3: ["09:00 - 12:00 น. | เรียนเลกเชอร์", "15:00 น. | นัดคุยงานโปรเจกต์"],
    4: ["10:00 - 15:00 น. | เรียนวิชาเอก", "18:00 น. | สรุปงานประจำสัปดาห์"],
    5: ["ช่วงบ่าย | ซักผ้า / ทำความสะอาดห้อง", "20:00 น. | ดูหนัง / พักผ่อน"],
    6: ["ช่วงเย็น | วางแผนงานสำหรับสัปดาห์หน้า", "23:00 น. | เข้านอนไวเตรียมเริ่มสัปดาห์ใหม่"]
}

def get_current_date():
    # เวลาในเซิร์ฟเวอร์ GitHub เป็น UTC จึงบวก 7 ชั่วโมงให้ตรงกับเวลาไทย
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    days_th = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months_th = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                 "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    day_name = days_th[now.weekday()]
    return f"วัน{day_name}ที่ {now.day} {months_th[now.month]} {now.year + 543}", now.weekday()

def get_today_tasks(day_index):
    tasks = WEEKLY_SCHEDULE.get(day_index, ["ไม่มีนัดหมายพิเศษ"])
    return "\n".join([f"  • {task}" for task in tasks])

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric&lang=th"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            return (
                f"  • อุณหภูมิ: {temp}°C (รู้สึกเหมือน {feels_like}°C)\n"
                f"  • สภาพอากาศ: {desc}\n"
                f"  • ความชื้น: {humidity}%"
            )
        return f"  • ⚠️ ไม่สามารถดึงสภาพอากาศได้ (Code: {res.status_code})"
    except Exception as e:
        return f"  • ⚠️ เกิดข้อผิดพลาด: {e}"

def send_line_briefing(message_text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message_text}]
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print("✅ ส่งข้อความ Morning Briefing เข้า LINE สำเร็จ!")
    else:
        print(f"❌ เกิดข้อผิดพลาด: {res.status_code}, {res.text}")

if __name__ == "__main__":
    date_str, today_index = get_current_date()
    weather_info = get_weather()
    tasks_info = get_today_tasks(today_index)
    
    full_message = (
        "☀️ MORNING BRIEFING (Cloud Runner) ☀️\n"
        f"📅 {date_str}\n"
        "--------------------------------\n"
        f"📍 พยากรณ์อากาศ ({CITY_NAME}):\n"
        f"{weather_info}\n"
        "--------------------------------\n"
        "📝 กำหนดการ / สิ่งที่ต้องทำวันนี้:\n"
        f"{tasks_info}\n"
        "--------------------------------\n"
        "✨ ขอให้วันนี้เป็นวันที่ราบรื่นและสดใสนะครับ!"
    )
    send_line_briefing(full_message)
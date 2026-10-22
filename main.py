import datetime
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# 1. Credentials จาก GitHub Secrets
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GCP_SA_KEY = os.getenv("GCP_SA_KEY")
CITY_NAME = "Pathum Thani"

# ตารางเรียนตามตารางลงทะเบียน (0 = จันทร์, ..., 6 = อาทิตย์)
WEEKLY_SCHEDULE = {
    0: [
        {"time": "09:00 - 12:00", "subject": "TCP/IP Networks", "room": "ห้อง 16307"},
        {"time": "13:00 - 20:00", "subject": "Machine Learning", "room": "ห้อง 16306"},
    ],
    1: [
        {
            "time": "ทั้งวัน",
            "subject": "ไม่มีเรียน (Free Day)",
            "room": "พักผ่อน / ทบทวนเนื้อหา",
        }
    ],
    2: [
        {
            "time": "09:00 - 12:00",
            "subject": "Internet of Things",
            "room": "ห้อง 16203",
        },
        {
            "time": "15:00 - 17:00",
            "subject": "Entrepreneurship",
            "room": "ห้อง บธ-2 BA 2406",
        },
        {
            "time": "19:00 - 21:00",
            "subject": "Computer Network Lab",
            "room": "ห้อง 16204",
        },
    ],
    3: [
        {
            "time": "09:00 - 12:00",
            "subject": "Server Programming",
            "room": "ห้อง 16306",
        },
        {
            "time": "13:00 - 18:00",
            "subject": "Computer Software Lab",
            "room": "ห้อง 16306",
        },
    ],
    4: [
        {
            "time": "10:00 - 12:00",
            "subject": "Computer Network Lab",
            "room": "ห้อง 16204",
        },
        {
            "time": "13:00 - 20:00",
            "subject": "Software Engineering",
            "room": "ห้อง 16202",
        },
    ],
    5: [
        {
            "time": "15:00 - 18:00",
            "subject": "Internet of Things",
            "room": "ห้อง 16203",
        },
        {
            "time": "18:00 - 21:00",
            "subject": "Server Programming",
            "room": "ห้อง 16207",
        },
    ],
    6: [
        {
            "time": "ทั้งวัน",
            "subject": "วันอาทิตย์ (Holiday)",
            "room": "พักผ่อนเตรียมลุยสัปดาห์ใหม่",
        }
    ],
}


def get_current_date():
  now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
  days_th = [
      "จันทร์",
      "อังคาร",
      "พุธ",
      "พฤหัสบดี",
      "ศุกร์",
      "เสาร์",
      "อาทิตย์",
  ]
  months_th = [
      "",
      "ม.ค.",
      "ก.พ.",
      "มี.ค.",
      "เม.ย.",
      "พ.ค.",
      "มิ.ย.",
      "ก.ค.",
      "ส.ค.",
      "ก.ย.",
      "ต.ค.",
      "พ.ย.",
      "ธ.ค.",
  ]
  day_name = days_th[now.weekday()]
  return (
      f"วัน{day_name}ที่ {now.day} {months_th[now.month]} {now.year + 543}",
      now.weekday(),
  )


def get_weather_data():
  url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric&lang=th"
  try:
    res = requests.get(url)
    if res.status_code == 200:
      data = res.json()
      return {
          "temp": f"{round(data['main']['temp'], 1)}°C",
          "feels_like": f"{round(data['main']['feels_like'], 1)}°C",
          "desc": data["weather"][0]["description"],
          "humidity": f"{data['main']['humidity']}%",
      }
    return {
        "temp": "-",
        "feels_like": "-",
        "desc": "ไม่พบข้อมูล",
        "humidity": "-",
    }
  except:
    return {"temp": "-", "feels_like": "-", "desc": "ขัดข้อง", "humidity": "-"}


def get_pending_tasks():
  """ดึงรายการงานค้างที่สถานะเป็น Pending จาก Google Sheets"""
  try:
    if not GCP_SA_KEY:
      return []
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    sa_info = json.loads(GCP_SA_KEY)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_info, scope)
    client = gspread.authorize(creds)

    sheet = client.open("DailyTasks").sheet1
    records = sheet.get_all_records()

    pending_tasks = []
    for row in records:
      status = str(row.get("Status", "")).strip().lower()
      if status == "pending":
        task_name = row.get("Task", "ไม่มีชื่องาน")
        deadline = row.get("Deadline", "ไม่ระบุวัน")
        pending_tasks.append({"task": task_name, "deadline": deadline})
    return pending_tasks
  except Exception as e:
    print(f"เกิดข้อผิดพลาดในการอ่าน Google Sheets: {e}")
    return []


def build_flex_message(date_str, today_index, weather, tasks_from_sheet):
  schedules = WEEKLY_SCHEDULE.get(today_index, [])

  # ส่วนแสดงตารางเรียน
  schedule_components = []
  for item in schedules:
    schedule_components.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "spacing": "xs",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "⏰ " + item["time"],
                        "size": "xs",
                        "color": "#06c755",
                        "weight": "bold",
                        "flex": 0,
                    },
                    {
                        "type": "text",
                        "text": " | " + item["room"],
                        "size": "xs",
                        "color": "#888888",
                        "flex": 1,
                    },
                ],
            },
            {
                "type": "text",
                "text": item["subject"],
                "size": "sm",
                "weight": "bold",
                "color": "#333333",
                "wrap": True,
            },
        ],
    })

  # ส่วนแสดง To-do list จาก Google Sheets
  task_components = []
  if tasks_from_sheet:
    for t in tasks_from_sheet:
      task_components.append({
          "type": "box",
          "layout": "horizontal",
          "margin": "sm",
          "contents": [
              {
                  "type": "text",
                  "text": "📌 " + t["task"],
                  "size": "xs",
                  "color": "#333333",
                  "flex": 4,
                  "wrap": True,
              },
              {
                  "type": "text",
                  "text": t["deadline"],
                  "size": "xs",
                  "color": "#ff5555",
                  "weight": "bold",
                  "align": "end",
                  "flex": 2,
              },
          ],
      })
  else:
    task_components.append({
        "type": "text",
        "text": "🎉 ไม่มีงานค้างในระบบ!",
        "size": "xs",
        "color": "#888888",
        "margin": "sm",
    })

  flex_payload = {
      "type": "flex",
      "altText": "☀️ รายงานสรุป Morning Briefing ประจำวัน",
      "contents": {
          "type": "bubble",
          "size": "mega",
          "header": {
              "type": "box",
              "layout": "vertical",
              "backgroundColor": "#06c755",
              "paddingTop": "20px",
              "paddingBottom": "20px",
              "contents": [
                  {
                      "type": "text",
                      "text": "MORNING BRIEFING",
                      "color": "#ffffff",
                      "weight": "bold",
                      "size": "xs",
                  },
                  {
                      "type": "text",
                      "text": date_str,
                      "color": "#ffffff",
                      "weight": "bold",
                      "size": "lg",
                      "margin": "sm",
                  },
              ],
          },
          "body": {
              "type": "box",
              "layout": "vertical",
              "paddingAll": "20px",
              "contents": [
                  # กล่องสภาพอากาศ
                  {
                      "type": "box",
                      "layout": "horizontal",
                      "backgroundColor": "#f8f9fa",
                      "cornerRadius": "12px",
                      "paddingAll": "14px",
                      "contents": [
                          {
                              "type": "box",
                              "layout": "vertical",
                              "flex": 3,
                              "contents": [
                                  {
                                      "type": "text",
                                      "text": (
                                          f"📍 ปทุมธานี • {weather['desc']}"
                                      ),
                                      "size": "xs",
                                      "color": "#666666",
                                  },
                                  {
                                      "type": "text",
                                      "text": weather["temp"],
                                      "size": "xxl",
                                      "weight": "bold",
                                      "color": "#111111",
                                      "margin": "xs",
                                  },
                              ],
                          },
                          {
                              "type": "box",
                              "layout": "vertical",
                              "flex": 2,
                              "justifyContent": "center",
                              "alignItems": "flex-end",
                              "contents": [
                                  {
                                      "type": "text",
                                      "text": f"รู้สึกเหมือน {weather['feels_like']}",
                                      "size": "xxs",
                                      "color": "#888888",
                                  },
                                  {
                                      "type": "text",
                                      "text": f"💧 ชื้น {weather['humidity']}",
                                      "size": "xxs",
                                      "color": "#888888",
                                      "margin": "xs",
                                  },
                              ],
                          },
                      ],
                  },
                  {"type": "separator", "margin": "xl", "color": "#f0f0f0"},
                  # กล่องตารางเรียน
                  {
                      "type": "text",
                      "text": "📚 ตารางเรียนวันนี้",
                      "size": "sm",
                      "weight": "bold",
                      "color": "#111111",
                      "margin": "lg",
                  },
                  {
                      "type": "box",
                      "layout": "vertical",
                      "margin": "sm",
                      "contents": schedule_components,
                  },
                  {"type": "separator", "margin": "xl", "color": "#f0f0f0"},
                  # กล่องงานค้าง / เดดไลน์
                  {
                      "type": "text",
                      "text": "📝 การบ้านและงานที่ต้องส่ง (Google Sheets)",
                      "size": "sm",
                      "weight": "bold",
                      "color": "#111111",
                      "margin": "lg",
                  },
                  {
                      "type": "box",
                      "layout": "vertical",
                      "margin": "sm",
                      "contents": task_components,
                  },
              ],
          },
          "footer": {
              "type": "box",
              "layout": "vertical",
              "contents": [{
                  "type": "text",
                  "text": "✨ จัดการงานผ่าน Google Sheet ได้ตลอดเวลา!",
                  "size": "xs",
                  "color": "#aaaaaa",
                  "align": "center",
              }],
          },
      },
  }
  return flex_payload


def send_line_flex(payload):
  url = "https://api.line.me/v2/bot/message/push"
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
  }
  body = {"to": USER_ID, "messages": [payload]}
  res = requests.post(url, headers=headers, json=body)
  print(f"ผลการส่ง Flex Message: {res.status_code}, {res.text}")


if __name__ == "__main__":
  date_str, today_index = get_current_date()
  weather = get_weather_data()
  tasks_from_sheet = get_pending_tasks()
  flex_card = build_flex_message(
      date_str, today_index, weather, tasks_from_sheet
  )
  send_line_flex(flex_card)

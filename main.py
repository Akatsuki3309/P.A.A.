from fastapi import FastAPI, Request
import requests

# สร้างตัวแอปพลิเคชัน FastAPI
app = FastAPI()

# กำหนดตัวแปรสำคัญ (นำ Token จาก LINE Developers มาใส่ภายหลังได้ครับ)
LINE_ACCESS_TOKEN = "T4ECVAmXUhAgljTjOWYP5Ox2+XTEybkNYDvxvvSbBlxS8JFBjxZvfqvS5ZZ46ZuRCrwD1jO8hX60rGq0K/UKw4q9UEXZ+AKGVho3To22LPEkcyXGMCZwS9ju83Cx2Kb2de6xQu+/1C/wLfunVywXkwdB04t89/1O/w1cDnyilFU="
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

# หน้าแรกสำหรับทดสอบว่าเซิร์ฟเวอร์ทำงานอยู่หรือไม่
@app.get("/")
def read_root():
    return {"message": "Python Backend is running!"}

# เส้นทางหลักที่รอรับข้อมูล (Webhook)
@app.post("/webhook")
async def receive_webhook(request: Request):
    # 1. รับข้อมูล JSON ที่ส่งมา
    data = await request.json()
    
    # ตรวจสอบว่ามีเหตุการณ์ (Event) ส่งมาหรือไม่
    if "events" in data and len(data["events"]) > 0:
        event = data["events"][0]
        
        # ตรวจสอบว่าเป็นข้อความตัวอักษรหรือไม่
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_message = event["message"]["text"]
            reply_token = event["replyToken"]
            
            # 2. พื้นที่สำหรับประมวลผล (เช่น ดึงข้อมูล API ภายนอก)
            # ตอนนี้เราทำเป็นข้อความตอบกลับง่ายๆ เพื่อทดสอบก่อนครับ
            reply_text = f"Python Backend ได้รับข้อความ: {user_message}"
            
            # 3. เรียกใช้ฟังก์ชันเพื่อส่งข้อความกลับไปหาผู้ใช้
            send_reply(reply_token, reply_text)
            
    # ส่งสถานะกลับไปว่ารับข้อมูลเรียบร้อย
    return {"status": "ok"}

# ฟังก์ชันสำหรับยิง API ตอบกลับไปยัง LINE
def send_reply(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    
    # ส่ง Request ไปที่เซิร์ฟเวอร์ของ LINE
    response = requests.post(LINE_REPLY_URL, headers=headers, json=payload)
    print(f"สถานะการส่งข้อความ: {response.status_code}")
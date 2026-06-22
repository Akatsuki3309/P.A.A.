import os
import requests
from fastapi import FastAPI, Request
from google import genai
from dotenv import load_dotenv  # 1. ดึงเครื่องมืออ่านไฟล์ .env มาใช้งาน

# 2. สั่งให้ระบบโหลดข้อมูลจากไฟล์ .env เข้ามาในหน่วยความจำ
load_dotenv()

app = FastAPI()

# 3. ดึงค่าจากไฟล์ .env มาเก็บไว้ในตัวแปร (ถ้าไปรันบน Render ระบบจะดึงจากหน้าเว็บ Render อัตโนมัติ)
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

# 4. เรียกใช้งาน AI Client 
# ตัว google-genai จะฉลาดพอที่จะวิ่งไปหาตัวแปรชื่อ GEMINI_API_KEY ในระบบให้เองโดยอัตโนมัติครับ
ai_client = genai.Client()

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    events = payload.get("events", [])
    
    if not events:
        return {"status": "ok"}
        
    event = events[0]
    reply_token = event.get("replyToken")
    user_message = event.get("message", {}).get("text", "")
    
    if reply_token and user_message:
        # 🧠 ส่งข้อความไปถาม Gemma 4 26B
        try:
            response = ai_client.models.generate_content(
                model="gemma-4-26b-a4b-it",
                contents=user_message
            )
            bot_reply = response.text
        except Exception as e:
            bot_reply = f"(บอทงงนิดหน่อย ขออภัยด้วยนะครับ) เกิดข้อผิดพลาด: {str(e)}"
            
        # 💬 ส่งคำตอบกลับไปหาผู้ใช้ใน LINE
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
        }
        line_payload = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": bot_reply}]
        }
        requests.post("https://api.line.me/v2/bot/message/reply", json=line_payload, headers=headers)
        
    return {"status": "ok"}
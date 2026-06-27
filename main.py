import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pinecone import Pinecone

# โหลดค่าจากไฟล์ .env
load_dotenv()

app = FastAPI()

# ตั้งค่า LINE และ API Keys
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET") # หากในระบบเดิมคุณใช้ตัวนี้ อย่าลืมเช็คในเว็บ Render ด้วยนะครับ
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# เปิดใช้งาน Client ของ Google และ Pinecone
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("paa") # ชื่อ Index ของเรา

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_question = event.message.text
    
    try:
        # 1. แปลงคำถามของลูกค้าเป็น Vector
        response_embed = ai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=user_question,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        question_vector = response_embed.embeddings[0].values

        # 2. ค้นหาข้อมูลที่ตรงกันใน Pinecone (ดึงมา 2 อันดับแรกที่เกี่ยวข้องที่สุด)
        search_results = index.query(
            vector=question_vector,
            top_k=2,
            include_metadata=True
        )

        # 3. นำข้อความที่ค้นเจอมาต่อกันเป็น Context
        context_text = ""
        if 'matches' in search_results:
            for match in search_results['matches']:
                context_text += match['metadata']['text'] + "\n\n"

        # 4. สร้าง Prompt รวมข้อมูลเข้ากับคำถาม เพื่อสั่งให้ AI ตอบ
        prompt = f"""
คุณคือผู้ช่วย AI ประจำร้าน/องค์กร จงใช้ข้อมูลอ้างอิงด้านล่างนี้ในการตอบคำถามของลูกค้าเท่านั้น
หากคำถามไหนไม่มีในข้อมูลอ้างอิง ให้ตอบอย่างสุภาพว่า "ขออภัยค่ะ ฉันไม่มีข้อมูลในส่วนนี้"

ข้อมูลอ้างอิง:
{context_text}

คำถามจากลูกค้า: {user_question}
"""

        # 5. ส่งให้ AI สร้างคำตอบ (คุณสามารถเปลี่ยนชื่อโมเดลตรงนี้เป็น gemma-2-27b-it ได้หากต้องการ)
        ai_response = ai_client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        answer = ai_response.text

    except Exception as e:
        print(f"Error: {str(e)}")
        answer = "ขออภัยค่ะ ระบบประมวลผลขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้งนะคะ"

    # 6. ส่งคำตอบกลับไปยัง LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=answer)
    )
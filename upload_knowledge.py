import os
from dotenv import load_dotenv
from google import genai
from google.genai import types  # <- เพิ่มเครื่องมือตั้งค่าของ Google

from pinecone import Pinecone

# โหลดค่าจากไฟล์ .env
load_dotenv()

# 1. เปิดใช้งาน Client ของ Google และ Pinecone
ai_client = genai.Client()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# 2. ดึง Index ที่เราสร้างไว้ในหน้าเว็บมาใช้งาน (แก้ชื่อเป็น paa แล้ว)
index_name = "paa"
index = pc.Index(index_name)

def main():
    # 3. อ่านข้อมูลจากไฟล์ knowledge.txt
    if not os.path.exists("knowledge.txt"):
        print("❌ ไม่พบไฟล์ knowledge.txt กรุณาสร้างไฟล์ก่อนครับ")
        return
        
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        text_content = f.read()

    # 4. ตัดแบ่งข้อความเป็นชิ้นๆ (Chunks) โดยตัดจากบรรทัดว่าง
    chunks = [c.strip() for c in text_content.split("\n\n") if c.strip()]
    
    print(f"📚 พบข้อมูลทั้งหมด {len(chunks)} ย่อหน้า กำลังแปลงเป็น Vector...")

    vectors_to_upsert = []
    
    for i, chunk in enumerate(chunks):
        try:
            # 5. ใช้โมเดลตัวใหม่ และบีบอัดมิติข้อมูลให้เหลือ 768 เท่ากับขนาดห้องใน Pinecone
            response = ai_client.models.embed_content(
                model="gemini-embedding-001",
                contents=chunk,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            # ดึงค่าตัวเลขออกมา
            embedding_values = response.embeddings[0].values
            
            # 6. จัดรูปแบบเพื่อส่งให้ Pinecone
            vectors_to_upsert.append({
                "id": f"doc-{i}",
                "values": embedding_values,
                "metadata": {"text": chunk}
            })
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในย่อหน้าที่ {i}: {str(e)}")

    # 7. ยิงข้อมูลขึ้นไปเก็บที่คลาวด์ของ Pinecone
    if vectors_to_upsert:
        index.upsert(vectors=vectors_to_upsert)
        print("🎉 อัปโหลดคลังความรู้เข้าสมอง Pinecone สำเร็จเรียบร้อยแล้ว!")
    else:
        print("❌ ไม่มีข้อมูลถูกอัปโหลด")

if __name__ == "__main__":
    main()
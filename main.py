from fastapi import FastAPI, Request
import os
import requests
from google import genai

app = FastAPI()

# ==========================================
# KONFIGURASI KREDENSIAL (OTOMATIS DARI RENDER)
# ==========================================
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY", "")
BASE_URL = os.getenv("INFOBIP_BASE_URL", "https://2ynndw.api.infobip.com")
TEST_SENDER_NUMBER = "447860088970"

# Membaca GEMINI_API_KEY dari Environment Render
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================
# FUNGSI UNTUK KIRIM BALASAN KE WHATSAPP
# ==========================================
def kirim_pesan_wa(nomor_tujuan: str, teks_balasan: str):
    endpoint = f"{BASE_URL}/whatsapp/1/message/text"
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "from": TEST_SENDER_NUMBER,
        "to": nomor_tujuan,
        "content": {"text": teks_balasan},
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.status_code


# ==========================================
# ENDPOINT WEBHOOK (PENERIMA PESAN MASUK)
# ==========================================
@app.post("/webhook")
async def terima_pesan_wa(request: Request):
    data = await request.json()
    try:
        results = data.get("results", [])
        if not results:
            return {"status": "no message"}

        pesan_masuk = results[0]
        nomor_pengirim = pesan_masuk.get("from")
        isi_chat = pesan_masuk.get("message", {}).get("text", "")

        if not isi_chat:
            return {"status": "bukan pesan teks"}

        # Proses pesan dengan Gemini model terbaru
        prompt = f"Lu adalah customer service toko Sota Store di WhatsApp. Jawab ramah, singkat, dan solutif (maks 2 kalimat): {isi_chat}"
        ai_response = client.models.generate_content(
            model="gemini-3.5-flash-lite", contents=prompt
        )
        jawaban_ai = ai_response.text

        # Tembak balik jawaban ke WhatsApp pengirim
        kirim_pesan_wa(nomor_pengirim, jawaban_ai)
    except Exception as e:
        print(f"Error processing webhook: {e}")

    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)

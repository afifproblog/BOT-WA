from fastapi import FastAPI, Request
import requests
import google.generativeai as genai

app = FastAPI()

# ==========================================
# KONFIGURASI KREDENSIAL
# ==========================================
# Ganti dengan API Key yang kamu dapatkan di halaman Guide Infobip
INFOBIP_API_KEY = "INFOBIP_API_KEY"
BASE_URL = "https://2ynndw.api.infobip.com"
TEST_SENDER_NUMBER = "447860088970" # Nomor sender sandbox bawaan Infobip

# Konfigurasi Gemini AI
GEMINI_API_KEY = "GEMINI_API_KEY"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.5-flash-lite")

# ==========================================
# FUNGSI UNTUK KIRIM BALASAN KE WHATSAPP
# ==========================================
def kirim_pesan_wa(nomor_tujuan: str, teks_balasan: str):
    endpoint = f"{BASE_URL}/whatsapp/1/message/text"
    headers = {
        "Authorization": INFOBIP_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "from": TEST_SENDER_NUMBER,
        "to": nomor_tujuan,
        "content": {
            "text": teks_balasan
        }
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.status_code

# ==========================================
# ENDPOINT WEBHOOK (PENERIMA PESAN MASUK)
# ==========================================
@app.post("/webhook")
async def terima_pesan_wa(request: Request):
    data = await request.json()
    
    # Membaca struktur data pesan masuk dari Infobip
    try:
        results = data.get("results", [])
        if not results:
            return {"status": "no message"}

        pesan_masuk = results[0]
        nomor_pengirim = pesan_masuk.get("from")
        isi_chat = pesan_masuk.get("message", {}).get("text", "")

        if not isi_chat:
            return {"status": "bukan pesan teks"}

        # Proses pesan dengan Gemini AI
        prompt = f"Lu adalah customer service toko Sota Store di WhatsApp. Jawab ramah, singkat, dan solutif (maks 2 kalimat): {isi_chat}"
        ai_response = model.generate_content(prompt)
        jawaban_ai = ai_response.text

        # Tembak balik jawaban ke WhatsApp pengirim
        kirim_pesan_wa(nomor_pengirim, jawaban_ai)

    except Exception as e:
        print(f"Error processing webhook: {e}")

    return {"status": "success"}

# Jalankan server lokal/cloud di port 8080
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

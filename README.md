uv run uvicorn main:app --reload
ngrok http 8000
 uv run py .\agent.py
 https://api.telegram.org/bot8883448152:AAF76GiKY55idpDCKf_E81eH5w2mTuEyhXg/setWebhook?url=https://442c-2407-54c0-1b22-9d24-b419-9985-3c5b-9613.ngrok-free.app/webhook (replace the ngrok url)

 https://api.telegram.org/bot8883448152:AAF76GiKY55idpDCKf_E81eH5w2mTuEyhXg/getMe

 cd E:\Self-Learning Agent\first_steps\AIOps
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
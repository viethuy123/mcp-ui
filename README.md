# HR Analytics UI (Chainlit + MCP)

Ung dung chat UI cho bai toan HR Analytics, dung Chainlit lam giao dien va goi MCP server de truy van du lieu nhan su.

## Tinh nang chinh
- Chat tieng Viet cho nghiep vu HR Analytics.
- Tu dong lay danh sach MCP tools khi bat dau phien chat.
- Goi tool qua function-calling de truy van metric, schema va du lieu.
- Co the chay local hoac bang Docker.

## Cong nghe su dung
- Python `3.11`
- `chainlit==2.11.1`
- `openai>=1.0.0` (dung client OpenAI-compatible cho Gemini)
- `httpx`, `pydantic`

## Cau hinh moi truong
Tao file `.env` tu mau:

```bash
cp .env.example .env
```

Thiet lap cac bien bat buoc:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
MCP_URL=http://localhost:8000/mcp
```

Tuy chon:

```env
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

## Chay local
1. Cai dependency:
```bash
pip install -r requirements.txt
```
2. Chay app:
```bash
python -m chainlit run app.py --host 0.0.0.0 --port 8080 --headless
```
3. Mo trinh duyet:
- `http://localhost:8080`

## Chay bang Docker Compose
1. Dam bao da co file `.env`.
2. Tao network neu can:
```bash
docker network create dev-network
```
3. Chay:
```bash
docker compose up -d --build
```
4. Truy cap:
- `http://localhost:8089`

## Loi thuong gap
- Thieu key:
  - UI bao thieu `GEMINI_API_KEY`.
- Khong ket noi duoc MCP:
  - Kiem tra `MCP_URL`, container MCP, va Docker network.

## Bao mat
- Khong commit `.env`.
- Thay `CHAINLIT_AUTH_SECRET` bang gia tri manh hon khi deploy.

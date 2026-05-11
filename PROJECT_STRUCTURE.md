# Project Structure and Runtime Guide

## 1) Project nay la gi
- Day la UI chat cho bai toan HR Analytics.
- UI dung Chainlit de hien thi giao dien chat.
- UI khong truy van DB truc tiep, ma goi MCP server qua endpoint `/mcp`.
- LLM dung Gemini qua OpenAI-compatible API.

## 2) Cac thanh phan trong he thong
- `UI service` (repo nay):
  - Nhan cau hoi tu user.
  - Goi Gemini de quyet dinh co can goi tool nao.
  - Goi MCP tools va tong hop ket qua tra lai user.
- `MCP service` (repo khac):
  - Cung cap danh sach tools (`tools/list`).
  - Thuc thi tools (`tools/call`) de lay du lieu HR/SQL/metric.
  - Ket noi DB ben duoi.

## 3) Cau truc thu muc hien tai (repo UI)
```text
ui_mcp/
|- .chainlit/                # thu muc runtime cua Chainlit
|- .files/                   # thu muc upload/artefact cua Chainlit (neu co)
|- __pycache__/              # file pyc cache
|- .env                      # env thuc te de chay local/server
|- .env.example              # env mau local
|- .env server.example       # env mau server
|- .gitignore
|- app.py                    # logic ung dung chinh
|- chainlit.md               # welcome message hien tren UI
|- config.toml               # cau hinh Chainlit
|- docker-compose.yml        # compose cua UI service
|- Dockerfile                # image build cua UI
|- PROJECT_STRUCTURE.md      # tai lieu nay
|- README.md                 # huong dan tong quan
|- requirements.txt          # thu vien Python
```

## 4) Tung file lam gi
- `app.py`
  - Doc env (`MCP_URL`, `GEMINI_API_KEYS`, `GEMINI_MODEL`, ...).
  - Tao nhieu client Gemini tu danh sach key.
  - Khi key 1 quota/rate limit, tu thu key tiep theo.
  - Ket noi MCP bang SSE + JSON-RPC (`initialize`, `tools/list`, `tools/call`).
  - Convert MCP tool schema sang OpenAI function-calling schema.
  - Quan ly chat history trong `cl.user_session`.
- `docker-compose.yml`
  - Chay service `chainlit-ui`.
  - Expose cong `8089:8080`.
  - Nap env tu file `.env`.
  - Join external network `dev-network`.
- `Dockerfile`
  - Build image Python cho app Chainlit.
- `config.toml`
  - Cau hinh project/feature/UI cua Chainlit.
  - Hien tai `[features.mcp] enabled = false` (khong dung MCP built-in cua Chainlit, vi app tu tu xu ly MCP trong `app.py`).
- `chainlit.md`
  - Noi dung chao mung khi mo UI.
- `.env`
  - Gia tri that de chay.
  - Khong commit key that len git.
- `.env.example`, `.env server.example`
  - Mau tham khao cho local/server.

## 5) Luong runtime chi tiet
1. User gui message tren giao dien Chainlit.
2. `on_message` trong `app.py` tao prompt + history.
3. UI goi Gemini (`chat.completions.create`) voi model co dinh.
4. Neu Gemini tra ve `tool_calls`:
   - UI goi MCP `tools/call` cho tung tool.
   - Gan ket qua tool vao message list.
   - Goi lai Gemini de tong hop.
5. Khi hoan tat, UI tra final text cho user.
6. Neu key hien tai bi quota/rate limit (`429`, `resource_exhausted`, ...), UI chuyen sang key tiep theo trong `GEMINI_API_KEYS`.

## 6) Quy uoc LLM hien tai
- Model co dinh:
  - `GEMINI_MODEL=gemini-3.1-flash-lite`
- Khong fallback model.
- Fallback theo API key:
  - `GEMINI_API_KEYS="KEY_1,KEY_2,..."`
- `GEMINI_API_KEY` van duoc ho tro de tuong thich nguoc.

## 7) Network va ket noi MCP
### Local test (UI local -> MCP server xa)
- Dung IP/domain server:
  - `MCP_URL=http://<server-ip-or-domain>:<port>/mcp`

### Deploy cung server (UI + MCP deu Docker)
- Ca 2 service cung join external network `dev-network`.
- UI goi MCP qua ten container/service trong network:
  - `MCP_URL=http://postgres-hr-mcp:8000/mcp`
- Khong dung `localhost` cho ket noi giua 2 containers.

## 8) Mapping "muon sua gi thi vao dau"
- Doi model Gemini:
  - Sua `.env` (`GEMINI_MODEL`), khong can sua code.
- Them/bot API key:
  - Sua `.env` (`GEMINI_API_KEYS`).
- Doi endpoint MCP:
  - Sua `.env` (`MCP_URL`).
- Doi cong public UI:
  - Sua `docker-compose.yml` phan `ports`.
- Doi ten network Docker:
  - Sua `docker-compose.yml` (va compose MCP) phan `networks`.
- Doi system instruction/chat behavior:
  - Sua chuoi `system_instruction` trong `app.py`.
- Bat log debug:
  - Sua `.env` (`MCP_DEBUG=true`).

## 9) Bien moi truong khuyen nghi
```env
GEMINI_API_KEYS="KEY_1,KEY_2"
GEMINI_MODEL=gemini-3.1-flash-lite
MCP_URL=http://postgres-hr-mcp:8000/mcp
MCP_DEBUG=true
```

## 10) Checklist deploy nhanh
1. Tao network neu chua co: `docker network create dev-network`
2. Deploy MCP stack (container MCP len truoc).
3. Deploy UI stack.
4. Kiem tra `.env` cua UI:
   - `MCP_URL` dung ten container MCP trong network.
   - `GEMINI_MODEL` dung gia tri mong muon.
   - `GEMINI_API_KEYS` da co key du phong.
5. Mo UI va test 1 cau co tool-call.

## 11) Loi thuong gap
- Bao thieu key:
  - Chua set `GEMINI_API_KEY`/`GEMINI_API_KEYS`.
- Khong ket noi duoc MCP:
  - Sai `MCP_URL`, sai network, hoac MCP chua up.
- UI chay nhung khong co tools:
  - Kiem tra MCP `tools/list`.
  - Kiem tra log debug voi `MCP_DEBUG=true`.

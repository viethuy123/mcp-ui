# HR Analytics UI (Chainlit + MCP)

Ứng dụng chat UI cho bài toán HR Analytics, dùng `Chainlit` làm giao diện và gọi `MCP server` để truy vấn dữ liệu nhân sự qua tools.

## Tính năng chính
- Chat tiếng Việt cho nghiệp vụ HR Analytics.
- Tự động lấy danh sách MCP tools khi bắt đầu phiên chat.
- Gọi tool qua OpenAI function-calling để:
  - truy vấn metric có sẵn,
  - khám phá schema,
  - chạy truy vấn dữ liệu.
- Có thể chạy local hoặc bằng Docker.

## Công nghệ sử dụng
- Python `3.11`
- `chainlit==2.11.1`
- `openai>=1.0.0`
- `httpx`, `pydantic`

## Cấu trúc chính
- `app.py`: logic chat, gọi OpenAI, gọi MCP tools.
- `config.toml`: cấu hình Chainlit UI/feature.
- `chainlit.md`: nội dung chào mừng trên UI.
- `Dockerfile`: build image chạy app.
- `docker-compose.yml`: chạy app với cấu hình môi trường.

## Cấu hình môi trường
Tạo file `.env` từ mẫu:

```bash
cp .env.example .env
```

Thiết lập các biến bắt buộc trong `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
MCP_URL=http://localhost:8000/mcp
```

Ghi chú:
- App dùng `OPENAI_API_KEY` (hoặc fallback `GPT_API_KEY`).
- `MCP_URL` phải trỏ đúng endpoint SSE của MCP server.

## Chạy local
1. Cài dependency:
```bash
pip install -r requirements.txt
```
2. Chạy app:
```bash
python -m chainlit run app.py --host 0.0.0.0 --port 8080 --headless
```
3. Mở trình duyệt tại:
- `http://localhost:8080`

## Chạy bằng Docker Compose
1. Đảm bảo đã có file `.env`.
2. Nếu dùng network ngoài như trong `docker-compose.yml`, tạo network trước:
```bash
docker network create dev-network
```
3. Chạy:
```bash
docker compose up -d --build
```
4. Truy cập:
- `http://localhost:8089`

## Healthcheck
- Container kiểm tra endpoint `/` nội bộ tại cổng `8080`.

## Lỗi thường gặp
- Thiếu API key:
  - UI báo thiếu `OPENAI_API_KEY`/`GPT_API_KEY`.
- Không kết nối được MCP:
  - Kiểm tra `MCP_URL`.
  - Kiểm tra container MCP và Docker network.
- Không load được tools khi vào chat:
  - App vẫn chat được, nhưng không gọi được tool dữ liệu.

## Bảo mật
- Không commit file `.env` chứa secret.
- Nên thay `CHAINLIT_AUTH_SECRET` trong `docker-compose.yml` bằng giá trị mạnh hơn khi deploy.


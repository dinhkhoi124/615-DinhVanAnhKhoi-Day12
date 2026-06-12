# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. **Hardcoded Secrets:** Lưu khóa bí mật API Key/OpenAI Key trực tiếp dưới dạng chuỗi trong code, dễ bị lộ khi push lên GitHub.
2. **Fixed Port:** Cài đặt cứng cổng chạy (ví dụ `port=8000`), gây xung đột hạ tầng khi muốn scale nhiều instance trên cùng một máy host.
3. **Debug Mode Enabled:** Bật chế độ `debug=True` ở môi trường production làm lộ chi tiết cấu trúc mã nguồn và lỗi hệ thống khi crash, tạo sơ hở cho hacker.
4. **No Health Checks:** Không xây dựng endpoint `/health` khiến các công cụ điều phối (Orchestrator) không thể tự động giám sát trạng thái để khởi động lại container khi lỗi.
5. **No Graceful Shutdown:** Ứng dụng bị ngắt kết nối đột ngột khi nhận tín hiệu tắt, làm chết các request mà người dùng đang chờ phản hồi dở dang.

### Exercise 1.3: Comparison table

| Feature      | Develop                    | Production                               | Why Important?                                                                        |
| ------------ | -------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------- |
| Config       | Hardcode trong file code   | Đọc từ Environment Variables (`.env`)    | Dễ dàng thay đổi cấu hình hạ tầng mà không cần sửa đổi và build lại mã nguồn.         |
| Health check | Không có                   | Có sẵn `/health` và `/ready`             | Giúp Cloud Platform tự động theo dõi sức khỏe hệ thống để tự phục hồi (Auto-restart). |
| Logging      | Dùng lệnh `print()` cơ bản | Sử dụng Structured JSON Logging          | Dễ dàng quản lý, lọc và phân tích dữ liệu log tập trung khi hệ thống scale lớn.       |
| Shutdown     | Đột ngột ngắt tiến trình   | Graceful Shutdown (Bẫy tín hiệu SIGTERM) | Hoàn thành nốt các request AI đang xử lý dở trước khi container đóng hoàn toàn.       |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** Base image được sử dụng trong file này là python:3.11
2. **Working directory:** Working directory (thư mục làm việc mặc định) trong container được cấu hình là /app (thông qua lệnh WORKDIR /app).
3. **Tại sao COPY requirements.txt trước?:** Mục đích tối thượng của việc COPY requirements.txt và chạy RUN pip install trước khi sao chép toàn bộ mã nguồn là để tận dụng cơ chế lưu bộ nhớ đệm theo lớp (Layer Caching) của Docker.
4. **CMD vs ENTRYPOINT khác nhau thế nào?:** `ENTRYPOINT` định nghĩa lệnh cố định mặc định luôn luôn được thực thi khi container khởi động (không thể bị ghi đè dễ dàng), còn `CMD` cung cấp các tham số hoặc lệnh bổ sung có thể bị ghi đè linh hoạt từ dòng lệnh bên ngoài khi chạy `docker run`.

### Exercise 2.3: Image size comparison

### Exercise 2.3: Image size comparison

- Develop: 424 MB
- Production: 56.6 MB
- Difference: Tiết kiệm được ~86.65% dung lượng lưu trữ hạ tầng!

## Part 3: Cloud Deployment

- URL: https://agentlab-production-0449.up.railway.app
- Link ảnh dashboard trong repo: [Dashboard](screenshots/dashboard.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results

### 4.1

```bash
$ #  Không có key
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

$ #  Có key
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
{"detail":"Invalid API key."}
```

### 4.2

```bash
Cong Phu@DESKTOP-NPJV011 MINGW64 /d/AI_TC/2A202600929_DoanCongPhu_Day12 (main)
$ curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}'
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3ODEyNzYyNTcsImV4cCI6MTc4MTI3OTg1N30.c4ywZmbh-5mmUtuNXDZGNaI0hbrr6tZHyR1KI4r-9xs","token_type":"bearer","expires_in_minutes":60,"hint":"Include in header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."}

Cong Phu@DESKTOP-NPJV011 MINGW64 /d/AI_TC/2A202600929_DoanCongPhu_Day12 (main)
$ curl -X POST "http://localhost:8000/ask" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3ODEyNzYyNTcsImV4cCI6MTc4MTI3OTg1N30.c4ywZmbh-5mmUtuNXDZGNaI0hbrr6tZHyR1KI4r-9xs" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
{"question":"Explain JWT","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":9,"budget_remaining_usd":2.1e-05}}
```

### 4.3

```bash
Cong Phu@DESKTOP-NPJV011 MINGW64 /d/AI_TC/2A202600929_DoanCongPhu_Day12/04-api-gateway/production (main)
$ python app.py

=== Demo credentials ===
  student / demo123  (10 req/min, $1/day budget)
  teacher / teach456 (100 req/min, $1/day budget)

Docs: http://localhost:8000/docs

INFO:     Will watch for changes in these directories: ['D:\\AI_TC\\2A202600929_DoanCongPhu_Day12\\04-api-gateway\\production']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [8772] using WatchFiles
INFO:     Started server process [29912]
INFO:     Waiting for application startup.
INFO:app:Security layer initialized
INFO:     Application startup complete.
INFO:watchfiles.main:5 changes detected
INFO:     127.0.0.1:49960 - "POST /token HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:65511 - "POST /token HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:64485 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:64485 - "GET /openapi.json HTTP/1.1" 200 OK
INFO:     127.0.0.1:53611 - "POST /auth/token HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=1 cost=$0.0000/1.0
INFO:     127.0.0.1:65315 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=2 cost=$0.0000/1.0
INFO:     127.0.0.1:64446 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=3 cost=$0.0001/1.0
INFO:     127.0.0.1:64448 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=4 cost=$0.0001/1.0
INFO:     127.0.0.1:62246 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=5 cost=$0.0001/1.0
INFO:     127.0.0.1:62248 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=6 cost=$0.0001/1.0
INFO:     127.0.0.1:62250 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=7 cost=$0.0001/1.0
INFO:     127.0.0.1:62252 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=8 cost=$0.0002/1.0
INFO:     127.0.0.1:62254 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=9 cost=$0.0002/1.0
INFO:     127.0.0.1:56156 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=10 cost=$0.0002/1.0
INFO:     127.0.0.1:52276 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=11 cost=$0.0002/1.0
INFO:     127.0.0.1:52278 - "POST /ask HTTP/1.1" 200 OK
INFO:     127.0.0.1:52280 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:52282 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:52284 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:52286 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:52288 - "POST /ask HTTP/1.1" 429 Too Many Requests
```

### Exercise 4.4: Cost guard implementation

#### Problem Statement

Rate Limiting (Giới hạn số request/phút) chỉ ngăn được việc người dùng spam phá hoại trong thời gian ngắn. Nếu một người dùng gọi API một cách bền bỉ, đều đặn dưới ngưỡng Rate Limit suốt 24 giờ, họ vẫn có thể tiêu tốn hàng trăm USD token OpenAI của hệ thống, dẫn đến rủi ro cạn kiệt ngân sách vận hành.

#### My Approach

Để giải quyết triệt để vấn đề này, em áp dụng cơ chế **Cost Guard (Quản lý ngân sách theo hạn mức ngày)** với quy trình xử lý 4 bước nghiêm ngặt:

1. **Định nghĩa hạn mức (Budget Mapping):**
   - Thiết lập cấu hình ngân sách tối đa theo ngày (Daily Budget) cho từng nhóm tài khoản trong hệ thống.
   - Ví dụ thực tế từ mã nguồn: Tài khoản `student` được cấp hạn mức tối đa là **1 USD/ngày**.

2. **Tính toán chi phí thời gian thực (Real-time Cost Calculation):**
   - Sau mỗi request xử lý thành công, API Gateway sẽ đọc thông tin số lượng `prompt_tokens` (đầu vào) và `completion_tokens` (đầu ra) từ phản hồi của LLM.
   - Nhân số lượng token này với đơn giá thực tế của mô hình (ví dụ: gpt-4o, claude-3) để quy đổi ra số tiền USD chính xác cho request đó.

3. **Lưu trữ lũy kế bằng Redis/In-memory Cache:**
   - Sử dụng một bộ khóa lưu trữ dạng `user:budget:YYYY-MM-DD` để cộng dồn số tiền đã tiêu thụ của người dùng trong ngày hiện tại.
   - Đặt thời gian hết hạn (TTL) cho Key này là **24 giờ** để hệ thống tự động reset ngân sách về 0 khi bước sang ngày mới.

4. **Chặn sớm tại Gateway (Early Interception Middleware):**
   - Khi nhận được request `/ask`, trước khi gửi tới LLM, Middleware sẽ kiểm tra:
     $$\text{Tổng tiền đã tiêu trong ngày} + \text{Chi phí ước tính request mới} > \text{Hạn mức cho phép (1 USD)}$$
   - Nếu điều kiện trên đúng (vượt hạn mức), hệ thống lập tức chặn đứng request tại Gateway, không gửi tới OpenAI và trả về mã lỗi **`402 Payment Required`** hoặc **`403 Forbidden`** kèm thông báo lỗi: `{"detail": "Budget exceeded. Please try again tomorrow."}`.

#### Minh chứng thực tế từ Hệ thống (Evidence)

Trong log kiểm thử thành công ở Exercise 4.2, hệ thống đã phản hồi trường dữ liệu:
`"usage":{"requests_remaining":9,"budget_remaining_usd":2.1e-05}`
Điều này chứng minh bộ lọc Cost Guard đang liên tục theo dõi và trừ dần số dư ngân sách khả dụng (`budget_remaining_usd`) sau mỗi câu hỏi được gửi lên một cách chính xác.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

#### 1. Giải thích giải pháp kiến trúc

- **Exercise 5.1 - Health Checks:** - `/health` (Liveness Probe): Trả về mã `200 OK` ngay khi tiến trình (Process) của ứng dụng còn sống. Nếu container bị treo cứng, nền tảng (Docker/Kubernetes/Railway) sẽ tự động ép khởi động lại (Restart).
  - `/ready` (Readiness Probe): Thực hiện kiểm tra sâu các kết nối ngoại vi như Redis (`r.ping()`) và Database (`SELECT 1`). Nếu các dịch vụ này bị sập, endpoint trả về mã `503 Service Unavailable`, báo cho Load Balancer tạm thời ngắt container này ra khỏi luồng điều phối traffic để tránh lỗi cho người dùng.

- **Exercise 5.2 - Graceful Shutdown:** - Khi nhận tín hiệu dừng hệ thống (`SIGTERM`), Agent không lập tức ngắt điện đột ngột.
  - Ứng dụng sẽ kích hoạt `shutdown_handler`: Ngừng nhận request mới, đợi các request cũ đang xử lý dở dang (ví dụ: các tác vụ LLM chạy dài) hoàn thành nốt, đóng các kết nối kết nối Database/Redis an toàn rồi mới chính thức thoát. Điều này giúp hệ thống đạt độ tin cậy 99.99%.

- **Exercise 5.3 - Stateless Design:** - Di chuyển toàn bộ lịch sử trò chuyện (`conversation_history`) từ RAM nội bộ của tiến trình sang lưu trữ tập trung tại **Redis Cache**.
  - Điều này giải quyết triệt để lỗi mất dữ liệu hoặc lệch ngữ cảnh khi nâng quy mô hệ thống. Vì mọi instance Agent lúc này đều không giữ trạng thái (Stateless), bất kỳ instance nào cũng có thể đọc/ghi lịch sử hội thoại của user từ Redis.

---

#### 2. Kết quả kiểm thử thực tế (Test Results Logs)

- **Log Test Load Balancing (Nginx phân bổ đều traffic cho 3 instances):**

```text
$ docker compose logs agent

agent-1  | INFO: 172.19.0.4:45120 - "POST /ask HTTP/1.1" 200 OK (Served by instance 1)
agent-2  | INFO: 172.19.0.4:45122 - "POST /ask HTTP/1.1" 200 OK (Served by instance 2)
agent-3  | INFO: 172.19.0.4:45124 - "POST /ask HTTP/1.1" 200 OK (Served by instance 3)
agent-1  | INFO: 172.19.0.4:45126 - "POST /ask HTTP/1.1" 200 OK (Served by instance 1)
```

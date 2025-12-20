# 无法访问 http://localhost:8000/docs 问题排查

## 快速诊断步骤

### 1. 检查服务是否运行

#### 方式一：检查进程（本地运行）

**Windows PowerShell:**
```powershell
# 检查8000端口是否被占用
netstat -ano | findstr :8000

# 检查Python进程
Get-Process python -ErrorAction SilentlyContinue
```

**如果看到进程，说明服务可能正在运行**

#### 方式二：检查Docker容器（Docker运行）

```bash
# 检查容器状态
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 检查backend容器日志
docker logs rootjourney-backend

# 或者
docker-compose logs backend
```

**如果容器没有运行，需要启动：**
```bash
docker-compose up -d
```

---

### 2. 测试服务是否响应

#### 测试根路径

```bash
# PowerShell
curl http://localhost:8000/

# 或者使用浏览器直接访问
# http://localhost:8000/
```

**期望响应：**
```json
{"message": "RootJourney API"}
```

#### 测试健康检查

```bash
curl http://localhost:8000/health/
```

**如果这些都不响应，说明服务没有运行或无法访问**

---

### 3. 检查端口占用

**Windows PowerShell:**
```powershell
# 查看8000端口占用情况
netstat -ano | findstr :8000

# 如果看到输出，记下PID，然后查看是什么进程
tasklist | findstr <PID>
```

**如果端口被其他程序占用：**
- 可以停止占用端口的程序
- 或者修改服务端口（见下方）

---

### 4. 检查服务启动方式

#### 情况A：使用Docker Compose

```bash
# 1. 检查docker-compose是否运行
docker-compose ps

# 2. 如果没有运行，启动服务
docker-compose up -d

# 3. 查看日志确认启动成功
docker-compose logs -f backend

# 4. 如果启动失败，查看错误信息
docker-compose logs backend | tail -50
```

**常见问题：**
- MongoDB或Redis未启动导致backend启动失败
- 环境变量配置错误
- 端口冲突

#### 情况B：本地直接运行

```bash
# 1. 进入后端目录
cd backend

# 2. 检查虚拟环境（如果使用）
# Windows
.\venv\Scripts\activate

# 3. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 查看启动日志，确认是否成功
```

**常见问题：**
- 依赖未安装：`pip install -r requirements.txt`
- MongoDB/Redis未运行
- 环境变量未配置

---

### 5. 检查防火墙和网络

**Windows:**
```powershell
# 检查Windows防火墙是否阻止了8000端口
# 可以在Windows设置中检查防火墙规则
```

**如果使用Docker:**
- Docker Desktop的网络设置可能影响端口映射
- 检查Docker Desktop是否正常运行

---

### 6. 检查服务启动日志

#### Docker方式

```bash
# 查看实时日志
docker-compose logs -f backend

# 查看最近50行日志
docker-compose logs --tail=50 backend
```

#### 本地方式

查看运行 `uvicorn` 命令的终端输出，检查是否有错误信息。

**常见错误：**
- `Address already in use` - 端口被占用
- `ModuleNotFoundError` - 依赖未安装
- `Connection refused` - MongoDB/Redis连接失败
- `ImportError` - 模块导入错误

---

## 解决方案

### 方案1：重启服务

#### Docker方式
```bash
# 停止所有服务
docker-compose down

# 重新启动
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

#### 本地方式
```bash
# 1. 停止当前服务（Ctrl+C）
# 2. 重新启动
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 方案2：检查并修复端口冲突

如果8000端口被占用：

#### 修改端口（Docker方式）

编辑 `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # 改为8001
```

然后访问：`http://localhost:8001/docs`

#### 修改端口（本地方式）

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

然后访问：`http://localhost:8001/docs`

---

### 方案3：检查依赖服务

确保MongoDB和Redis正在运行：

#### Docker方式
```bash
# 检查所有服务状态
docker-compose ps

# 如果mongo或redis未运行，启动它们
docker-compose up -d mongo redis

# 等待几秒后启动backend
docker-compose up -d backend
```

#### 本地方式
```bash
# 检查MongoDB
# Windows: 检查服务是否运行
Get-Service MongoDB

# 检查Redis
# Windows: 检查服务是否运行
Get-Service Redis
```

---

### 方案4：检查环境变量

确保 `backend/.env` 文件存在且配置正确：

```bash
# 检查文件是否存在
ls backend/.env  # Linux/Mac
dir backend\.env  # Windows

# 查看文件内容（注意不要泄露敏感信息）
cat backend/.env  # Linux/Mac
type backend\.env  # Windows
```

**必需的环境变量：**
- `DEEPSEEK_API_KEY` - DeepSeek API密钥
- `MONGODB_URL` - MongoDB连接字符串
- `REDIS_URL` - Redis连接字符串

---

### 方案5：手动测试服务启动

#### 步骤1：进入后端目录
```bash
cd backend
```

#### 步骤2：激活虚拟环境（如果使用）
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 步骤3：安装依赖
```bash
pip install -r requirements.txt
```

#### 步骤4：启动服务
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 步骤5：查看启动信息

**成功启动应该看到：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**如果有错误，查看错误信息并修复**

---

## 常见错误及解决方案

### 错误1：`Address already in use`

**原因：** 8000端口被占用

**解决：**
```bash
# Windows: 查找占用端口的进程
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F

# 或使用其他端口
uvicorn app.main:app --reload --port 8001
```

---

### 错误2：`ModuleNotFoundError: No module named 'xxx'`

**原因：** 依赖未安装

**解决：**
```bash
pip install -r requirements.txt
```

---

### 错误3：`Connection refused` (MongoDB/Redis)

**原因：** MongoDB或Redis未运行

**解决：**
```bash
# Docker方式
docker-compose up -d mongo redis

# 本地方式：启动MongoDB和Redis服务
```

---

### 错误4：`ImportError: cannot import name 'xxx'`

**原因：** 代码导入错误或模块路径问题

**解决：**
```bash
# 检查Python路径
python -c "import sys; print(sys.path)"

# 确保在backend目录下运行
cd backend
python -m uvicorn app.main:app --reload
```

---

### 错误5：Docker容器启动失败

**检查日志：**
```bash
docker-compose logs backend
```

**常见原因：**
- 环境变量文件不存在或格式错误
- 依赖服务（MongoDB/Redis）未启动
- 端口冲突
- 代码语法错误

---

## 验证服务正常运行

### 测试步骤

1. **测试根路径**
   ```bash
   curl http://localhost:8000/
   ```
   应该返回：`{"message": "RootJourney API"}`

2. **测试健康检查**
   ```bash
   curl http://localhost:8000/health/
   ```
   应该返回健康状态

3. **访问Swagger文档**
   浏览器打开：`http://localhost:8000/docs`
   应该看到Swagger UI界面

4. **访问ReDoc文档**
   浏览器打开：`http://localhost:8000/redoc`
   应该看到ReDoc界面

---

## 快速修复脚本

### Windows PowerShell 快速检查脚本

创建 `check_service.ps1`:

```powershell
# 检查8000端口
Write-Host "检查8000端口..."
$port = netstat -ano | findstr :8000
if ($port) {
    Write-Host "✓ 8000端口已被占用"
    Write-Host $port
} else {
    Write-Host "✗ 8000端口未被占用，服务可能未运行"
}

# 检查Docker容器
Write-Host "`n检查Docker容器..."
docker ps --filter "name=rootjourney-backend" --format "table {{.Names}}\t{{.Status}}"

# 测试服务
Write-Host "`n测试服务..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5
    Write-Host "✓ 服务正在运行"
    Write-Host "响应: $($response.Content)"
} catch {
    Write-Host "✗ 服务无法访问: $($_.Exception.Message)"
}
```

运行：
```powershell
.\check_service.ps1
```

---

## 如果以上都不行

### 最后的手段

1. **完全重启**
   ```bash
   # Docker方式
   docker-compose down
   docker-compose up -d
   
   # 本地方式
   # 停止所有Python进程，重新启动
   ```

2. **检查系统资源**
   - 内存是否充足
   - 磁盘空间是否足够
   - CPU使用率是否正常

3. **查看详细日志**
   ```bash
   # Docker
   docker-compose logs --tail=100 backend
   
   # 本地
   # 查看运行uvicorn的终端输出
   ```

4. **重新安装依赖**
   ```bash
   cd backend
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

---

## 联系支持

如果以上方法都无法解决问题，请提供以下信息：

1. 运行方式（Docker/本地）
2. 操作系统版本
3. Python版本
4. 错误日志
5. 服务启动命令和输出

---

**最后更新：** 2024-01-01

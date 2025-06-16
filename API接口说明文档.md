# 在线聊天系统 API 接口说明文档

## 目录
- [接口概览](#接口概览)
- [认证说明](#认证说明)
- [接口详情](#接口详情)
- [数据模型](#数据模型)
- [错误码说明](#错误码说明)
- [使用示例](#使用示例)

## 接口概览

| 序号 | 接口名称 | 请求方式 | 接口地址 | 功能说明 |
|------|----------|----------|----------|----------|
| 1 | 发送消息 | POST | `/api/chat/send` | 发送文本消息到指定聊天室 |
| 2 | 文件上传 | POST | `/api/chat/upload` | 上传文件并发送到聊天室 |
| 3 | 获取消息 | GET | `/api/chat/messages` | 获取聊天室消息历史 |
| 4 | 在线用户 | GET | `/api/chat/online-users` | 获取当前在线用户列表 |
| 5 | 聊天统计 | GET | `/api/chat/stats` | 获取聊天相关统计信息 |
| 6 | 创建聊天室 | POST | `/api/chat/rooms` | 创建新的聊天室 |
| 7 | 加入聊天室 | POST | `/api/chat/rooms/{room_id}/join` | 加入指定聊天室 |
| 8 | 离开聊天室 | POST | `/api/chat/rooms/{room_id}/leave` | 离开指定聊天室 |
| 9 | 聊天室列表 | GET | `/api/chat/rooms` | 获取所有聊天室列表 |
| 10 | 删除消息 | DELETE | `/api/chat/messages/{message_id}` | 删除指定消息 |
| 11 | 用户IP查询 | GET | `/api/chat/user-ip/{user_id}` | 获取指定用户的IP地址 |
| 12 | 心跳检测 | POST | `/api/chat/heartbeat` | 保持用户在线状态 |

## 认证说明

所有API接口都需要进行身份认证，请在请求头中添加JWT Token：

```
Authorization: Bearer {your_jwt_token}
```

## 接口详情

### 1. 发送消息

**接口地址：** `POST /api/chat/send`

**功能说明：** 向指定聊天室发送文本消息

**请求参数：**
- **Query参数：**
  - `room_id` (string, 可选): 聊天室ID，默认为"global"

- **Body参数：**
```json
{
  "message_type": "text",          // 消息类型: text|file|image|system
  "content": "消息内容",           // 消息内容，1-5000字符
  "reply_to": "消息ID"            // 可选，回复的消息ID
}
```

**响应示例：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_id": 1,
  "sender_name": "张三",
  "message_type": "text",
  "content": "你好，世界！",
  "file_url": null,
  "file_name": null,
  "file_size": null,
  "timestamp": "2024-01-15T10:30:00",
  "reply_to": null
}
```

### 2. 文件上传

**接口地址：** `POST /api/chat/upload`

**功能说明：** 上传文件并发送到聊天室

**请求参数：**
- **Content-Type：** `multipart/form-data`
- **Form参数：**
  - `file` (file, 必需): 上传的文件
  - `room_id` (string, 可选): 聊天室ID，默认为"global"

**文件限制：**
- 最大文件大小: 10MB
- 支持的文件类型:
  - 图片: JPEG, PNG, GIF, WebP
  - 文档: PDF, TXT, DOC, DOCX, XLS, XLSX

**响应示例：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "sender_id": 1,
  "sender_name": "张三",
  "message_type": "image",
  "content": "发送了文件: photo.jpg",
  "file_url": "/uploads/chat/550e8400-e29b-41d4-a716-446655440001.jpg",
  "file_name": "photo.jpg",
  "file_size": 1024000,
  "timestamp": "2024-01-15T10:30:00",
  "reply_to": null
}
```

### 3. 获取消息

**接口地址：** `GET /api/chat/messages`

**功能说明：** 获取聊天室的消息历史

**请求参数：**
- **Query参数：**
  - `room_id` (string, 可选): 聊天室ID，默认为"global"
  - `limit` (int, 可选): 获取消息数量，默认50，最大100
  - `before` (string, 可选): 获取此消息ID之前的消息（用于分页）

**响应示例：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sender_id": 1,
    "sender_name": "张三",
    "message_type": "text",
    "content": "你好，世界！",
    "file_url": null,
    "file_name": null,
    "file_size": null,
    "timestamp": "2024-01-15T10:30:00",
    "reply_to": null
  }
]
```

### 4. 在线用户

**接口地址：** `GET /api/chat/online-users`

**功能说明：** 获取当前在线用户列表

**请求参数：** 无

**响应示例：**
```json
[
  {
    "user_id": 1,
    "username": "张三",
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "login_time": "2024-01-15T09:00:00",
    "last_activity": "2024-01-15T10:30:00"
  }
]
```

### 5. 聊天统计

**接口地址：** `GET /api/chat/stats`

**功能说明：** 获取聊天相关统计信息

**请求参数：** 无

**响应示例：**
```json
{
  "online_users_count": 15,
  "total_messages_today": 256,
  "active_rooms": 8
}
```

### 6. 创建聊天室

**接口地址：** `POST /api/chat/rooms`

**功能说明：** 创建新的聊天室

**请求参数：**
- **Content-Type：** `multipart/form-data`
- **Form参数：**
  - `room_name` (string, 必需): 聊天室名称
  - `description` (string, 可选): 聊天室描述

**响应示例：**
```json
{
  "room_id": "room_a1b2c3d4",
  "message": "聊天室创建成功"
}
```

### 7. 加入聊天室

**接口地址：** `POST /api/chat/rooms/{room_id}/join`

**功能说明：** 加入指定的聊天室

**请求参数：**
- **Path参数：**
  - `room_id` (string, 必需): 聊天室ID

**响应示例：**
```json
{
  "message": "成功加入聊天室"
}
```

### 8. 离开聊天室

**接口地址：** `POST /api/chat/rooms/{room_id}/leave`

**功能说明：** 离开指定的聊天室

**请求参数：**
- **Path参数：**
  - `room_id` (string, 必需): 聊天室ID

**响应示例：**
```json
{
  "message": "成功离开聊天室"
}
```

### 9. 聊天室列表

**接口地址：** `GET /api/chat/rooms`

**功能说明：** 获取所有聊天室列表

**请求参数：** 无

**响应示例：**
```json
[
  {
    "id": "global",
    "name": "全局聊天室",
    "description": "所有用户的公共聊天室",
    "members": [1, 2, 3, 4, 5],
    "created_at": "2024-01-15T08:00:00",
    "last_message": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sender_id": 1,
      "sender_name": "张三",
      "message_type": "text",
      "content": "你好，世界！",
      "timestamp": "2024-01-15T10:30:00"
    }
  }
]
```

### 10. 删除消息

**接口地址：** `DELETE /api/chat/messages/{message_id}`

**功能说明：** 删除指定消息（软删除）

**请求参数：**
- **Path参数：**
  - `message_id` (string, 必需): 消息ID
- **Query参数：**
  - `room_id` (string, 可选): 聊天室ID，默认为"global"

**响应示例：**
```json
{
  "message": "消息删除成功"
}
```

### 11. 用户IP查询

**接口地址：** `GET /api/chat/user-ip/{user_id}`

**功能说明：** 获取指定用户的IP地址

**请求参数：**
- **Path参数：**
  - `user_id` (int, 必需): 用户ID

**响应示例：**
```json
{
  "user_id": 1,
  "ip": "192.168.1.100"
}
```

### 12. 心跳检测

**接口地址：** `POST /api/chat/heartbeat`

**功能说明：** 保持用户在线状态，更新最后活动时间

**请求参数：** 无

**响应示例：**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00"
}
```

## 数据模型

### 消息类型枚举 (MessageType)
- `text`: 文本消息
- `file`: 文件消息
- `image`: 图片消息
- `system`: 系统消息

### 聊天消息 (ChatMessage)
```typescript
interface ChatMessage {
  id: string;                    // 消息唯一ID
  sender_id: number;             // 发送者用户ID
  sender_name: string;           // 发送者用户名
  message_type: MessageType;     // 消息类型
  content: string;               // 消息内容
  file_url?: string;             // 文件URL（可选）
  file_name?: string;            // 文件名（可选）
  file_size?: number;            // 文件大小（可选）
  timestamp: string;             // 发送时间（ISO格式）
  reply_to?: string;             // 回复的消息ID（可选）
}
```

### 在线用户 (OnlineUser)
```typescript
interface OnlineUser {
  user_id: number;               // 用户ID
  username: string;              // 用户名
  ip: string;                    // IP地址
  user_agent: string;            // 用户代理字符串
  login_time: string;            // 登录时间（ISO格式）
  last_activity: string;         // 最后活动时间（ISO格式）
}
```

### 聊天室 (ChatRoom)
```typescript
interface ChatRoom {
  id: string;                    // 聊天室ID
  name: string;                  // 聊天室名称
  description?: string;          // 聊天室描述（可选）
  members: number[];             // 成员用户ID列表
  created_at: string;            // 创建时间（ISO格式）
  last_message?: ChatMessage;    // 最后一条消息（可选）
}
```

### 聊天统计 (ChatStats)
```typescript
interface ChatStats {
  online_users_count: number;    // 在线用户数
  total_messages_today: number;  // 今日消息总数
  active_rooms: number;          // 活跃聊天室数
}
```

## 错误码说明

| HTTP状态码 | 错误类型 | 说明 |
|------------|----------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 请求错误 | 请求参数错误或格式不正确 |
| 401 | 未授权 | 未提供有效的JWT Token |
| 403 | 权限不足 | 没有执行该操作的权限 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 413 | 文件过大 | 上传的文件超过大小限制 |
| 415 | 文件类型不支持 | 上传的文件类型不在允许列表中 |
| 500 | 服务器错误 | 服务器内部错误 |

**错误响应格式：**
```json
{
  "detail": "具体的错误信息描述"
}
```

## 使用示例

### 前端集成示例

#### 1. 初始化聊天系统
```javascript
class ChatAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // 发送消息
  async sendMessage(content, roomId = 'global', replyTo = null) {
    const response = await fetch(`${this.baseURL}/api/chat/send?room_id=${roomId}`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        message_type: 'text',
        content: content,
        reply_to: replyTo
      })
    });
    return await response.json();
  }

  // 获取消息历史
  async getMessages(roomId = 'global', limit = 50, before = null) {
    let url = `${this.baseURL}/api/chat/messages?room_id=${roomId}&limit=${limit}`;
    if (before) url += `&before=${before}`;
    
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return await response.json();
  }

  // 上传文件
  async uploadFile(file, roomId = 'global') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('room_id', roomId);
    
    const response = await fetch(`${this.baseURL}/api/chat/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });
    return await response.json();
  }

  // 获取在线用户
  async getOnlineUsers() {
    const response = await fetch(`${this.baseURL}/api/chat/online-users`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return await response.json();
  }

  // 心跳检测
  async heartbeat() {
    const response = await fetch(`${this.baseURL}/api/chat/heartbeat`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return await response.json();
  }
}
```

#### 2. 使用示例
```javascript
// 初始化API客户端
const chatAPI = new ChatAPI('http://localhost:8000', 'your_jwt_token');

// 发送消息
chatAPI.sendMessage('Hello, World!').then(message => {
  console.log('消息已发送:', message);
});

// 获取消息历史
chatAPI.getMessages().then(messages => {
  console.log('消息历史:', messages);
});

// 上传文件
const fileInput = document.getElementById('file');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    const result = await chatAPI.uploadFile(file);
    console.log('文件上传成功:', result);
  }
});

// 定时心跳检测
setInterval(() => {
  chatAPI.heartbeat().then(result => {
    console.log('心跳检测:', result);
  });
}, 30000); // 每30秒一次
```

## 注意事项

1. **认证要求**：所有接口都需要有效的JWT Token认证
2. **频率限制**：建议心跳检测间隔30秒，避免过于频繁的请求
3. **文件安全**：上传的文件会进行类型和大小检查
4. **消息持久化**：消息在Redis中保存7天，每个聊天室最多保留1000条消息
5. **在线状态**：用户30分钟无活动将自动标记为离线
6. **错误处理**：建议对所有API调用进行适当的错误处理
7. **实时性**：如需实时聊天效果，建议结合WebSocket或定时轮询

## 技术支持

如有任何问题或需要技术支持，请参考：
- API文档：`http://localhost:8000/docs`
- 详细文档：`backend/CHAT_API_README.md`
- 接口测试：使用Postman或类似工具进行API测试 
<template>
  <div id="app" class="app-layout">
    
    <!-- 左侧固定常驻侧边栏 (模仿 DeepSeek) -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-logo">KNOW-LAW</span>
      </div>
      
      <div class="new-chat-btn" @click="createNewSession">
        <i class="el-icon-plus"></i> <span style="margin-left: 5px;">新对话</span>
      </div>
      
      <div class="history-wrapper">
        <div class="history-title">历史记录</div>
        <ul class="history-list">
          <li 
            v-for="(session, index) in sessions" 
            :key="session.id || index"
            :class="['history-item', { active: currentSessionIndex === index }]"
            @click="switchSession(index)"
          >
            <div v-if="editingSessionId === session.id" class="edit-mode" @click.stop>
              <el-input 
                size="mini" 
                v-model="editTitleTemp" 
                @keyup.enter.native="confirmEditSession(session)" 
                @blur="confirmEditSession(session)"
                ref="editInput"
              ></el-input>
            </div>
            <div v-else class="view-mode">
              <span class="session-text">{{ session.title }}</span>
              <span class="session-actions">
                <i class="el-icon-edit-outline" @click.stop="startEditSession(session)"></i>
                <i class="el-icon-delete" @click.stop="deleteSession(session.id, index)"></i>
              </span>
            </div>
          </li>
        </ul>
      </div>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-info-left">
            <div class="avatar-wrapper">
              <i class="el-icon-user-solid"></i>
            </div>
            <span class="user-name">法律咨询用户</span>
          </div>
          <i class="el-icon-more more-icon"></i>
        </div>
      </div>
    </aside>

    <!-- 中间主对话区 -->
    <main class="chat-main">
      <header class="chat-header">
        <span class="header-title">{{ sessions[currentSessionIndex] ? sessions[currentSessionIndex].title : '法律咨询' }}</span>
      </header>
      
      <!-- 滚动对话框 (绝对填充，通过 padding 留空间保证不遮挡) -->
      <div class="chat-scroll-area" ref="chatHistory">
        <div class="message-list">
          
          <div v-if="messages.length === 0" class="empty-state">
            <div class="ai-logo-large">KL</div>
            <h2 class="welcome-title">我是 Know-Law 法律助手</h2>
            <p class="welcome-subtitle">我可以帮你分析合同漏洞、解答刑法知识，或提供法律建议。</p>
            
            <div class="suggestion-cards">
              <div class="card" @click="query = '帮我草拟一份简单的房屋租赁合同'; sendMessageWrapper()">
                <i class="el-icon-document"></i>
                <span style="margin-left: 5px;">起草房屋租赁合同</span>
              </div>
              <div class="card" @click="query = '劳动者被无故辞退，该如何申请劳动仲裁？'; sendMessageWrapper()">
                <i class="el-icon-s-custom"></i>
                <span style="margin-left: 5px;">劳动纠纷维权指南</span>
              </div>
            </div>
          </div>

          <!-- 消息流 (左右错开排版) -->
          <div v-else class="messages-wrapper">
            <div v-for="(msg, index) in messages" :key="index" :class="['msg-row', msg.role]">
              
              <!-- AI 头像 -->
              <div class="ai-avatar" v-if="msg.role === 'ai'">KL</div>
              
              <!-- 消息内容体 -->
              <div class="msg-bubble">
                <div v-if="msg.role === 'ai'" class="ai-content markdown-body" v-html="parseMarkdown(msg.content)"></div>
                <div v-else class="user-content">{{ msg.content }}</div>
                
                <div v-if="msg.sources && msg.sources.length" class="reference-block">
                  <div class="ref-title"><i class="el-icon-collection"></i> 法律依据引用</div>
                  <div class="ref-content">{{ msg.sources.join('、') }}</div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- 底部悬浮输入框层 -->
      <div class="input-wrapper">
        <div class="input-container">
          
          <div v-if="uploadedFile" class="attachment-badge">
            <div class="file-icon"><i class="el-icon-document"></i></div>
            <span class="file-name" style="margin: 0 4px;">{{ uploadedFile.name }}</span>
            <i class="el-icon-close close-file" @click="removeFile"></i>
          </div>

          <div class="input-controls">
            <el-upload
              class="upload-trigger"
              action="http://localhost:9091/upload"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              accept=".pdf,.docx,.txt"
            >
              <el-tooltip content="上传案卷或合同(PDF/DOCX/TXT)" placement="top" :open-delay="500">
                <div class="tool-btn attach-btn">
                  <i class="el-icon-paperclip"></i>
                </div>
              </el-tooltip>
            </el-upload>
            
            <el-tooltip :content="isDeepThinkMode ? '已开启深度思考' : '开启深度思考'" placement="top">
              <div 
                class="tool-btn deep-think-btn" 
                :class="{ 'active': isDeepThinkMode }" 
                @click="isDeepThinkMode = !isDeepThinkMode"
              >
                 <i class="el-icon-aim"></i> <span class="btn-text">深度分析</span>
              </div>
            </el-tooltip>

            <el-input
              v-model="query"
              type="textarea"
              autosize
              placeholder="给 Know-Law 发送消息..."
              @keyup.enter.native.exact="sendMessageWrapper"
              :disabled="loading"
              class="transparent-input"
            ></el-input>

            <div class="send-action">
              <div 
                class="send-btn" 
                :class="{ active: (query && query.trim() || uploadedFile) && !loading }"
                @click="sendMessageWrapper"
              >
                <i v-if="loading" class="el-icon-loading"></i>
                <i v-else class="el-icon-position"></i>
              </div>
            </div>
          </div>
        </div>
        <div class="disclaimer">内容由 AI 生成，仅供参考。对于具体的法律案件，请咨询专业律师。</div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { marked } from 'marked';

export default {
  name: 'App',
  data() {
    return {
      query: '',
      sessions: [],
      currentSessionIndex: 0,
      loading: false,
      editingSessionId: null,
      editTitleTemp: '',
      uploadedFile: null,
      isDeepThinkMode: false
    };
  },
  computed: {
    messages() {
      if (this.sessions.length === 0) return [];
      return this.sessions[this.currentSessionIndex].messages || [];
    }
  },
  mounted() {
    this.loadSessions();
  },
  methods: {
    sendMessageWrapper(e) {
      if (e) e.preventDefault();
      this.sendMessage();
    },
    handleUploadSuccess(res) {
      if (res.error) {
        this.$message.error('解析文件失败：' + res.error);
        return;
      }
      this.uploadedFile = {
        name: res.filename,
        content: res.content
      };
      this.$message.success('文件读取成功，请发送问题！');
    },
    handleUploadError() {
      this.$message.error('文件上传失败，请检查后端服务。');
    },
    beforeUpload(file) {
      const isAllowed = file.name.endsWith('.pdf') || file.name.endsWith('.docx') || file.name.endsWith('.txt');
      if (!isAllowed) {
        this.$message.error('只能上传 PDF, DOCX 或 TXT 格式的文件');
      }
      return isAllowed;
    },
    removeFile() {
      this.uploadedFile = null;
    },
    async loadSessions() {
      try {
        const { data } = await axios.get("http://localhost:9091/sessions");
        if (data && data.length > 0) {
          this.sessions = data.map(s => ({ ...s, messages: [] }));          
          const emptyNewIndex = this.sessions.findIndex(s => s.title === "新会话");
          if (emptyNewIndex !== -1) {
            this.switchSession(emptyNewIndex);
          } else {
            const res = await axios.post("http://localhost:9091/sessions");
            this.sessions.unshift({ ...res.data, messages: [] });
            this.currentSessionIndex = 0;
          }
        } else {
          this.createNewSession();
        }
      } catch (e) {
        console.error("加载历史会话失败", e);
        this.createNewSession();
      }
    },
    async createNewSession() {
      const existingNewIndex = this.sessions.findIndex(s => s.title === "新会话" && (!s.messages || s.messages.length === 0));
      if (existingNewIndex !== -1) {
        this.switchSession(existingNewIndex);
        return;
      }
      try {
        const { data } = await axios.post("http://localhost:9091/sessions");
        this.sessions.unshift({ ...data, messages: [] });
        this.currentSessionIndex = 0;
      } catch (e) {
        console.error("创建会话失败", e);
      }
    },
    parseMarkdown(text) {
      if (!text) return "";
      return marked.parse(text);
    },
    startEditSession(session) {
      this.editingSessionId = session.id;
      this.editTitleTemp = session.title;
      this.$nextTick(() => {
        if(this.$refs.editInput && this.$refs.editInput.length > 0) {
            this.$refs.editInput[0].focus();
        }
      });
    },
    async confirmEditSession(session) {
      if (!this.editingSessionId) return;
      const newTitle = this.editTitleTemp.trim() || "新会话";
      session.title = newTitle;
      this.editingSessionId = null;
      try {
        await axios.put(`http://localhost:9091/sessions/${session.id}`, { title: newTitle });
      } catch (e) {
        console.error("修改名字失败", e);
        this.$message.error("保存标题失败");
      }
    },
    async deleteSession(id, index) {
      try {
        await this.$confirm("确定删除这份法律问答吗？", "高能提示", { type: "warning" });
        await axios.delete(`http://localhost:9091/sessions/${id}`);
        this.sessions.splice(index, 1);
        if (this.sessions.length === 0) {
          this.createNewSession();
        } else if (this.currentSessionIndex === index) {
          this.switchSession(0);
        } else if (this.currentSessionIndex > index) {
          this.currentSessionIndex--;
        }
      } catch (e) {
        if (e !== "cancel") console.error("删除失败", e);
      }
    },
    async switchSession(index) {
      this.currentSessionIndex = index;
      const session = this.sessions[index];
      if (!session.messages || session.messages.length === 0) {
        try {
          const { data } = await axios.get(`http://localhost:9091/sessions/${session.id}/messages`);
          this.$set(session, "messages", data || []);
          this.$nextTick(() => { this.scrollToBottom(); });
        } catch (e) {
          console.error("加载记录失败", e);
        }
      } else {
          this.$nextTick(() => { this.scrollToBottom(); });
      }
    },
    async sendMessage() {
      if ((!this.query || !this.query.trim()) && !this.uploadedFile) return;
      const currentQuery = this.query || '';
      const currentSession = this.sessions[this.currentSessionIndex];
      
      if (currentSession.messages.length === 0 && currentQuery) {
        currentSession.title = currentQuery.length > 20 ? currentQuery.substring(0, 20) + "..." : currentQuery;
      }
      
      if (currentQuery.trim()) {
          currentSession.messages.push({ role: "user", content: currentQuery });
      } else if (this.uploadedFile) {
          currentSession.messages.push({ role: "user", content: `[已上传案件材料]：《${this.uploadedFile.name}》` });
      }
      
      const aiMessage = { role: "ai", content: "深度思考中...", sources: [] };
      currentSession.messages.push(aiMessage);
      
      this.query = "";
      this.loading = true;
      this.$nextTick(() => { this.scrollToBottom(); });

      try {
        const payload = { 
          query: currentQuery || "提取并分析附件材料的法律风险点", 
          session_id: currentSession.id,
          deep_think: this.isDeepThinkMode
        };
        if (this.uploadedFile) {
          payload.file_name = this.uploadedFile.name;
          payload.file_content = this.uploadedFile.content;
          this.uploadedFile = null;
        }

        const response = await fetch("http://localhost:9091/law_agent/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        
        if (!response.body) throw new Error("ReadableStream not supported");
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let isFirstChunk = true; 
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop(); 

          for (const line of lines) {
            if (line.trim() === "") continue;
            if (line.startsWith("data: ")) {
              const dataStr = line.slice(6).trim();
              if (dataStr) {
                try {
                  const data = JSON.parse(dataStr);
                  if (isFirstChunk) {
                    aiMessage.content = "";
                    isFirstChunk = false;
                  }
                  aiMessage.content += data.content;
                  this.$nextTick(() => { this.scrollToBottom(); });
                } catch (e) {}
              }
            }
          }
        }
      } catch (error) {
        this.$message.error("网络访问不畅");
        aiMessage.content = "网络连接出错，请检查服务端状态。";
      } finally {
        this.loading = false;
        this.$nextTick(() => { this.scrollToBottom(); });
      }
    },
    scrollToBottom() {
      const container = this.$refs.chatHistory;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }
}
</script>

<style>
html, body {
  margin: 0; padding: 0; height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
  background-color: #ffffff; color: #111827;
  -webkit-font-smoothing: antialiased;
}

.app-layout {
  height: 100vh; width: 100vw; display: flex; overflow: hidden; background: #ffffff;
}

/* ====== 左侧固定边栏 ====== */
.sidebar {
  width: 260px; background-color: #f9fafb; border-right: 1px solid rgba(0,0,0,0.05);
  display: flex; flex-direction: column; flex-shrink: 0; z-index: 10;
}
.sidebar-header { padding: 20px 20px 15px; }
.sidebar-logo { font-weight: 700; font-size: 16px; color: #111827; }
.new-chat-btn {
  margin: 0 16px 20px; height: 40px; background-color: #ffffff;
  border: 1px solid #e5e7eb; border-radius: 8px; display: flex; align-items: center; justify-content: center; gap: 8px;
  font-size: 14px; font-weight: 500; color: #374151; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.new-chat-btn:hover { background-color: #111827; color: #ffffff; border-color: #111827; }
.history-wrapper { flex: 1; overflow-y: auto; padding: 0 16px; }
.history-title { font-size: 12px; color: #9ca3af; font-weight: 600; margin: 10px 8px; }
.history-list { list-style: none; padding: 0; margin: 0; }
.history-item {
  padding: 10px 12px; font-size: 14px; color: #4b5563; border-radius: 8px; margin-bottom: 4px; cursor: pointer; transition: background 0.2s;
}
.history-item:hover { background-color: #f3f4f6; color: #111827; }
.history-item.active { background-color: #e5e7eb; font-weight: 500; color: #111827; }
.view-mode { display: flex; justify-content: space-between; align-items: center; }
.session-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.session-actions { display: none; color: #9ca3af; gap: 8px; }
.history-item:hover .session-actions { display: flex; }
.sidebar-footer { padding: 12px; border-top: 1px solid rgba(0,0,0,0.05); }
.user-info { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
.user-info:hover { background-color: #e5e7eb; }
.user-info-left { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 500; color: #374151; }
.avatar-wrapper { width: 28px; height: 28px; border-radius: 14px; background: #d1d5db; display: flex; align-items: center; justify-content: center; color: #4b5563; font-size: 14px; }
.user-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 120px; font-weight: 500; }
.more-icon { color: #9ca3af; font-size: 18px; }

/* ====== 中间主区域 ====== */
.chat-main { flex: 1; display: flex; flex-direction: column; position: relative; background-color: #ffffff; min-width: 0; }
.chat-header {
  height: 56px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #f3f4f6;
  font-size: 15px; font-weight: 500; color: #374151; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px);
  z-index: 20; position: absolute; top:0; left: 0; right: 0;
}
.chat-scroll-area {
  flex: 1; overflow-y: auto; scroll-behavior: smooth; padding-top: 56px; padding-bottom: 180px; width: 100%;
}
.message-list { max-width: 800px; margin: 0 auto; padding: 20px 20px 0; }

.empty-state { display: flex; flex-direction: column; align-items: center; margin-top: 15vh; animation: fadeUp 0.8s ease; }
.ai-logo-large {
  width: 60px; height: 60px; border-radius: 12px; background-color: #111827; color: white;
  display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; margin-bottom: 20px;
}
.welcome-title { font-size: 28px; font-weight: 600; margin-bottom: 10px; }
.welcome-subtitle { font-size: 15px; color: #6b7280; margin-bottom: 40px; }
.suggestion-cards { display: flex; gap: 16px; cursor: pointer; }
.card {
  padding: 16px 20px; border: 1px solid #f3f4f6; border-radius: 12px; display: flex; align-items: center; gap: 10px; font-size: 14px;
}
.card:hover { border-color: #e5e7eb; background: #f9fafb; }

.messages-wrapper { margin-top: 20px; }
.msg-row { display: flex; margin-bottom: 32px; width: 100%; }
.msg-row.user { flex-direction: row-reverse; }
.msg-row.ai { flex-direction: row; align-items: flex-start; }
.ai-avatar {
  width: 32px; height: 32px; border-radius: 6px; background-color: #111827; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; margin-right: 16px; flex-shrink: 0; margin-top: 4px;
}
.user-content {
  background-color: #f3f4f6; color: #111827; padding: 12px 18px; border-radius: 16px; border-top-right-radius: 4px;
  font-size: 15px; line-height: 1.6; max-width: 85%; word-wrap: break-word;
}
.msg-row.ai .msg-bubble { max-width: 85%; color: #111827; font-size: 15px; line-height: 1.7; width: 100%;}
.reference-block { margin-top: 16px; padding: 12px 16px; background-color: #f9fafb; border-radius: 8px; border-left: 4px solid #d1d5db; font-size: 13px; }
.ref-title { font-weight: 600; margin-bottom: 6px; color: #374151; }

/* ====== 底部悬浮 ====== */
.input-wrapper {
  position: absolute; bottom: 0; left: 0; right: 0; padding: 0 20px 30px; box-sizing: border-box;
  background: linear-gradient(to top, #ffffff 70%, rgba(255,255,255,0) 100%); pointer-events: none;
  display: flex; flex-direction: column; align-items: center;
}
.input-container {
  pointer-events: auto; width: 100%; max-width: 800px; background-color: #f4f4f5; border-radius: 16px; padding: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.05); transition: all 0.3s;
}
.input-container:focus-within { background-color: #ffffff; border-color: #d1d5db; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }
.attachment-badge {
  display: flex; align-items: center; gap: 8px; background: #ffffff; padding: 6px 12px; border-radius: 8px; border: 1px solid #e5e7eb;
  font-size: 13px; margin-bottom: 12px; width: fit-content; pointer-events: auto;
}
.input-controls { display: flex; align-items: flex-end; gap: 8px; }
.tool-btn {
  width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
  color: #6b7280; font-size: 18px; cursor: pointer; margin-bottom: 2px;
}
.tool-btn:hover { background-color: #e5e7eb; color: #111827; }
.deep-think-btn { width: auto; padding: 0 10px; border: 1px solid #d1d5db; font-size: 14px; gap: 4px; border-radius: 17px; background: transparent; cursor: pointer; transition: all 0.2s;}
.deep-think-btn.active { border-color: #3b82f6; color: #3b82f6; background-color: #eff6ff; }
.transparent-input { flex: 1; }
.transparent-input textarea {
  border: none !important; background: transparent !important; box-shadow: none !important; font-size: 15px; margin: 0;
  color: #111827; padding: 6px 4px !important; line-height: 1.5; resize: none; max-height: 150px;
}
.send-action { margin-bottom: 2px; }
.send-btn {
  width: 34px; height: 34px; border-radius: 8px; background-color: #e5e7eb; color: #9ca3af; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: all 0.3s;
}
.send-btn.active { background-color: #111827; color: #ffffff; cursor: pointer; }
.disclaimer { text-align: center; font-size: 12px; color: #9ca3af; margin-top: 12px; pointer-events: auto; }

/* Markdown */
.markdown-body p { margin-top: 0; margin-bottom: 1.25em; }
.markdown-body strong { font-weight: 600; }
.markdown-body table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px; }
.markdown-body th, .markdown-body td { border: 1px solid #e5e7eb; padding: 10px 14px; }
.markdown-body th { background: #f9fafb; font-weight: 600; text-align: left; }
.markdown-body pre { background: #f3f4f6; border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 15px 0; }
.markdown-body code { font-family: ui-monospace, sans-serif; background: #f3f4f6; padding: 3px 6px; border-radius: 4px; color: #ef4444; }
.markdown-body pre code { background: transparent; padding: 0; color: inherit; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

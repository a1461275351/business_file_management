<template>
  <div class="ai-page">
    <el-row :gutter="16">
      <!-- 左侧：功能卡片 -->
      <el-col :span="8">
        <div class="feature-list">
          <div class="feature-card" v-for="f in features" :key="f.title" @click="insertPrompt(f.prompt)">
            <div class="feature-icon" :style="{ background: f.bg }">{{ f.icon }}</div>
            <div class="feature-info">
              <div class="feature-title">{{ f.title }}</div>
              <div class="feature-desc">{{ f.desc }}</div>
            </div>
          </div>
        </div>

        <el-card shadow="never" class="mt-16">
          <template #header><span>使用说明</span></template>
          <div class="tips">
            <p>基于系统内的文件数据进行智能问答，支持：</p>
            <ul>
              <li>查询订单/客户/金额等业务数据</li>
              <li>跨文件数据比对和异常检测</li>
              <li>生成统计分析报告</li>
              <li>HS编码查询和贸易政策咨询</li>
            </ul>
            <p class="tip-note">💡 点击左侧卡片可快速插入常用问题</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：对话区 -->
      <el-col :span="16">
        <el-card shadow="never" class="chat-card">
          <template #header>
            <div class="chat-header">
              <div class="chat-title">
                <span class="ai-dot"></span>
                外贸业务助手
              </div>
              <el-button size="small" @click="clearChat"><el-icon><Delete /></el-icon> 清空对话</el-button>
            </div>
          </template>

          <!-- 消息列表 -->
          <div class="chat-messages" ref="messagesRef">
            <div v-if="!messages.length" class="chat-welcome">
              <div class="welcome-icon">🤖</div>
              <h3>你好，我是外贸业务助手</h3>
              <p>我可以帮你查询文件数据、分析业务趋势、检测异常。试试问我：</p>
              <div class="welcome-prompts">
                <span class="prompt-tag" v-for="p in quickPrompts" :key="p" @click="sendMessage(p)">{{ p }}</span>
              </div>
            </div>

            <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role === 'user' ? 'msg-user' : 'msg-ai']">
              <div class="msg-content">
                <div class="msg-text" v-html="formatMessage(msg.content)"></div>
                <div class="msg-time">{{ msg.time }}</div>
              </div>
            </div>

            <div v-if="loading" class="msg msg-ai">
              <div class="msg-content">
                <div class="msg-text typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区 -->
          <div class="chat-input">
            <el-input
              v-model="inputText"
              placeholder="输入问题，如：查询本月报关单总金额..."
              @keyup.enter="sendMessage()"
              :disabled="loading"
              size="large"
            >
              <template #append>
                <el-button type="primary" @click="sendMessage()" :loading="loading" :icon="Promotion">发送</el-button>
              </template>
            </el-input>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { Promotion, Delete } from '@element-plus/icons-vue';
import http from '@/api/http';

const inputText = ref('');
const messages = ref([]);
const loading = ref(false);
const messagesRef = ref(null);

const quickPrompts = [
    '本月上传了多少份文件？',
    '有哪些文件还未归档？',
    '报关单的平均金额是多少？',
];

const features = [
    { icon: '🔍', title: '智能文件问答', desc: '查询订单、金额、客户信息', bg: '#e6f1fb', prompt: '请帮我查询系统中的文件统计信息' },
    { icon: '⚡', title: '异常预警', desc: '发票与报关单金额比对', bg: '#eaf3de', prompt: '请检查是否有发票和报关单金额不一致的情况' },
    { icon: '📊', title: '业务趋势', desc: '按月/客户/商品统计分析', bg: '#faeeda', prompt: '请分析本月的文件上传趋势' },
    { icon: '📋', title: 'HS编码查询', desc: '海关编码分类和税率', bg: '#faece7', prompt: '请帮我查询HS编码 8542310001 对应的商品类别' },
];

function insertPrompt(prompt) {
    inputText.value = prompt;
}

function formatMessage(text) {
    // 简单 markdown 转换
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function scrollToBottom() {
    nextTick(() => {
        if (messagesRef.value) {
            messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
        }
    });
}

async function sendMessage(text) {
    const content = text || inputText.value.trim();
    if (!content) return;

    // 添加用户消息
    messages.value.push({
        role: 'user',
        content,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    });
    inputText.value = '';
    scrollToBottom();

    // 调用 AI
    loading.value = true;
    try {
        const res = await http.post('/ai/chat', {
            message: content,
            history: messages.value.slice(-10).map(m => ({ role: m.role, content: m.content })),
        });

        messages.value.push({
            role: 'assistant',
            content: res.data?.reply || res.message || '暂时无法回答，请稍后再试',
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        });
    } catch {
        // AI 接口未实现时，用本地统计数据回答
        const reply = await getLocalAnswer(content);
        messages.value.push({
            role: 'assistant',
            content: reply,
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        });
    }
    loading.value = false;
    scrollToBottom();
}

async function getLocalAnswer(question) {
    try {
        const stats = await http.get('/documents/statistics');
        const s = stats.data;

        if (question.includes('文件') && (question.includes('多少') || question.includes('统计'))) {
            return `根据系统数据：\n\n**本月文件数**: ${s.total_this_month} 份\n**待处理**: ${s.pending_count} 份\n**字段提取准确率**: ${s.ocr_accuracy}%\n**已提取字段**: ${s.total_fields} 个\n\n文件类型分布：\n${(s.type_distribution || []).map(t => `- ${t.name}: ${t.count} 份`).join('\n')}`;
        }

        if (question.includes('未归档') || question.includes('待处理')) {
            return `当前有 **${s.pending_count}** 份文件待处理，请到「文件管理」页面查看详情。`;
        }

        return `根据当前系统数据：本月共 **${s.total_this_month}** 份文件，其中 **${s.pending_count}** 份待处理。\n\n如需更详细的分析，请在「数据报表」页面查看。\n\n_注：AI 问答功能将接入通义千问大模型，届时可进行更智能的业务分析。_`;
    } catch {
        return '抱歉，暂时无法获取系统数据。请确认服务正常运行后重试。';
    }
}

function clearChat() {
    messages.value = [];
}
</script>

<style scoped>
.feature-list { display: flex; flex-direction: column; gap: 10px; }
.feature-card { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid #e4e7ed; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.feature-card:hover { border-color: #409eff; background: #f5f9ff; }
.feature-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.feature-title { font-size: 13px; font-weight: 600; color: #303133; }
.feature-desc { font-size: 11px; color: #909399; margin-top: 2px; }
.tips { font-size: 13px; color: #606266; line-height: 1.8; }
.tips ul { padding-left: 18px; margin: 6px 0; }
.tip-note { color: #909399; font-size: 12px; margin-top: 8px; }

.chat-card :deep(.el-card__body) { padding: 0; display: flex; flex-direction: column; height: 520px; }
.chat-header { display: flex; justify-content: space-between; align-items: center; }
.chat-title { display: flex; align-items: center; gap: 8px; font-weight: 500; }
.ai-dot { width: 8px; height: 8px; border-radius: 50%; background: #67c23a; }

.chat-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.chat-welcome { text-align: center; padding: 40px 20px; color: #909399; }
.welcome-icon { font-size: 40px; margin-bottom: 12px; }
.chat-welcome h3 { color: #303133; font-size: 16px; margin-bottom: 8px; }
.chat-welcome p { font-size: 13px; }
.welcome-prompts { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 16px; }
.prompt-tag { padding: 6px 12px; background: #f0f7ff; color: #409eff; border-radius: 16px; font-size: 12px; cursor: pointer; }
.prompt-tag:hover { background: #409eff; color: #fff; }

.msg { display: flex; }
.msg-user { justify-content: flex-end; }
.msg-ai { justify-content: flex-start; }
.msg-content { max-width: 75%; }
.msg-text { padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.7; }
.msg-user .msg-text { background: #409eff; color: #fff; border-radius: 12px 12px 2px 12px; }
.msg-ai .msg-text { background: #f4f4f5; color: #303133; border-radius: 12px 12px 12px 2px; }
.msg-ai .msg-text :deep(strong) { color: #409eff; }
.msg-ai .msg-text :deep(code) { background: #e8e8e8; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.msg-time { font-size: 10px; color: #c0c4cc; margin-top: 4px; text-align: right; }
.msg-ai .msg-time { text-align: left; }

.typing span { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #c0c4cc; margin: 0 2px; animation: typing 1.2s infinite; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%,60%,100% { opacity:0.3; } 30% { opacity:1; } }

.chat-input { padding: 12px 16px; border-top: 1px solid #e4e7ed; }
.mt-16 { margin-top: 16px; }
</style>

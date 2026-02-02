import streamlit as st
import google.generativeai as genai
import time
import re
import sqlite3
import uuid

# -------------------------------------------------------------
# --- 0. 页面配置 ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="AI 财富人格实验室", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# --- 1. 数据与Prompt定义 ---
# -------------------------------------------------------------

# 仅保留基础描述，名人案例将改为动态生成
MBTI_META = {
    "INTJ": {"name": "建筑师", "icon": "🏰", "desc": "富有战略能力的思考者"},
    "INTP": {"name": "逻辑学家", "icon": "⚗️", "desc": "渴求知识的创新发明家"},
    "ENTJ": {"name": "指挥官", "icon": "🎬", "desc": "大胆果断的领导者"},
    "ENTP": {"name": "辩论家", "icon": "🗣️", "desc": "机智好奇的思想者"},
    "INFJ": {"name": "提倡者", "icon": "🕯️", "desc": "安静神秘的理想主义者"},
    "INFP": {"name": "调停者", "icon": "🍃", "desc": "诗意善良的利他主义者"},
    "ENFJ": {"name": "主人公", "icon": "⚔️", "desc": "魅力四射的领导者"},
    "ENFP": {"name": "竞选者", "icon": "🎉", "desc": "热情洋溢的自由人"},
    "ISTJ": {"name": "物流师", "icon": "📋", "desc": "注重事实的可靠人员"},
    "ISFJ": {"name": "守卫者", "icon": "🛡️", "desc": "专注温暖的守护者"},
    "ESTJ": {"name": "总经理", "icon": "👔", "desc": "出色的行政管理者"},
    "ESFJ": {"name": "执政官", "icon": "🤝", "desc": "极有同情心的社交达人"},
    "ISTP": {"name": "鉴赏家", "icon": "🔧", "desc": "大胆实际的实验家"},
    "ISFP": {"name": "探险家", "icon": "🎨", "desc": "灵活有魅力的艺术家"},
    "ESTP": {"name": "企业家", "icon": "🚀", "desc": "精力充沛的感知者"},
    "ESFP": {"name": "表演者", "icon": "💃", "desc": "热情自发的表演者"}
}

# -------------------------------------------------------------
# --- 2. CSS 样式 ---
# -------------------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    * { box-sizing: border-box; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #f4f7f9 !important;
        font-family: 'Noto Sans SC', sans-serif !important;
    }
    
    /* 隐藏顶部 */
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    .main .block-container { padding-top: 0 !important; max-width: 100% !important; }

    /* 导航栏 */
    .nav-bar {
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 15px 40px;
        position: sticky; top: 0; z-index: 999;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .logo-area { display: flex; align-items: center; }
    .logo-text { font-size: 1.2rem; font-weight: 700; color: #4b0082; margin-right: 10px; }
    .nav-tag { background: #f3e5f5; color: #4b0082; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }

    /* 案例卡片样式 */
    .case-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    .case-card {
        background: white;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 20px;
        transition: transform 0.2s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-top: 4px solid #4b0082;
    }
    .case-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .case-name { font-weight: 700; color: #333; font-size: 1.1rem; margin-bottom: 5px; }
    .case-company { font-size: 0.9rem; color: #666; font-weight: 600; margin-bottom: 10px; }
    .case-story { font-size: 0.9rem; color: #555; line-height: 1.6; }
    .case-tag { display: inline-block; background: #f3f0ff; color: #4b0082; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; margin-bottom: 10px; }

    /* 聊天气泡 */
    .chat-row { display: flex; margin-bottom: 20px; width: 100%; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }
    .chat-avatar { 
        width: 40px; height: 40px; border-radius: 8px; 
        display: flex; align-items: center; justify-content: center; 
        font-size: 24px; flex-shrink: 0; 
    }
    .assistant .chat-avatar { background: #4b0082; color: white; margin-right: 15px; }
    .user .chat-avatar { background: #8a2be2; color: white; margin-left: 15px; order: 2; }
    .chat-bubble { 
        padding: 15px 20px; border-radius: 10px; font-size: 0.95rem; line-height: 1.6; max-width: 80%; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .assistant .chat-bubble { background: white; border: 1px solid #eee; color: #333; }
    .user .chat-bubble { background: #4b0082; color: white; }

    /* 输入框固定底部 */
    [data-testid="stChatInput"] { background: white; border-top: 1px solid #eee; z-index: 1000; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 3. 核心功能函数 ---
# -------------------------------------------------------------

def clean_text(text):
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def markdown_to_html(text):
    """简易HTML渲染"""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) 
    return text.replace("\n", "<br>")

def stream_gemini(prompt, model):
    """流式输出"""
    try:
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.01)
    except Exception as e:
        yield f"⚠️ 连接中断: {str(e)[:50]}"

def generate_billionaire_cases(mbti_code, capital, api_key):
    """
    根据 MBTI 和 资金量，生成3个真实案例
    """
    if not api_key: return "请先配置 API Key"
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    作为一名商业历史学家和创业专家，请为我寻找 3 个真实的亿万富豪或极其成功的企业家案例。
    
    **筛选条件：**
    1. **人格类型**：必须被广泛认为是 **{mbti_code}** ({MBTI_META[mbti_code]['name']})。
    2. **起步资金**：他们的创业初期资金或资源情况，需**尽可能接近**用户提供的条件："{capital}"。
       - 如果用户资金很少（如几千元），请找白手起家、车库创业的案例。
       - 如果用户资金较多（如百万），请找利用第一桶金或家庭资助起步的案例。
    
    **输出格式要求（严格遵守 JSON 格式，不要Markdown代码块）：**
    [
        {{
            "name": "姓名",
            "company": "创立的公司",
            "start_capital_desc": "简述他的起步资金/资源情况",
            "strategy": "他如何利用这笔有限的资源，结合{mbti_code}性格优势获得了成功（100字以内）"
        }},
        ... (共3个)
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 清洗数据，防止模型返回 ```json ```
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return eval(clean_json) # 使用 eval 解析列表
    except Exception as e:
        print(f"Error generating cases: {e}")
        return []

# -------------------------------------------------------------
# --- 4. 初始化 ---
# -------------------------------------------------------------

gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
st.session_state["api_configured"] = bool(gemini_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "cases" not in st.session_state:
    st.session_state.cases = []

# -------------------------------------------------------------
# --- 5. 侧边栏：自评与设置 ---
# -------------------------------------------------------------

with st.sidebar:
    st.title("🎛️ 设置台")
    
    # === Tab 切换：直接选择 vs 快速自评 ===
    tab1, tab2 = st.tabs(["🧩 快速自评", "👇 直接选择"])
    
    with tab1:
        st.caption("回答 4 个问题，确定你的人格类型")
        
        q1 = st.radio("1. 精力来源：", ["E (外向：社交、活动)", "I (内向：独处、思考)"], index=1)
        q2 = st.radio("2. 认知方式：", ["S (实感：细节、现实)", "N (直觉：未来、概念)"], index=1)
        q3 = st.radio("3. 决策依据：", ["T (理智：逻辑、事实)", "F (情感：价值、和谐)"], index=0)
        q4 = st.radio("4. 生活方式：", ["J (判断：计划、有序)", "P (感知：灵活、随机)"], index=0)
        
        # 自动计算 Code
        calculated_code = q1[0] + q2[0] + q3[0] + q4[0]
        st.markdown(f"#### 你的结果：`{calculated_code}`")
        if st.button("使用此结果", type="primary", use_container_width=True):
            st.session_state.mbti_selected = calculated_code
            st.session_state.messages = [] # 重置对话
            st.session_state.cases = []    # 重置案例
            st.rerun()

    with tab2:
        manual_code = st.selectbox("选择 MBTI 类型", list(MBTI_META.keys()), index=0)
        if st.button("确认选择", use_container_width=True):
            st.session_state.mbti_selected = manual_code
            st.session_state.messages = []
            st.session_state.cases = []
            st.rerun()
            
    # 确保 session 中有值
    if "mbti_selected" not in st.session_state:
        st.session_state.mbti_selected = "INTJ" # 默认

    current_code = st.session_state.mbti_selected
    current_meta = MBTI_META[current_code]
    
    st.divider()
    
    # === 资金输入模块 ===
    st.subheader("💰 财富模拟器")
    st.caption(f"查找和 **{current_code}** 性格一样，且起步资金相似的富豪。")
    user_capital = st.text_input("输入你的现有资金/资源", placeholder="例：5000元, 10万, 或 '只有一台电脑'")
    
    if st.button("🔍 生成致富案例", type="primary", use_container_width=True):
        if not user_capital:
            st.warning("请输入资金量")
        elif not gemini_api_key:
            st.error("未配置 API Key")
        else:
            with st.spinner("正在检索商业史数据库..."):
                cases = generate_billionaire_cases(current_code, user_capital, gemini_api_key)
                st.session_state.cases = cases
                # 同时也重置对话，让AI带入新上下文
                st.session_state.messages = [{
                    "role": "assistant", 
                    "content": f"你好！我是 {current_code} ({current_meta['name']}) 型的人工智能助手。我看到了为你生成的 3 个案例，你想深入了解哪一个？或者我们可以聊聊如何用你手中的 **{user_capital}** 开始创业。"
                }]
                st.rerun()

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -------------------------------------------------------------
# --- 6. 主页面内容 ---
# -------------------------------------------------------------

# 导航
st.markdown(f"""
<div class="nav-bar">
    <div class="logo-area">
        <span class="logo-text">🧬 AI 财富人格实验室</span>
    </div>
    <div class="nav-tag">当前人格：{current_code} {current_meta['name']}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="padding: 20px;">', unsafe_allow_html=True)

# === 动态案例展示区 ===
if st.session_state.cases and isinstance(st.session_state.cases, list):
    st.markdown(f"### 🚀 {current_code} 创业蓝图：从 {user_capital} 起步")
    
    # 使用列布局展示卡片
    cols = st.columns(3)
    for i, case in enumerate(st.session_state.cases):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="case-card">
                <div class="case-tag">🌟 相似起步</div>
                <div class="case-name">{case.get('name', 'N/A')}</div>
                <div class="case-company">{case.get('company', 'N/A')}</div>
                <div style="font-size:0.85rem; color:#888; margin-bottom:8px;"><b>起步资源:</b> {case.get('start_capital_desc', '')}</div>
                <div class="case-story">{case.get('strategy', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")

elif not st.session_state.cases:
    # 引导提示
    st.info(f"👈 请在左侧输入你的**现有资金**，点击“生成致富案例”，看看历史上哪些 **{current_code}** 大佬是和你一样起步的。")


# === 聊天区域 ===
st.subheader(f"💬 与 {current_meta['name']} 对话")

# 聊天模型初始化
system_prompt = f"""
你现在是 {current_meta['name']} ({current_code})。你的性格特征是：{current_meta['desc']}。
用户目前的资金状况是：{user_capital if 'user_capital' in locals() else '未知'}。
请完全沉浸在这个人格中。
如果用户问创业建议，请结合你的性格优势（{current_code}）以及用户现有的资金量给出务实、犀利的建议。
参考已生成的案例（如果有）来激励用户。
"""
chat_model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)

# 渲染历史消息
for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "assistant"
    avatar = "👤" if msg["role"] == "user" else current_meta['icon']
    
    st.markdown(f"""
    <div class="chat-row {role_class}">
        <div class="chat-avatar">{avatar}</div>
        <div class="chat-bubble">{markdown_to_html(msg["content"])}</div>
    </div>
    """, unsafe_allow_html=True)

# 输入框
user_input = st.chat_input(f"问问 {current_code} 如何利用这笔钱...")

if user_input and st.session_state.get("api_configured"):
    # 用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f"""
    <div class="chat-row user">
        <div class="chat-avatar">👤</div>
        <div class="chat-bubble">{user_input}</div>
    </div>
    """, unsafe_allow_html=True)

    # AI 回复
    placeholder = st.empty()
    full_response = ""
    
    # 构建包含历史的 Prompt (简化版，防止 token 过长)
    # 实际生产中应保留更多上下文，这里仅发送当前 Prompt
    
    for chunk in stream_gemini(user_input, chat_model):
        full_response += chunk
        placeholder.markdown(f"""
        <div class="chat-row assistant">
            <div class="chat-avatar">{current_meta['icon']}</div>
            <div class="chat-bubble">{markdown_to_html(full_response)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown('</div>', unsafe_allow_html=True)

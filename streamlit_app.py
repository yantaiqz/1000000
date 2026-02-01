import streamlit as st
import google.generativeai as genai
import datetime
import time
import re
import sqlite3
import uuid

# -------------------------------------------------------------
# --- 0. 页面配置 ---
# -------------------------------------------------------------
st.set_page_config(
    page_title="MBTI人格分析助手", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# --- 1. CSS 注入 (新增人格分析/富豪案例卡片样式) ---
# -------------------------------------------------------------
st.markdown("""
<style>
    /* === 全局基础样式 === */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    * { box-sizing: border-box; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #f4f7f9 !important;
        font-family: 'Noto Sans SC', sans-serif !important;
        color: #333 !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    .main .block-container {
        padding: 0 !important;
        padding-bottom: 6rem !important;
        max-width: 100% !important;
    }

    /* === 顶部导航 === */
    .nav-bar {
        background: #fff; border-bottom: 1px solid #e0e0e0; padding: 15px 40px;
        position: sticky; top: 0; z-index: 999; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .logo-text { font-size: 1.2rem; font-weight: 700; color: #6a5acd; letter-spacing: 0.5px; }
    .nav-tag {
        background: #f0e6ff; color: #6a5acd; font-size: 0.75rem;
        padding: 4px 8px; border-radius: 4px; margin-left: 12px; font-weight: 500;
    }

    /* === 主容器 === */
    .main-content-wrapper { max-width: 900px; margin: 0 auto; padding: 30px 20px; }

    /* === 标题区域 === */
    .hero-section { margin-bottom: 30px; text-align: left; }
    .page-title { font-size: 2rem !important; font-weight: 700 !important; color: #1a1a1a !important; margin-bottom: 8px !important; }
    .subtitle { font-size: 1rem !important; color: #666 !important; font-weight: 400 !important; }

    /* === 聊天气泡 === */
    [data-testid="stChatMessage"] { background: transparent !important; padding: 10px 0 !important; }
    [data-testid="stChatMessage"] > div:first-child { display: none !important; }
    .chat-row { display: flex; margin-bottom: 20px; width: 100%; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }
    .chat-avatar {
        width: 36px; height: 36px; border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; flex-shrink: 0;
    }
    .assistant .chat-avatar { background: #6a5acd; color: white; margin-right: 12px; }
    .user .chat-avatar { background: #9370db; color: white; margin-left: 12px; order: 2; }
    .chat-bubble {
        padding: 16px 20px; border-radius: 8px; font-size: 0.95rem;
        line-height: 1.6; max-width: 85%; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .assistant .chat-bubble { background: #fff; border: 1px solid #e0e0e0; color: #1a1a1a; }
    .user .chat-bubble { background: #6a5acd; color: white; }

    /* === 功能卡片 (MBTI选择/分析/富豪案例) === */
    .func-card {
        background: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
        padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .func-card-title {
        font-size: 1rem; font-weight: 700; color: #6a5acd;
        margin-bottom: 15px; padding-left: 8px; border-left: 3px solid #6a5acd;
    }

    /* === 模型卡片 === */
    .model-section-title {
        font-size: 0.9rem; font-weight: 700; color: #555;
        margin: 30px 0 15px 0; text-transform: uppercase;
        letter-spacing: 0.5px; border-left: 4px solid #6a5acd;
        padding-left: 10px;
    }
    .model-card {
        background: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
        margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .model-card-header {
        padding: 12px 20px; font-size: 0.9rem; font-weight: 600;
        background: #f8f9fa; border-bottom: 1px solid #e0e0e0;
        display: flex; align-items: center;
    }
    .gemini-header { color: #6a5acd; }
    .model-card-content {
        padding: 20px; font-size: 0.95rem; line-height: 1.7; color: #333;
    }

    /* === 底部输入框 === */
    [data-testid="stChatInput"] {
        background: white !important; padding: 20px 0 !important;
        border-top: 1px solid #e0e0e0 !important;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.03) !important;
        z-index: 1000;
    }
    [data-testid="stChatInput"] > div { max-width: 900px !important; margin: 0 auto !important; }

    /* === 按钮样式 === */
    div.stButton > button {
        border-radius: 6px !important; border: 1px solid #dcdfe6 !important;
        background: white !important; color: #333 !important;
        font-weight: 500 !important; transition: all 0.2s !important;
    }
    div.stButton > button:hover {
        border-color: #6a5acd !important; color: #6a5acd !important;
        background: #f0e6ff !important;
    }
    [data-testid="stButton"] button[kind="secondary"] {
        margin-top: 10px; width: 100%; border-style: dashed !important;
    }

    /* === 光标动画 === */
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    .blinking-cursor { animation: blink 1s infinite; color: #6a5acd; font-weight: bold; margin-left: 2px;}

    /* === 统计模块 === */
    .metric-container {
        display: flex; justify-content: center; gap: 20px;
        margin-top: 20px; padding: 10px; background: #f8f9fa;
        border-radius: 10px; border: 1px solid #e9ecef;
    }
    .metric-box { text-align: center; }
    .metric-sub { font-size: 0.7rem; color: #adb5bd; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 工具函数：文本格式化 ---
# -------------------------------------------------------------
def clean_extra_newlines(text):
    """清理冗余换行/空格"""
    cleaned = re.sub(r'\n{3,}', '\n\n', text)
    cleaned = re.sub(r'　+', '', cleaned)
    return cleaned.strip('\n')

def markdown_to_html(text):
    """Markdown转HTML，适配页面样式"""
    lines = [re.sub(r'###+', '', line.strip()) for line in text.split("\n") if not line.strip().startswith("###")]
    html_lines, in_list = [], False
    for line in lines:
        if not line: continue
        # 处理加粗标题
        if line.startswith("**") and line.endswith("**"):
            if in_list: html_lines.append("</ul>"); in_list = False
            content = line.strip("*")
            html_lines.append(f"<div style='color: #6a5acd; font-weight: 700; margin: 16px 0 8px; font-size: 1rem;'>{content}</div>")
        # 处理列表
        elif line.startswith(("- ", "* ")):
            if not in_list: html_lines.append("<ul style='margin: 0 0 16px 20px; padding: 0;'>"); in_list = True
            content = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#6a5acd; font-weight:600;">\1</span>', line[2:].strip())
            html_lines.append(f"<li style='margin-bottom: 6px;'>{content}</li>")
        # 处理普通段落
        else:
            if in_list: html_lines.append("</ul>"); in_list = False
            line = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#6a5acd; font-weight:600;">\1</span>', line)
            html_lines.append(f"<p style='margin-bottom: 10px;'>{line}</p>")
    if in_list: html_lines.append("</ul>")
    return "\n".join(html_lines)

# -------------------------------------------------------------
# --- 常量定义：MBTI类型+人格描述+白手起家富豪案例 ---
# -------------------------------------------------------------
USER_ICON = "👤"
ASSISTANT_ICON = "🧠"
GEMINI_ICON = "♊️"

# MBTI 16型人格定义
MBTI_16_TYPES = [
    "ISTJ - 检查员", "ISFJ - 守护者", "INFJ - 咨询师", "INTJ - 策划师",
    "ISTP - 手艺人", "ISFP - 艺术家", "INFP - 调停者", "INTP - 逻辑学家",
    "ESTP - 企业家", "ESFP - 表演者", "ENFP - 活动家", "ENTP - 辩论家",
    "ESTJ - 总经理", "ESFJ - 执政官", "ENFJ - 教育家", "ENTJ - 指挥官"
]

# 【核心新增】16型人格白手起家亿万富豪案例（每类3个，真实知名人物）
MBTI_BILLIONAIRES = {
    "ISTJ - 检查员": [
        "沃伦·巴菲特（Warren Buffett）：伯克希尔·哈撒韦公司创始人，从报童起家，凭借严谨的价值投资成为世界首富之一，典型的ISTJ稳重、理性、注重规则的特质。",
        "山姆·沃尔顿（Sam Walton）：沃尔玛创始人，白手起家打造全球最大零售帝国，做事有条理、务实专注，坚持低成本运营的核心原则。",
        "李嘉诚：长江实业创始人，从塑胶厂学徒起家，凭借谨慎的决策、超强的责任心和长期规划，成为华人商界传奇。"
    ],
    "ISFJ - 守护者": [
        "霍华德·舒尔茨（Howard Schultz）：星巴克CEO，从普通销售员接手星巴克，注重员工和顾客体验，用温暖的服务打造咖啡帝国，极具同理心。",
        "玫琳凯·艾施（Mary Kay Ash）：玫琳凯化妆品创始人，白手起家打造女性创业平台，关爱女性、乐于奉献，是ISFJ乐于助人的典范。",
        "稻盛和夫：京瓷/KDDI创始人，从技术员起家，秉持“敬天爱人”的理念，注重团队和谐，用真诚和责任带领企业成为世界500强。"
    ],
    "INFJ - 咨询师": [
        "马云：阿里巴巴创始人，白手起家打造电商帝国，极具洞察力和理想主义，始终坚持“让天下没有难做的生意”的使命，善于理解他人需求。",
        "史蒂夫·乔布斯（Steve Jobs）：苹果公司创始人，从车库创业，凭借对用户需求的深刻洞察和创新理念，重新定义了手机、电脑等多个行业。",
        "特蕾莎·梅里（Teresa Mayr）：奥地利知名女企业家，白手起家打造有机护肤品牌，秉持理想主义，用商业力量推动环保和女性创业。"
    ],
    "INTJ - 策划师": [
        "埃隆·马斯克（Elon Musk）：特斯拉/太空探索技术公司创始人，从PayPal起家，凭借超强的战略眼光和逻辑分析能力，跨界颠覆多个行业。",
        "拉里·佩奇（Larry Page）：谷歌创始人，车库创业打造全球最大搜索引擎，理性、创新，始终坚持用技术解决全球难题的战略目标。",
        "张一鸣：字节跳动创始人，白手起家打造抖音/今日头条，凭借极致的理性分析和长期规划，成为全球最年轻的亿万富豪之一。"
    ],
    "ISTP - 手艺人": [
        "理查德·布兰森（Richard Branson）：维珍集团创始人，白手起家打造跨行业商业帝国，动手能力强、灵活应变，喜欢挑战和探索新领域。",
        "雷军：小米科技创始人，从程序员起家，务实、善于解决实际问题，用“性价比”理念颠覆手机行业，打造生态链企业。",
        "马克·扎克伯格（Mark Zuckerberg）：Facebook创始人，从校园创业，注重实际效果、思维敏捷，快速迭代产品成为全球社交巨头。"
    ],
    "ISFP - 艺术家": [
        "华特·迪士尼（Walt Disney）：迪士尼创始人，白手起家打造童话帝国，富有创造力、热爱生活，用艺术和想象力影响全球几代人。",
        "可可·香奈儿（Coco Chanel）：香奈儿品牌创始人，从孤儿到时尚女王，用独特的审美和创造力重新定义女性时尚，成为时尚界传奇。",
        "村上隆：日本知名艺术家/企业家，将艺术与商业完美结合，白手起家打造艺术IP帝国，极具个性和创造力。"
    ],
    "INFP - 调停者": [
        "杰夫·贝佐斯（Jeff Bezos）：亚马逊创始人，从车库创业打造全球最大电商平台，理想主义、富有想象力，始终坚持“长期主义”和客户至上。",
        "J.K.罗琳（J.K. Rowling）：《哈利·波特》作者，从单亲妈妈到亿万富豪，用想象力创造魔法世界，凭借坚持和理想实现人生逆袭。",
        "韩寒：中国作家/企业家，从辍学青年到作家、赛车手、导演，坚持内心追求，用多元创作打造个人品牌，实现商业和理想的结合。"
    ],
    "INTP - 逻辑学家": [
        "比尔·盖茨（Bill Gates）：微软创始人，从车库创业打造软件帝国，理性、好奇、善于分析，用技术推动全球信息化发展，成为世界首富。",
        "林纳斯·托瓦兹（Linus Torvalds）：Linux系统创始人，白手起家打造开源操作系统，凭借超强的逻辑思维，影响全球软件行业发展。",
        "马化腾：腾讯创始人，从程序员起家，理性、低调，善于分析用户需求，打造微信/QQ等国民产品，成为中国互联网巨头。"
    ],
    "ESTP - 企业家": [
        "唐纳德·特朗普（Donald Trump）：特朗普集团创始人，白手起家打造房地产帝国，外向、务实、善于应变，极具商业冒险精神。",
        "布兰妮·斯皮尔斯（Britney Spears）：跨界企业家，从歌手起家，凭借外向的性格和商业敏感度，打造个人品牌帝国，成为亿万富豪。",
        "王思聪：普思资本创始人，凭借敏锐的商业嗅觉和务实的风格，在投资、电竞等领域快速布局，成为年轻一代企业家代表。"
    ],
    "ESFP - 表演者": [
        "奥普拉·温弗瑞（Oprah Winfrey）：脱口秀女王/企业家，从贫民窟黑人女孩起家，外向、热情，用口才和感染力打造媒体帝国，成为全球最有影响力的女性之一。",
        "李湘：中国知名主持人/企业家，从主持人跨界创业，外向、善于交际，在电商、投资等领域布局，实现商业成功。",
        "帕丽斯·希尔顿（Paris Hilton）：希尔顿集团继承人/企业家，凭借外向的性格和个人魅力，打造时尚、美妆等个人品牌，白手起家实现财富增值。"
    ],
    "ENFP - 活动家": [
        "理查德·布兰森（Richard Branson）：维珍集团联合代表，ENFP特质突出，外向、富有创造力，用热情激励团队，跨界打造多个成功品牌。",
        "马云：阿里巴巴联合代表，ENFP特质显著，善于激励他人，用梦想和热情凝聚团队，打造全球电商帝国。",
        "特雷弗·诺亚（Trevor Noah）：脱口秀演员/企业家，从南非贫民窟起家，外向、富有想象力，用幽默和正能量打造个人品牌，成为亿万富豪。"
    ],
    "ENTP - 辩论家": [
        "马斯克（Elon Musk）：联合代表，ENTP特质突出，机智、善于辩论，喜欢挑战传统，用创新思维颠覆航天、汽车等行业。",
        "彼得·蒂尔（Peter Thiel）：PayPal创始人，白手起家打造支付巨头，机智、富有思辨性，成为硅谷知名投资人和企业家。",
        "罗永浩：锤子科技/交个朋友创始人，白手起家，机智、幽默，善于辩论，在科技、直播电商领域持续创业，实现财富逆袭。"
    ],
    "ESTJ - 总经理": [
        "杰克·韦尔奇（Jack Welch）：通用电气前CEO，从普通员工做到全球顶级CEO，外向、务实、有领导力，注重效率和结果，被誉为“全球第一CEO”。",
        "任正非：华为创始人，白手起家打造全球通信巨头，外向、果断，极具领导力，用军事化管理带领华为走向世界。",
        "柳传志：联想创始人，从科研人员起家，外向、务实，有超强的企业管理能力，打造中国首个全球500强科技企业。"
    ],
    "ESFJ - 执政官": [
        "梅琳达·盖茨（Melinda Gates）：盖茨基金会联合创始人，注重公益和他人感受，外向、热情，用财富推动全球教育、医疗事业发展，极具领导力。",
        "董明珠：格力电器董事长，从销售员起家，外向、体贴员工，用严格的管理和优质的产品，打造格力空调帝国，成为中国女性企业家代表。",
        "杨澜：阳光媒体创始人，从主持人跨界创业，外向、善于交际，注重女性发展，打造媒体和公益平台，实现商业和社会价值。"
    ],
    "ENFJ - 教育家": [
        "马云：联合代表，ENFJ特质突出，善于激励和引导他人，用教育理念做企业，打造阿里巴巴“铁军”团队，成为全球知名企业家。",
        "俞敏洪：新东方创始人，白手起家打造教育帝国，外向、富有同理心，用教育改变无数人命运，疫情后跨界直播电商实现二次创业。",
        "托尼·罗宾斯（Tony Robbins）：全球知名励志导师/企业家，白手起家，善于激励他人，用演讲和课程打造个人品牌，成为亿万富豪。"
    ],
    "ENTJ - 指挥官": [
        "史蒂夫·鲍尔默（Steve Ballmer）：微软前CEO，从员工做到CEO，外向、果断，有超强的战略眼光和领导力，带领微软成为全球科技巨头。",
        "拉里·埃里森（Larry Ellison）：甲骨文创始人，白手起家打造数据库巨头，外向、自信，极具领导力，喜欢挑战和竞争，成为世界首富之一。",
        "王健林：万达集团创始人，白手起家打造房地产和文旅帝国，外向、果断，有超强的战略规划能力，成为中国前首富。"
    ]
}

# MBTI人格系统对话指令
def get_mbti_system_prompt(mbti_type):
    mbti_desc = {
        "ISTJ - 检查员": "你是ISTJ型人格（检查员），注重实际、稳重可靠、责任感强，做事有条理，喜欢按规则和传统行事，沟通风格直接、务实、注重细节。",
        "ISFJ - 守护者": "你是ISFJ型人格（守护者），富有同情心、乐于助人、有责任心，注重和谐，善于照顾他人感受，沟通风格温和、耐心、体贴。",
        "INFJ - 咨询师": "你是INFJ型人格（咨询师），富有洞察力、理想主义、有创造力，善于理解他人内心，沟通风格深刻、富有同理心、充满智慧。",
        "INTJ - 策划师": "你是INTJ型人格（策划师），理性、创新、有战略眼光，追求完美，善于分析和规划，沟通风格简洁、逻辑严密、直击核心。",
        "ISTP - 手艺人": "你是ISTP型人格（手艺人），务实、灵活、善于动手，喜欢探索和解决实际问题，沟通风格简洁、直接、注重实际效果。",
        "ISFP - 艺术家": "你是ISFP型人格（艺术家），敏感、温和、富有创造力，热爱生活和美好事物，沟通风格温柔、真诚、富有感染力。",
        "INFP - 调停者": "你是INFP型人格（调停者），理想主义、富有想象力、追求内心和谐，善于理解他人情感，沟通风格温柔、富有同理心、充满理想。",
        "INTP - 逻辑学家": "你是INTP型人格（逻辑学家），理性、好奇、善于分析，喜欢探索抽象概念，沟通风格理性、客观、富有逻辑性。",
        "ESTP - 企业家": "你是ESTP型人格（企业家），外向、务实、善于应变，喜欢冒险和挑战，沟通风格直接、自信、充满活力。",
        "ESFP - 表演者": "你是ESFP型人格（表演者），外向、热情、善于交际，喜欢享受生活，沟通风格活泼、热情、富有感染力。",
        "ENFP - 活动家": "你是ENFP型人格（活动家），外向、富有创造力、充满热情，善于激励他人，沟通风格活泼、富有想象力、充满正能量。",
        "ENTP - 辩论家": "你是ENTP型人格（辩论家），外向、机智、善于辩论，喜欢挑战和创新，沟通风格机智、幽默、富有思辨性。",
        "ESTJ - 总经理": "你是ESTJ型人格（总经理），外向、务实、有领导力，注重效率和结果，沟通风格直接、果断、富有权威性。",
        "ESFJ - 执政官": "你是ESFJ型人格（执政官），外向、热情、善于交际，注重和谐和他人感受，沟通风格热情、体贴、善于倾听。",
        "ENFJ - 教育家": "你是ENFJ型人格（教育家），外向、富有同理心、有领导力，善于激励和引导他人，沟通风格热情、富有感染力、充满智慧。",
        "ENTJ - 指挥官": "你是ENTJ型人格（指挥官），外向、果断、有战略眼光，善于领导和规划，沟通风格直接、自信、富有权威性。"
    }
    return mbti_desc.get(mbti_type, "你是一个专业的MBTI人格对话助手，能够精准模拟不同人格的沟通风格。")

# -------------------------------------------------------------
# --- 核心逻辑函数 ---
# -------------------------------------------------------------
def stream_gemini_response(prompt, model, max_retries=3):
    """Gemini流式回复函数，带429重试机制"""
    for attempt in range(max_retries):
        try:
            stream = model.generate_content(prompt, stream=True)
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
                    time.sleep(0.02)
            return
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    yield f"⚠️ Gemini调用失败 (429配额超限)：多次重试后仍失败。{error_str[:100]}..."
                    break
            else:
                yield f"⚠️ Gemini调用失败：{error_str[:100]}..."
                break

def analyze_user_mbti(user_desc, gemini_model):
    """【核心新增】快速分析用户MBTI人格，返回分析结果+对应人格类型"""
    analyze_prompt = f"""
    你是专业的MBTI人格分析师，根据用户的自我描述快速判断其MBTI人格类型，要求如下：
    1. 分析逻辑：结合用户的性格、行为、思维方式、沟通习惯等特征，匹配16型MBTI人格；
    2. 输出格式：先给出明确的MBTI人格类型（如INTJ - 策划师），再用200字以内简要分析判断依据，语言简洁、专业；
    3. 判断原则：精准匹配，不模棱两可，基于用户描述的核心特征分析，不添加无关内容。

    用户自我描述：{user_desc}
    """
    # 调用Gemini获取分析结果
    try:
        response = gemini_model.generate_content(analyze_prompt)
        response_text = response.text.strip()
        # 提取人格类型（适配输出格式，确保能匹配到MBTI_16_TYPES）
        for mbti_type in MBTI_16_TYPES:
            if mbti_type in response_text:
                return response_text, mbti_type
        # 若未匹配到，返回默认结果
        return f"暂无法精准判断你的MBTI人格，可补充更详细的自我描述后重试！\n\n用户描述：{user_desc}", MBTI_16_TYPES[0]
    except Exception as e:
        return f"⚠️ 人格分析失败：{str(e)[:100]}...", MBTI_16_TYPES[0]

# -------------------------------------------------------------
# --- 状态初始化 ---
# -------------------------------------------------------------
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
st.session_state["api_configured"] = bool(gemini_api_key)

# 初始化核心状态
if "selected_mbti" not in st.session_state:
    st.session_state["selected_mbti"] = MBTI_16_TYPES[0]
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！你可以选择分析自己的MBTI人格，或直接选择一种人格开始对话～"}]
if "user_mbti_analysis" not in st.session_state:
    st.session_state["user_mbti_analysis"] = ""  # 存储用户人格分析结果
if "analyzed_mbti_type" not in st.session_state:
    st.session_state["analyzed_mbti_type"] = ""   # 存储分析出的用户人格类型

# 初始化Gemini模型（通用模型，用于人格分析+对话）
@st.cache_resource
def initialize_gemini_model():
    if not gemini_api_key: return None
    # 通用系统指令，兼顾人格分析和对话
    system_prompt = """
    你是专业的MBTI人格分析与对话助手，既能精准分析用户的MBTI人格类型，也能完美模拟不同MBTI人格的沟通风格，
    分析时专业、精准，对话时贴合对应人格的核心特质，语言自然、符合人格特征。
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt
    )
gemini_model = initialize_gemini_model()

# 初始化对话专用模型（根据选择的MBTI动态调整）
def init_chat_model(mbti_type):
    if not gemini_api_key: return None
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=get_mbti_system_prompt(mbti_type)
    )

# -------------------------------------------------------------
# --- 页面渲染 ---
# -------------------------------------------------------------
# 顶部导航
st.markdown("""
<div class="nav-bar">
    <div class="logo-text">🧠 MBTI人格分析助手</div>
    <div class="nav-tag">快速分析 + 富豪案例 + 人格对话 | Powered by Gemini</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

# 标题区域
st.markdown("""
<div class="hero-section">
    <h1 class="page-title">MBTI 16型人格分析与对话</h1>
    <div class="subtitle">快速判断你的人格类型 + 查看同人格白手起家亿万富豪案例 + 与任意人格对话</div>
</div>
""", unsafe_allow_html=True)

# 【核心新增】1. 快速分析用户MBTI人格卡片
st.markdown('<div class="func-card">', unsafe_allow_html=True)
st.markdown('<div class="func-card-title">📊 快速分析你的MBTI人格</div>', unsafe_allow_html=True)
user_self_desc = st.text_area(
    "请简要描述你的性格、行为习惯、思维方式或沟通特点（例：内向、喜欢思考、做事有条理、注重逻辑）",
    placeholder="输入你的自我描述，越详细分析越精准～",
    key="user_mbti_desc",
    height=100
)
col_analyze, col_reset_analyze = st.columns([1, 4])
with col_analyze:
    if st.button("立即分析", use_container_width=True) and user_self_desc and gemini_model:
        with st.spinner("正在分析你的MBTI人格..."):
            analysis_result, mbti_type = analyze_user_mbti(user_self_desc, gemini_model)
            st.session_state["user_mbti_analysis"] = analysis_result
            st.session_state["analyzed_mbti_type"] = mbti_type
with col_reset_analyze:
    if st.button("清空描述", use_container_width=True, kind="secondary"):
        st.session_state["user_mbti_analysis"] = ""
        st.session_state["analyzed_mbti_type"] = ""
        st.rerun()
# 展示分析结果
if st.session_state["user_mbti_analysis"]:
    st.markdown("### 你的MBTI人格分析结果")
    st.info(st.session_state["user_mbti_analysis"])
st.markdown('</div>', unsafe_allow_html=True)

# 【核心新增】2. 展示对应人格白手起家富豪案例（分析结果/选择的人格）
st.markdown('<div class="func-card">', unsafe_allow_html=True)
# 优先展示分析出的人格案例，若无则展示选择的人格案例
target_mbti = st.session_state["analyzed_mbti_type"] if st.session_state["analyzed_mbti_type"] else st.session_state["selected_mbti"]
st.markdown(f'<div class="func-card-title">💴 {target_mbti} - 白手起家亿万富豪案例（3个）</div>', unsafe_allow_html=True)
billionaires = MBTI_BILLIONAIRES.get(target_mbti, ["暂无该人格的富豪案例"])
for idx, case in enumerate(billionaires, 1):
    st.markdown(f"{idx}. {case}")
st.markdown('</div>', unsafe_allow_html=True)

# 3. MBTI人格选择卡片（保留原有功能，优化样式）
st.markdown('<div class="func-card">', unsafe_allow_html=True)
st.markdown('<div class="func-card-title">💬 选择MBTI人格开始对话</div>', unsafe_allow_html=True)
selected_mbti = st.selectbox(
    "选择任意人格类型，即可模拟该人格的沟通风格进行对话",
    MBTI_16_TYPES,
    index=MBTI_16_TYPES.index(st.session_state["selected_mbti"]),
    key="mbti_selector"
)
# 切换人格重置对话
if selected_mbti != st.session_state["selected_mbti"]:
    st.session_state["selected_mbti"] = selected_mbti
    st.session_state.messages = [{"role": "assistant", "content": f"您好！我现在是{selected_mbti}人格，有什么想聊的吗？"}]
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 历史消息渲染
st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "assistant"
    avatar = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    content_html = markdown_to_html(msg["content"])
    st.markdown(f"""
    <div class="chat-row {role_class}">
        <div class="chat-avatar">{avatar}</div>
        <div class="chat-bubble">{content_html}</div>
    </div>
    """, unsafe_allow_html=True)

# 对话输入处理
chat_input_text = st.chat_input(f"和{st.session_state['selected_mbti']}聊聊天吧...")
user_input = chat_input_text

if user_input and st.session_state.get("api_configured", False) and gemini_model:
    # 显示用户消息
    st.markdown(f"""
    <div class="chat-row user">
        <div class="chat-avatar">{USER_ICON}</div>
        <div class="chat-bubble">{user_input}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 初始化对话专用模型
    chat_model = init_chat_model(st.session_state["selected_mbti"])
    # 占位容器
    st.markdown('<div class="model-section-title">🔍 Gemini 人格回复</div>', unsafe_allow_html=True)
    gemini_placeholder = st.empty()

    # 生成并展示流式回复
    gemini_full = ""
    with st.spinner(f"正在以{st.session_state['selected_mbti']}人格回复..."):
        for chunk in stream_gemini_response(user_input, chat_model):
            gemini_full += chunk
            gemini_html = markdown_to_html(clean_extra_newlines(gemini_full))
            gemini_placeholder.markdown(f"""
            <div class="model-card">
                <div class="model-card-header gemini-header">{GEMINI_ICON} Gemini Flash ({st.session_state['selected_mbti']})</div>
                <div class="model-card-content">{gemini_html}<span class="blinking-cursor">|</span></div>
            </div>
            """, unsafe_allow_html=True)
    # 完成态去除光标
    gemini_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">{GEMINI_ICON} Gemini Flash ({st.session_state['selected_mbti']})</div>
        <div class="model-card-content">{markdown_to_html(clean_extra_newlines(gemini_full))}</div>
    </div>
    """, unsafe_allow_html=True)

    # 保存对话历史
    st.session_state.messages.append({"role": "assistant", "content": gemini_full})

# 重置对话按钮
if st.button('🔄 重置当前对话', key="reset_btn", help="清空所有对话历史", use_container_width=True):
    st.session_state.messages = [{"role": "assistant", "content": f"您好！我现在是{st.session_state['selected_mbti']}人格，有什么想聊的吗？"}]
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 访问统计模块 (保留原有功能) ---
# -------------------------------------------------------------
DB_FILE = "visit_stats.db"
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_traffic (date TEXT PRIMARY KEY, pv_count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitors (visitor_id TEXT PRIMARY KEY, first_visit_date TEXT)''')
    c.execute("PRAGMA table_info(visitors)")
    columns = [info[1] for info in c.fetchall()]
    if "last_visit_date" not in columns:
        try:
            c.execute("ALTER TABLE visitors ADD COLUMN last_visit_date TEXT")
            c.execute("UPDATE visitors SET last_visit_date = first_visit_date WHERE last_visit_date IS NULL")
        except Exception as e:
            print(f"数据库升级失败: {e}")
    conn.commit()
    conn.close()

def get_visitor_id():
    if "visitor_id" not in st.session_state:
        st.session_state["visitor_id"] = str(uuid.uuid4())
    return st.session_state["visitor_id"]

def track_and_get_stats():
    init_db()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    today_str = datetime.datetime.utcnow().date().isoformat()
    visitor_id = get_visitor_id()
    if "has_counted" not in st.session_state:
        try:
            c.execute("INSERT OR IGNORE INTO daily_traffic (date, pv_count) VALUES (?, 0)", (today_str,))
            c.execute("UPDATE daily_traffic SET pv_count = pv_count + 1 WHERE date=?", (today_str,))
            c.execute("SELECT visitor_id FROM visitors WHERE visitor_id=?", (visitor_id,))
            exists = c.fetchone()
            if exists:
                c.execute("UPDATE visitors SET last_visit_date=? WHERE visitor_id=?", (today_str, visitor_id))
            else:
                c.execute("INSERT INTO visitors (visitor_id, first_visit_date, last_visit_date) VALUES (?, ?, ?)", (visitor_id, today_str, today_str))
            conn.commit()
            st.session_state["has_counted"] = True
        except Exception as e:
            st.error(f"数据库写入错误: {e}")
    c.execute("SELECT COUNT(*) FROM visitors WHERE last_visit_date=?", (today_str,))
    today_uv = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM visitors")
    total_uv = c.fetchone()[0]
    c.execute("SELECT pv_count FROM daily_traffic WHERE date=?", (today_str,))
    res_pv = c.fetchone()
    today_pv = res_pv[0] if res_pv else 0
    conn.close()
    return today_uv, total_uv, today_pv

# 展示统计数据
try:
    today_uv, total_uv, today_pv = track_and_get_stats()
except Exception as e:
    today_uv, total_uv, today_pv = 0, 0, 0

st.markdown(f"""
<div class="metric-container">
    <div class="metric-box">
        <div class="metric-sub">今日 UV: {today_uv} 访客数</div>
    </div>
    <div class="metric-box" style="border-left: 1px solid #dee2e6; border-right: 1px solid #dee2e6; padding: 0 20px;">
        <div class="metric-sub">历史总 UV: {total_uv} 总独立访客</div>
    </div>
    <div class="metric-box">
        <div class="metric-sub">今日 PV: {today_pv} 访问量</div>
    </div>
</div>
""", unsafe_allow_html=True)

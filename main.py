"""
塔罗牌占卜网站 - FastAPI 后端
"""
import os
import random
import json
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

# 加载环境变量
load_dotenv()

app = FastAPI(title="塔罗牌占卜", version="1.0.0")

# ==================== 频率限制 ====================
rate_limit_store = {}  # ip -> last_request_time
RATE_LIMIT_SECONDS = 10  # 每个IP每10秒只能请求一次

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==================== 图片资源 ====================

IMAGE_BASE = "https://raw.githubusercontent.com/lalesleon13-hash/Tarot/main"

# ==================== 塔罗牌数据 ====================

MAJOR_ARCANA = [
    {"id": 0, "name": "愚者", "english": "The Fool", "image": f"{IMAGE_BASE}/RWS_Tarot_00_Fool.jpg", "keywords": ["新开始", "冒险", "天真", "自由"]},
    {"id": 1, "name": "魔术师", "english": "The Magician", "image": f"{IMAGE_BASE}/RWS_Tarot_01_Magician.jpg", "keywords": ["创造力", "技能", "意志力", "自信"]},
    {"id": 2, "name": "女祭司", "english": "The High Priestess", "image": f"{IMAGE_BASE}/RWS_Tarot_02_High_Priestess.jpg", "keywords": ["直觉", "潜意识", "神秘", "内在智慧"]},
    {"id": 3, "name": "女皇", "english": "The Empress", "image": f"{IMAGE_BASE}/RWS_Tarot_03_Empress.jpg", "keywords": ["丰收", "母性", "自然", "富足"]},
    {"id": 4, "name": "皇帝", "english": "The Emperor", "image": f"{IMAGE_BASE}/RWS_Tarot_04_Emperor.jpg", "keywords": ["权威", "结构", "控制", "稳定"]},
    {"id": 5, "name": "教皇", "english": "The Hierophant", "image": f"{IMAGE_BASE}/RWS_Tarot_05_Hierophant.jpg", "keywords": ["传统", "信仰", "教育", "精神指引"]},
    {"id": 6, "name": "恋人", "english": "The Lovers", "image": f"{IMAGE_BASE}/RWS_Tarot_06_Lovers.jpg", "keywords": ["爱情", "选择", "和谐", "价值观"]},
    {"id": 7, "name": "战车", "english": "The Chariot", "image": f"{IMAGE_BASE}/RWS_Tarot_07_Chariot.jpg", "keywords": ["意志力", "胜利", "决心", "自律"]},
    {"id": 8, "name": "力量", "english": "Strength", "image": f"{IMAGE_BASE}/RWS_Tarot_08_Strength.jpg", "keywords": ["勇气", "耐心", "内在力量", "慈悲"]},
    {"id": 9, "name": "隐士", "english": "The Hermit", "image": f"{IMAGE_BASE}/RWS_Tarot_09_Hermit.jpg", "keywords": ["内省", "孤独", "智慧", "寻求真理"]},
    {"id": 10, "name": "命运之轮", "english": "Wheel of Fortune", "image": f"{IMAGE_BASE}/RWS_Tarot_10_Wheel_of_Fortune.jpg", "keywords": ["命运", "转折点", "机遇", "变化"]},
    {"id": 11, "name": "正义", "english": "Justice", "image": f"{IMAGE_BASE}/RWS_Tarot_11_Justice.jpg", "keywords": ["公平", "真理", "因果", "法律"]},
    {"id": 12, "name": "倒吊人", "english": "The Hanged Man", "image": f"{IMAGE_BASE}/RWS_Tarot_12_Hanged_Man.jpg", "keywords": ["牺牲", "新视角", "放下", "等待"]},
    {"id": 13, "name": "死神", "english": "Death", "image": f"{IMAGE_BASE}/RWS_Tarot_13_Death.jpg", "keywords": ["结束", "转变", "新生", "放下过去"]},
    {"id": 14, "name": "节制", "english": "Temperance", "image": f"{IMAGE_BASE}/RWS_Tarot_14_Temperance.jpg", "keywords": ["平衡", "耐心", "适度", "和谐"]},
    {"id": 15, "name": "恶魔", "english": "The Devil", "image": f"{IMAGE_BASE}/RWS_Tarot_15_Devil.jpg", "keywords": ["束缚", "诱惑", "物欲", "成瘾"]},
    {"id": 16, "name": "塔", "english": "The Tower", "image": f"{IMAGE_BASE}/RWS_Tarot_16_Tower.jpg", "keywords": ["突变", "毁灭", "觉醒", "真相"]},
    {"id": 17, "name": "星星", "english": "The Star", "image": f"{IMAGE_BASE}/RWS_Tarot_17_Star.jpg", "keywords": ["希望", "灵感", "宁静", "信心"]},
    {"id": 18, "name": "月亮", "english": "The Moon", "image": f"{IMAGE_BASE}/RWS_Tarot_18_Moon.jpg", "keywords": ["幻觉", "恐惧", "潜意识", "迷惑"]},
    {"id": 19, "name": "太阳", "english": "The Sun", "image": f"{IMAGE_BASE}/RWS_Tarot_19_Sun.jpg", "keywords": ["成功", "快乐", "活力", "乐观"]},
    {"id": 20, "name": "审判", "english": "Judgement", "image": f"{IMAGE_BASE}/RWS_Tarot_20_Judgement.jpg", "keywords": ["觉醒", "重生", "反思", "召唤"]},
    {"id": 21, "name": "世界", "english": "The World", "image": f"{IMAGE_BASE}/RWS_Tarot_21_World.jpg", "keywords": ["完成", "整合", "成就", "圆满"]},
]

# 四个花色的图片前缀
SUIT_IMAGE_MAP = {
    "权杖": "Wands",
    "圣杯": "Cups",
    "宝剑": "Swords",
    "钱币": "Pents",
}

# 宫廷牌名称映射
COURT_CARD_NAMES = ["侍从", "骑士", "王后", "国王"]
COURT_CARD_ENGLISH = ["Page", "Knight", "Queen", "King"]

def build_minor_arcana():
    """构建小阿卡纳牌组"""
    cards = []
    card_id = 22  # 从22开始，0-21是大阿卡纳

    keywords_map = {
        "权杖": {
            "王牌": ["新开始", "灵感", "创造力"],
            "二": ["计划", "决策", "未来规划"],
            "三": ["进展", "远见", "机遇"],
            "四": ["庆祝", "和谐", "家庭"],
            "五": ["冲突", "竞争", "挑战"],
            "六": ["胜利", "认可", "自信"],
            "七": ["防御", "坚持", "挑战"],
            "八": ["快速行动", "消息", "进展"],
            "九": ["韧性", "坚持", "毅力"],
            "十": ["负担", "责任", "压力"],
            "侍从": ["热情", "探索", "新消息"],
            "骑士": ["冒险", "热情", "行动"],
            "王后": ["自信", "独立", "热情"],
            "国王": ["领导力", "远见", "魅力"],
        },
        "圣杯": {
            "王牌": ["新感情", "直觉", "精神满足"],
            "二": ["伙伴关系", "和谐", "连接"],
            "三": ["庆祝", "友谊", "社交"],
            "四": ["冷漠", "冥想", "不满"],
            "五": ["悔恨", "失落", "悲伤"],
            "六": ["怀旧", "纯真", "回忆"],
            "七": ["幻想", "选择", "幻想"],
            "八": ["离开", "寻找", "放弃"],
            "九": ["满足", "愿望成真", "满足"],
            "十": ["幸福", "和谐", "家庭"],
            "侍从": ["直觉", "创意", "新感情"],
            "骑士": ["浪漫", "魅力", "理想主义"],
            "王后": ["同理心", "直觉", "情感智慧"],
            "国王": ["情感平衡", "智慧", "外交"],
        },
        "宝剑": {
            "王牌": ["新想法", "清晰", "突破"],
            "二": ["决定", "僵局", "逃避"],
            "三": ["心碎", "悲伤", "分离"],
            "四": ["休息", "恢复", "冥想"],
            "五": ["冲突", "失败", "争执"],
            "六": ["过渡", "离开", "平静"],
            "七": ["欺骗", "策略", "逃避"],
            "八": ["限制", "束缚", "无助"],
            "九": ["焦虑", "恐惧", "噩梦"],
            "十": ["结束", "背叛", "痛苦"],
            "侍从": ["好奇心", "警觉", "新想法"],
            "骑士": ["行动迅速", "决心", "冲动"],
            "王后": ["独立", "清晰", "直率"],
            "国王": ["权威", "智慧", "公正"],
        },
        "钱币": {
            "王牌": ["新机会", "财富", "稳定"],
            "二": ["平衡", "适应", "多重任务"],
            "三": ["合作", "技能", "团队"],
            "四": ["安全", "保守", "控制"],
            "五": ["困难", "贫穷", "孤立"],
            "六": ["慷慨", "分享", "繁荣"],
            "七": ["耐心", "等待", "长期投资"],
            "八": ["勤奋", "技能", "专注"],
            "九": ["富足", "独立", "成功"],
            "十": ["财富", "家庭", "传承"],
            "侍从": ["学习", "新技能", "机会"],
            "骑士": ["勤奋", "可靠", "耐心"],
            "王后": ["丰盛", "实际", "关怀"],
            "国王": ["成功", "安全", "领导"],
        },
    }

    # 花色英文名
    suit_english = {
        "权杖": "Wands",
        "圣杯": "Cups",
        "宝剑": "Swords",
        "钱币": "Pents",
    }

    for suit_name, suit_prefix in SUIT_IMAGE_MAP.items():
        # 数字牌 (Ace-10) - 图片编号 01-10
        numbers = ["王牌", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
        for i, num in enumerate(numbers):
            img_num = str(i + 1).zfill(2)
            cards.append({
                "id": card_id,
                "name": f"{suit_name}{num}",
                "english": f"{['Ace','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten'][i]} of {suit_english[suit_name]}",
                "image": f"{IMAGE_BASE}/{suit_prefix}{img_num}.jpg",
                "keywords": keywords_map[suit_name][num],
                "suit": suit_name,
            })
            card_id += 1

        # 宫廷牌 - 图片编号 11-14
        for j, court in enumerate(COURT_CARD_NAMES):
            img_num = str(j + 11).zfill(2)
            cards.append({
                "id": card_id,
                "name": f"{suit_name}{court}",
                "english": f"{COURT_CARD_ENGLISH[j]} of {suit_english[suit_name]}",
                "image": f"{IMAGE_BASE}/{suit_prefix}{img_num}.jpg",
                "keywords": keywords_map[suit_name][court],
                "suit": suit_name,
            })
            card_id += 1

    return cards

MINOR_ARCANA = build_minor_arcana()
ALL_CARDS = MAJOR_ARCANA + MINOR_ARCANA

# ==================== 数据模型 ====================

class ReadingRequest(BaseModel):
    cosmic_energy: int

class CardReading(BaseModel):
    card_id: int
    card_name: str
    card_english: str
    image: str
    is_reversed: bool
    keywords: list[str]

class ReadingResponse(BaseModel):
    cosmic_energy: int
    cards: list[CardReading]
    interpretation: str

# ==================== 路由 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回主页"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/cards")
async def get_all_cards():
    """获取所有塔罗牌"""
    return {"cards": ALL_CARDS}

@app.post("/api/reading", response_model=ReadingResponse)
async def create_reading(request: ReadingRequest, request_obj: Request):
    """创建塔罗牌占卜"""
    # 频率限制
    client_ip = request_obj.client.host
    current_time = time.time()
    if client_ip in rate_limit_store:
        elapsed = current_time - rate_limit_store[client_ip]
        if elapsed < RATE_LIMIT_SECONDS:
            raise HTTPException(status_code=429, detail=f"请求太频繁，请{int(RATE_LIMIT_SECONDS - elapsed)}秒后再试")
    rate_limit_store[client_ip] = current_time
    cosmic_energy = request.cosmic_energy

    # 使用宇宙能量计算三张牌
    seed = cosmic_energy % 78
    card_indices = [
        seed,
        (seed + cosmic_energy % 22 + 7) % 78,
        (seed + cosmic_energy % 56 + 13) % 78,
    ]

    # 确保没有重复
    seen = set()
    unique_indices = []
    for idx in card_indices:
        while idx in seen:
            idx = (idx + 1) % 78
        seen.add(idx)
        unique_indices.append(idx)

    # 获取牌并决定正逆位
    drawn_cards = []
    for i, idx in enumerate(unique_indices):
        card = ALL_CARDS[idx]
        # 使用宇宙能量的各个位来决定正逆位
        is_reversed = (cosmic_energy // (10 ** i)) % 2 == 1
        drawn_cards.append(CardReading(
            card_id=card["id"],
            card_name=card["name"],
            card_english=card["english"],
            image=card["image"],
            is_reversed=is_reversed,
            keywords=card["keywords"],
        ))

    # 调用 AI 生成解读
    interpretation = await generate_interpretation(cosmic_energy, drawn_cards)

    return ReadingResponse(
        cosmic_energy=cosmic_energy,
        cards=drawn_cards,
        interpretation=interpretation,
    )

@app.websocket("/ws/reading")
async def websocket_reading(websocket: WebSocket):
    """WebSocket实时占卜"""
    await websocket.accept()

    try:
        # 频率限制
        client_ip = websocket.client.host
        current_time = time.time()
        if client_ip in rate_limit_store:
            elapsed = current_time - rate_limit_store[client_ip]
            if elapsed < RATE_LIMIT_SECONDS:
                await websocket.send_json({"type": "error", "message": f"请求太频繁，请{int(RATE_LIMIT_SECONDS - elapsed)}秒后再试"})
                await websocket.close()
                return
        rate_limit_store[client_ip] = current_time
        # 接收宇宙能量
        data = await websocket.receive_text()
        request = json.loads(data)
        cosmic_energy = request.get("cosmic_energy", 0)

        # 生成牌
        seed = cosmic_energy % 78
        card_indices = [
            seed,
            (seed + cosmic_energy % 22 + 7) % 78,
            (seed + cosmic_energy % 56 + 13) % 78,
        ]

        seen = set()
        unique_indices = []
        for idx in card_indices:
            while idx in seen:
                idx = (idx + 1) % 78
            seen.add(idx)
            unique_indices.append(idx)

        drawn_cards = []
        for i, idx in enumerate(unique_indices):
            card = ALL_CARDS[idx]
            is_reversed = (cosmic_energy // (10 ** i)) % 2 == 1
            drawn_cards.append(CardReading(
                card_id=card["id"],
                card_name=card["name"],
                card_english=card["english"],
                image=card["image"],
                is_reversed=is_reversed,
                keywords=card["keywords"],
            ))

        # 先发送牌的数据
        cards_data = [card.model_dump() for card in drawn_cards]
        await websocket.send_json({"type": "cards", "cards": cards_data})

        # 流式生成解读
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("MODEL_NAME", "deepseek-chat")

        if not api_key or api_key == "your_deepseek_api_key_here":
            # 本地生成
            interpretation = generate_local_interpretation(cosmic_energy, drawn_cards)
            await websocket.send_json({"type": "chunk", "content": interpretation})
        else:
            # 流式调用LLM
            await stream_interpretation(websocket, cosmic_energy, drawn_cards, api_key, base_url, model)

        await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass


async def stream_interpretation(
    websocket: WebSocket,
    cosmic_energy: int,
    cards: list[CardReading],
    api_key: str,
    base_url: str,
    model: str
):
    """流式生成塔罗牌解读"""
    client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    cards_desc = []
    for i, card in enumerate(cards):
        position = ["过去", "现在", "未来"][i]
        orientation = "逆位" if card.is_reversed else "正位"
        cards_desc.append(f"{position}位置：{card.card_name}（{card.card_english}）{orientation}，关键词：{', '.join(card.keywords)}")

    prompt = f"""你是一位神秘而富有智慧的塔罗牌占卜师。请根据以下三张牌为求问者提供一段富有诗意和启发性的解读。

宇宙能量：{cosmic_energy}

抽取的三张牌：
{chr(10).join(cards_desc)}

要求：
1. 用温柔、神秘的语气
2. 结合三张牌的位置关系（过去、现在、未来）进行连贯解读
3. 提供积极正面的建议和启发
4. 适当加入一些诗意的表达
5. 长度控制在200-300字
6. 这是娱乐性质的占卜，请在结尾温馨提醒

请开始你的解读："""

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位来自星空的塔罗牌占卜师，拥有千年的智慧。你用诗意而温暖的语言为人们解读命运的密码。记住，这只是一个轻松愉快的娱乐占卜，不是真正的预测未来。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                await websocket.send_json({"type": "chunk", "content": content})

    except Exception as e:
        print(f"流式生成失败: {e}")
        # 回退到本地生成
        interpretation = generate_local_interpretation(cosmic_energy, cards)
        await websocket.send_json({"type": "chunk", "content": interpretation})


async def generate_interpretation(cosmic_energy: int, cards: list[CardReading]) -> str:
    """使用 OpenAI 兼容 API 生成塔罗牌解读"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("MODEL_NAME", "deepseek-chat")

    # 如果没有配置 API key，使用本地生成的简单解读
    if not api_key or api_key == "your_deepseek_api_key_here":
        return generate_local_interpretation(cosmic_energy, cards)

    try:
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        # 构建提示词
        cards_desc = []
        for i, card in enumerate(cards):
            position = ["过去", "现在", "未来"][i]
            orientation = "逆位" if card.is_reversed else "正位"
            cards_desc.append(f"{position}位置：{card.card_name}（{card.card_english}）{orientation}，关键词：{', '.join(card.keywords)}")

        prompt = f"""你是一位神秘而富有智慧的塔罗牌占卜师。请根据以下三张牌为求问者提供一段富有诗意和启发性的解读。

宇宙能量：{cosmic_energy}

抽取的三张牌：
{chr(10).join(cards_desc)}

要求：
1. 用温柔、神秘的语气
2. 结合三张牌的位置关系（过去、现在、未来）进行连贯解读
3. 提供积极正面的建议和启发
4. 适当加入一些诗意的表达
5. 长度控制在200-300字
6. 这是娱乐性质的占卜，请在结尾温馨提醒

请开始你的解读："""

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位来自星空的塔罗牌占卜师，拥有千年的智慧。你用诗意而温暖的语言为人们解读命运的密码。记住，这只是一个轻松愉快的娱乐占卜，不是真正的预测未来。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500,
        )

        return response.choices[0].message.content

    except Exception as e:
        # 如果 API 调用失败，使用本地解读
        print(f"API调用失败: {e}")
        return generate_local_interpretation(cosmic_energy, cards)

def generate_local_interpretation(cosmic_energy: int, cards: list[CardReading]) -> str:
    """本地生成简单解读（当 API 不可用时）"""
    positions = ["过去", "现在", "未来"]

    intro = f"宇宙能量 {cosmic_energy} 已为你揭示命运的面纱...\n\n"

    readings = []
    for i, card in enumerate(cards):
        orientation = "逆位" if card.is_reversed else "正位"
        keyword = random.choice(card.keywords)
        readings.append(f"【{positions[i]}】：{card.card_name}（{orientation}）")
        readings.append(f"   这张牌带来「{keyword}」的能量。")
        readings.append("")

    closing = "亲爱的求问者，这三张牌编织出一段独特的命运之歌。记住，塔罗牌是指引而非定论，真正的力量始终在你心中。这次占卜仅供娱乐放松，愿你带着微笑继续前行。"

    return intro + "\n".join(readings) + "\n" + closing

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

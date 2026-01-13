"""
Strategy Pack Service.

Generates comprehensive strategy packs for SEO content creation.
Combines TF-IDF analysis, LLM intelligence, and competitor insights.
"""

import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.services.tfidf_service import tfidf_service
from app.services.llm_service import llm_service


class LsiKeyword(BaseModel):
    """LSI keyword with metadata."""
    term: str
    weight: float
    essential: bool = False
    source: str = "tfidf"


class SuggestedIntent(BaseModel):
    """Suggested search intent with confidence."""
    value: str
    label: str
    description: str
    confidence: float


class StrategyPack(BaseModel):
    """Complete strategy pack for content creation."""
    keyword: str
    market: str
    ai_detected_intent: str
    suggested_intents: List[SuggestedIntent]
    suggested_tones: List[str]
    suggested_titles: List[str]
    lsi_keywords: List[LsiKeyword]
    eeat_tips: List[str]
    competitor_insights: Optional[Dict[str, Any]] = None


# Intent definitions
INTENT_OPTIONS = [
    {
        "value": "informational",
        "label": "📚 資訊型",
        "description": "教學、指南或百科。適合解決疑惑、分享知識。"
    },
    {
        "value": "commercial",
        "label": "💰 商業型",
        "description": "產品評測或對比。適合購物建議、決策參考。"
    },
    {
        "value": "transactional",
        "label": "🛒 交易型",
        "description": "促成購買或服務預約。目標是直接轉單。"
    },
    {
        "value": "navigational",
        "label": "🗺️ 導航型",
        "description": "指引路徑或登入入口。適合品牌官網或地點導引。"
    }
]

# Tone options
TONE_OPTIONS = [
    "專業教育風",
    "新手友善型",
    "權威評論風",
    "強烈號召風",
    "親切對話風",
    "簡潔指令風"
]


class StrategyService:
    """
    Strategy Pack generation service.
    
    Combines multiple data sources to generate comprehensive
    content strategy recommendations.
    """
    
    def __init__(self):
        self._llm = llm_service
        self._tfidf = tfidf_service
    
    async def generate_strategy_pack(
        self,
        keyword: str,
        market: str = "tw",
        tfidf_analysis: Optional[Dict[str, Any]] = None,
        competitor_data: Optional[List[Dict[str, Any]]] = None,
        intent: Optional[str] = None,
        tone: Optional[str] = None,
        regenerate_titles: bool = False,
    ) -> StrategyPack:
        """
        Generate a complete strategy pack.
        
        Args:
            keyword: Target keyword
            market: Target market (tw, us, etc.)
            tfidf_analysis: Pre-computed TF-IDF analysis (from research job)
            competitor_data: Competitor data for context
            intent: User-specified intent (overrides AI detection)
            tone: User-specified tone
            regenerate_titles: If True, generate new titles based on intent/tone
            
        Returns:
            Complete StrategyPack with all recommendations
        """
        # 1. Build LSI keywords from TF-IDF
        lsi_keywords = self._build_lsi_keywords(tfidf_analysis, keyword)
        
        # 2. Detect intent (or use provided)
        detected_intent = intent or await self._detect_intent(keyword, competitor_data)
        
        # 3. Build suggested intents with confidence
        suggested_intents = self._build_suggested_intents(detected_intent)
        
        # 4. Generate titles
        selected_intent = intent or detected_intent
        selected_tone = tone or "專業教育風"
        titles = await self._generate_titles(keyword, selected_intent, selected_tone)
        
        # 5. Generate E-E-A-T tips
        eeat_tips = self._generate_eeat_tips(keyword, selected_intent, competitor_data)
        
        # 6. Build competitor insights
        competitor_insights = None
        if competitor_data:
            competitor_insights = {
                "count": len(competitor_data),
                "avg_word_count": sum(c.get("word_count", 0) for c in competitor_data) // max(len(competitor_data), 1),
            }
        
        return StrategyPack(
            keyword=keyword,
            market=market,
            ai_detected_intent=detected_intent,
            suggested_intents=suggested_intents,
            suggested_tones=TONE_OPTIONS,
            suggested_titles=titles,
            lsi_keywords=lsi_keywords,
            eeat_tips=eeat_tips,
            competitor_insights=competitor_insights,
        )
    
    def _build_lsi_keywords(
        self,
        tfidf_analysis: Optional[Dict[str, Any]],
        keyword: str
    ) -> List[LsiKeyword]:
        """Build LSI keyword list from TF-IDF analysis."""
        lsi_list: List[LsiKeyword] = []
        
        if not tfidf_analysis:
            # Return empty list if no analysis available
            return lsi_list
        
        # Get suggested keywords (high-score)
        suggested = tfidf_analysis.get("suggested_keywords", [])
        for idx, kw in enumerate(suggested[:5]):
            lsi_list.append(LsiKeyword(
                term=kw.get("term", ""),
                weight=kw.get("score", 0.5),
                essential=idx < 3,  # Top 3 are essential
                source="suggested"
            ))
        
        # Get keyword categories
        categories = tfidf_analysis.get("keyword_categories", {})
        
        # Semantic related
        semantic = categories.get("semantic_related", [])
        for kw in semantic[:3]:
            term = kw.get("term", "")
            if term and not any(l.term == term for l in lsi_list):
                lsi_list.append(LsiKeyword(
                    term=term,
                    weight=kw.get("score", 0.4),
                    essential=False,
                    source="semantic"
                ))
        
        # Long tail
        long_tail = categories.get("long_tail", [])
        for kw in long_tail[:2]:
            term = kw.get("term", "")
            if term and not any(l.term == term for l in lsi_list):
                lsi_list.append(LsiKeyword(
                    term=term,
                    weight=kw.get("score", 0.3),
                    essential=False,
                    source="long_tail"
                ))
        
        return lsi_list
    
    async def _detect_intent(
        self,
        keyword: str,
        competitor_data: Optional[List[Dict[str, Any]]]
    ) -> str:
        """
        Detect search intent using LLM.
        
        Falls back to 'informational' if detection fails.
        """
        try:
            # Simple heuristic-based detection (can be enhanced with LLM later)
            keyword_lower = keyword.lower()
            
            # Transaction signals
            if any(word in keyword_lower for word in ["買", "購買", "訂購", "價格", "費用", "優惠", "折扣"]):
                return "transactional"
            
            # Commercial signals
            if any(word in keyword_lower for word in ["推薦", "評價", "比較", "最好", "排名", "top"]):
                return "commercial"
            
            # Navigational signals
            if any(word in keyword_lower for word in ["官網", "登入", "網址", "怎麼去"]):
                return "navigational"
            
            # Default to informational
            return "informational"
            
        except Exception:
            return "informational"
    
    def _build_suggested_intents(self, detected_intent: str) -> List[SuggestedIntent]:
        """Build suggested intents list with confidence scores."""
        result = []
        
        for intent in INTENT_OPTIONS:
            confidence = 0.85 if intent["value"] == detected_intent else 0.3
            result.append(SuggestedIntent(
                value=intent["value"],
                label=intent["label"],
                description=intent["description"],
                confidence=confidence
            ))
        
        # Sort by confidence (detected first)
        result.sort(key=lambda x: x.confidence, reverse=True)
        return result
    
    async def _generate_titles(
        self,
        keyword: str,
        intent: str,
        tone: str
    ) -> List[str]:
        """
        Generate title suggestions based on intent and tone.
        
        Uses template-based generation for MVP.
        Can be enhanced with LLM-based generation.
        """
        titles = []
        
        if intent == "commercial":
            titles = [
                f"2026 評測：{keyword}相關產品對比指南",
                f"選購建議：{keyword}該怎麼挑？優缺點全解析",
                f"{keyword}推薦清單：適合新手的 CP 值之選"
            ]
        elif intent == "transactional":
            titles = [
                f"立即體驗{keyword}！限時優惠方案",
                f"{keyword}服務預約：專業團隊為您服務",
                f"現在就開始{keyword}，享受專屬折扣"
            ]
        elif intent == "navigational":
            titles = [
                f"{keyword}官方入口：快速登入與導覽",
                f"前往{keyword}：完整路線指南",
                f"{keyword}導航：找到您需要的資源"
            ]
        else:
            # Informational (default)
            style_label = "初學者" if tone == "新手友善型" else "專業人士"
            titles = [
                f"想學{keyword}必看！2026 最新科學指南",
                f"5 個關於{keyword}的核心觀念，讓你事半功倍",
                f"破解{keyword}常見迷思：這才是最適合{style_label}的策略"
            ]
        
        return titles
    
    def _generate_eeat_tips(
        self,
        keyword: str,
        intent: str,
        competitor_data: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        """Generate E-E-A-T optimization tips."""
        tips = []
        
        # Experience
        tips.append("強化「經驗 (Experience)」：加入實際測試或個人心得。")
        
        # Intent-based tip
        if intent == "informational":
            tips.append("對齊「教學」邏輯：使用步驟式說明，幫助讀者理解。")
        elif intent == "commercial":
            tips.append("對齊「評測」邏輯：提供客觀數據與比較表格。")
        elif intent == "transactional":
            tips.append("對齊「轉換」邏輯：清晰的 CTA 與價值主張。")
        else:
            tips.append("對齊「導航」邏輯：提供明確的路徑指引。")
        
        # Authority
        tips.append("引用權威來源（研究報告、官方數據）增加可信度。")
        
        # Trustworthiness
        tips.append("加入作者資訊與更新日期，展示內容的可信賴性。")
        
        return tips


# Singleton instance
strategy_service = StrategyService()

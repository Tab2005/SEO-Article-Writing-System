"""
TF-IDF Keyword Extraction Service.

提取競品網頁中高頻且具語意關聯的關鍵詞。
支援中文（使用 jieba 分詞）和英文。

功能：
1. TF-IDF 詞頻分析 - 提取高頻重要詞彙
2. 關鍵詞提取 - 使用 TextRank 演算法
3. N-gram 分析 - 提取常見詞組搭配（2-gram, 3-gram, 4-gram）
4. 語意相關詞 - 基於共現分析的相關詞
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict

import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer

from app.schemas.research import CompetitorData


class TFIDFService:
    """TF-IDF 關鍵詞提取服務"""
    
    # 中文停用詞（常見無意義詞）
    CHINESE_STOPWORDS = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一個",
        "上", "也", "很", "到", "說", "要", "去", "你", "會", "著", "沒有", "看", "好",
        "自己", "這", "那", "這個", "那個", "他", "她", "它", "們", "什麼", "怎麼",
        "為什麼", "哪", "哪裡", "哪個", "如何", "可以", "能", "能夠", "應該", "必須",
        "需要", "想", "想要", "知道", "覺得", "認為", "可能", "或者", "還是", "但是",
        "因為", "所以", "如果", "雖然", "然後", "已經", "正在", "將", "把", "被",
        "給", "讓", "用", "通過", "進行", "使用", "根據", "關於", "對於", "為了",
        "以", "與", "及", "等", "等等", "之", "其", "而", "且", "或", "則", "於",
        "更", "最", "非常", "特別", "十分", "相當", "比較", "尤其", "甚至", "只",
        "僅", "才", "再", "又", "還", "並", "卻", "倒", "反而", "來", "去",
        "個", "些", "種", "樣", "次", "點", "件", "條", "塊", "位", "名",
        # 網頁常見無意義詞
        "網站", "網頁", "點擊", "瀏覽", "更多", "詳情", "查看", "了解",
        "首頁", "返回", "下載", "分享", "收藏", "評論", "留言",
        # 英文常見停用詞
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "can", "this", "that", "these",
        "those", "i", "you", "he", "she", "it", "we", "they", "what", "which",
        "who", "when", "where", "why", "how", "all", "each", "every", "both",
        "few", "more", "most", "other", "some", "such", "no", "not", "only",
        "same", "so", "than", "too", "very", "just", "but", "and", "or", "if",
        "because", "as", "until", "while", "of", "at", "by", "for", "with",
        "about", "against", "between", "into", "through", "during", "before",
        "after", "above", "below", "to", "from", "up", "down", "in", "out",
        "on", "off", "over", "under", "again", "further", "then", "once",
    }
    
    # 需要過濾的無意義詞彙模式
    FILTER_PATTERNS = [
        r"^\d+$",           # 純數字
        r"^[a-z]$",         # 單個字母
        r"^[\u4e00-\u9fff]$",  # 單個中文字
        r"^(https?|www|com|org|net|html|css|js|php|asp)$",  # 網址相關
        r"^\d{2,4}年?\d{0,2}月?\d{0,2}日?$",  # 日期
    ]
    
    def __init__(self):
        # 設定 jieba
        jieba.setLogLevel(jieba.logging.INFO)
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.FILTER_PATTERNS]
    
    def _is_valid_term(self, term: str, min_len: int = 2) -> bool:
        """檢查詞彙是否有效（非停用詞、非無意義詞）"""
        term_lower = term.lower().strip()
        
        # 長度檢查
        if len(term_lower) < min_len:
            return False
        
        # 停用詞檢查
        if term_lower in self.CHINESE_STOPWORDS:
            return False
        
        # 模式過濾
        for pattern in self._compiled_patterns:
            if pattern.match(term_lower):
                return False
        
        return True
    
    def _segment_text(self, text: str, keep_long: bool = True) -> List[str]:
        """
        對文本進行分詞，保留較長的詞彙。
        """
        # 使用 jieba 搜尋模式（會提取更多詞組）
        if keep_long:
            words = jieba.cut_for_search(text)
        else:
            words = jieba.cut(text, cut_all=False)
        
        # 過濾並返回有效詞彙
        return [w.strip() for w in words if self._is_valid_term(w)]
    
    def _extract_ngrams(self, text: str, n: int = 2) -> List[str]:
        """
        提取 N-gram 詞組。
        
        Args:
            text: 輸入文本
            n: N-gram 的 N 值（2=bigram, 3=trigram）
            
        Returns:
            N-gram 詞組列表
        """
        # 先用 jieba 分詞
        words = list(jieba.cut(text, cut_all=False))
        
        # 過濾停用詞但保留較短的詞
        filtered_words = [w for w in words if w.strip() and w not in self.CHINESE_STOPWORDS and len(w.strip()) >= 1]
        
        # 生成 N-gram
        ngrams = []
        for i in range(len(filtered_words) - n + 1):
            gram = "".join(filtered_words[i:i+n])
            # 只保留有意義的 N-gram
            if len(gram) >= 3:
                ngrams.append(gram)
        
        return ngrams
    
    def extract_keywords_textrank(
        self,
        text: str,
        top_n: int = 30,
    ) -> List[Tuple[str, float]]:
        """
        使用 TextRank 演算法提取關鍵詞。
        """
        keywords = jieba.analyse.textrank(
            text, 
            topK=top_n * 3,
            withWeight=True,
            allowPOS=('n', 'ns', 'nr', 'nt', 'nz', 'v', 'vn', 'a', 'an', 'vd', 'vg')
        )
        
        filtered = [(word, weight) for word, weight in keywords if self._is_valid_term(word)]
        return filtered[:top_n]
    
    def extract_keywords_tfidf(
        self,
        text: str,
        top_n: int = 30,
    ) -> List[Tuple[str, float]]:
        """
        使用 jieba TF-IDF 提取關鍵詞。
        """
        keywords = jieba.analyse.extract_tags(
            text, 
            topK=top_n * 3,
            withWeight=True,
            allowPOS=('n', 'ns', 'nr', 'nt', 'nz', 'v', 'vn', 'a', 'an', 'eng', 'vd', 'vg')
        )
        
        filtered = [(word, weight) for word, weight in keywords if self._is_valid_term(word)]
        return filtered[:top_n]
    
    def extract_ngram_phrases(
        self,
        documents: List[str],
        min_n: int = 2,
        max_n: int = 4,
        top_n: int = 20,
    ) -> List[Tuple[str, int]]:
        """
        從多文檔提取常見 N-gram 詞組（長尾關鍵詞）。
        """
        all_ngrams = []
        
        for doc in documents:
            for n in range(min_n, max_n + 1):
                ngrams = self._extract_ngrams(doc, n)
                all_ngrams.extend(ngrams)
        
        # 統計詞頻
        ngram_counter = Counter(all_ngrams)
        
        # 過濾只出現一次的，且長度要 >= 4
        common_ngrams = [
            (gram, count) for gram, count in ngram_counter.most_common(top_n * 3) 
            if count >= 2 and len(gram) >= 4
        ]
        
        return common_ngrams[:top_n]
    
    def extract_cooccurrence_terms(
        self,
        documents: List[str],
        target_keyword: str,
        window_size: int = 10,
        top_n: int = 20,
    ) -> List[Tuple[str, int]]:
        """
        提取與目標關鍵字共現的語意相關詞。
        """
        cooccurrence = Counter()
        target_lower = target_keyword.lower()
        
        for doc in documents:
            # 分詞
            words = list(jieba.cut(doc, cut_all=False))
            words = [w.strip() for w in words if w.strip()]
            
            # 找到目標關鍵字的位置
            for i, word in enumerate(words):
                if target_lower in word.lower():
                    # 取得窗口內的詞
                    start = max(0, i - window_size)
                    end = min(len(words), i + window_size + 1)
                    
                    for j in range(start, end):
                        if i != j:
                            w = words[j]
                            if self._is_valid_term(w) and len(w) >= 2:
                                cooccurrence[w] += 1
        
        # 過濾目標關鍵字本身
        result = [
            (word, count) for word, count in cooccurrence.most_common(top_n * 2) 
            if target_lower not in word.lower() and count >= 2
        ]
        
        return result[:top_n]
    
    def extract_multi_doc_tfidf(
        self,
        documents: List[str],
        top_n: int = 30,
    ) -> List[Tuple[str, float]]:
        """
        使用 sklearn TfidfVectorizer 從多文檔提取關鍵詞。
        """
        if not documents:
            return []
        
        # 對每個文檔進行分詞
        tokenized_docs = [" ".join(self._segment_text(doc, keep_long=True)) for doc in documents]
        tokenized_docs = [doc for doc in tokenized_docs if doc.strip()]
        
        if not tokenized_docs:
            return []
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=1,
                max_df=0.9,
                token_pattern=r"(?u)\b\w+\b",
            )
            
            tfidf_matrix = vectorizer.fit_transform(tokenized_docs)
            feature_names = vectorizer.get_feature_names_out()
            avg_scores = tfidf_matrix.mean(axis=0).A1
            
            term_scores = list(zip(feature_names, avg_scores))
            term_scores = [
                (term, score) for term, score in term_scores 
                if self._is_valid_term(term) and len(term) >= 2
            ]
            term_scores.sort(key=lambda x: x[1], reverse=True)
            
            return term_scores[:top_n]
            
        except Exception as e:
            print(f"[TF-IDF] sklearn extraction failed: {e}")
            return []
    
    def analyze_competitors(
        self,
        competitors: List[CompetitorData],
        target_keyword: str,
        top_n: int = 30,
    ) -> Dict[str, any]:
        """
        分析競品網頁，提取關鍵詞建議。
        
        功能：
        1. 高頻核心詞 - TF-IDF + TextRank 綜合分析
        2. 語意相關詞 - 共現分析（與目標關鍵字一起出現的詞）
        3. 長尾關鍵詞 - N-gram 詞組分析
        """
        if not competitors:
            return {
                "suggested_keywords": [],
                "keyword_categories": {
                    "high_frequency": [],
                    "semantic_related": [],
                    "long_tail": [],
                },
                "competitor_common_terms": [],
            }
        
        # 收集所有競品的文本內容
        all_texts = []
        
        for comp in competitors:
            texts = [comp.title]
            if comp.meta_description:
                texts.append(comp.meta_description)
            texts.extend(comp.headings.h1)
            texts.extend(comp.headings.h2)
            texts.extend(comp.headings.h3)
            all_texts.append(" ".join(texts))
        
        combined_text = " ".join(all_texts)
        target_lower = target_keyword.lower()
        
        # ===== 1. 高頻核心詞（TF-IDF + TextRank）=====
        tfidf_keywords = self.extract_keywords_tfidf(combined_text, top_n=top_n)
        textrank_keywords = self.extract_keywords_textrank(combined_text, top_n=top_n)
        multi_doc_keywords = self.extract_multi_doc_tfidf(all_texts, top_n=top_n)
        
        high_freq_scores: Dict[str, float] = {}
        for word, score in tfidf_keywords:
            if target_lower not in word.lower():
                high_freq_scores[word] = high_freq_scores.get(word, 0) + score
        for word, score in textrank_keywords:
            if target_lower not in word.lower():
                high_freq_scores[word] = high_freq_scores.get(word, 0) + score * 0.8
        for word, score in multi_doc_keywords:
            if target_lower not in word.lower():
                high_freq_scores[word] = high_freq_scores.get(word, 0) + score * 1.2
        
        high_frequency = [
            {"term": word, "score": round(score, 4)}
            for word, score in sorted(high_freq_scores.items(), key=lambda x: -x[1])
        ][:15]
        
        # ===== 2. 語意相關詞（共現分析）=====
        cooccurrence_terms = self.extract_cooccurrence_terms(
            all_texts, target_keyword, window_size=10, top_n=top_n
        )
        
        semantic_related = [
            {"term": word, "score": round(count / 10, 4)}
            for word, count in cooccurrence_terms
            if len(word) >= 2
        ][:15]
        
        # ===== 3. 長尾關鍵詞（N-gram）=====
        ngram_phrases = self.extract_ngram_phrases(all_texts, min_n=2, max_n=4, top_n=top_n)
        
        long_tail = [
            {"term": phrase, "score": round(count / 5, 4)}
            for phrase, count in ngram_phrases
            if target_lower not in phrase.lower() and len(phrase) >= 4
        ][:15]
        
        # ===== 4. 競品共同出現詞彙 =====
        term_in_competitors: Dict[str, int] = Counter()
        for text in all_texts:
            words = set(self._segment_text(text, keep_long=True))
            for word in words:
                if len(word) >= 2:
                    term_in_competitors[word] += 1
        
        common_terms = [
            {"term": term, "count": count}
            for term, count in term_in_competitors.most_common(30)
            if count >= 2 and target_lower not in term.lower() and len(term) >= 2
        ][:20]
        
        # ===== 整合所有建議關鍵詞 =====
        all_keywords: Dict[str, float] = {}
        
        for item in high_frequency:
            all_keywords[item["term"]] = max(all_keywords.get(item["term"], 0), item["score"])
        for item in semantic_related:
            all_keywords[item["term"]] = max(all_keywords.get(item["term"], 0), item["score"] * 0.8)
        for item in long_tail:
            all_keywords[item["term"]] = max(all_keywords.get(item["term"], 0), item["score"] * 0.6)
        
        suggested_keywords = [
            {"term": word, "score": round(score, 4)}
            for word, score in sorted(all_keywords.items(), key=lambda x: -x[1])
        ][:top_n]
        
        return {
            "suggested_keywords": suggested_keywords,
            "keyword_categories": {
                "high_frequency": high_frequency,
                "semantic_related": semantic_related,
                "long_tail": long_tail,
            },
            "competitor_common_terms": common_terms,
        }


# Singleton instance
tfidf_service = TFIDFService()

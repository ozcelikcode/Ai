import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import json

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA7kpevybllWyvF-Vxjob2tjKW65mgEwqM")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AIContentGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
    def generate_blog_post(
        self,
        topic: str,
        content_length: str = "medium",
        content_type: str = "informative",
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete blog post using AI
        
        Args:
            topic: The main topic/title for the blog post
            content_length: "short", "medium", "long"
            content_type: "informative", "tutorial", "opinion", "news"
            custom_prompt: Optional custom prompt to override defaults
            
        Returns:
            Dict containing title, content, excerpt, meta_description
        """
        
        try:
            # Length guidelines
            length_guide = {
                "short": "300-500 kelime",
                "medium": "700-1000 kelime", 
                "long": "1200-1800 kelime"
            }
            
            # Content type guidelines
            type_guide = {
                "informative": "bilgilendirici ve eğitici",
                "tutorial": "adım adım rehber niteliğinde",
                "opinion": "görüş ve analiz odaklı",
                "news": "haber formatında güncel"
            }
            
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = f"""
                Türkçe olarak "{topic}" konusunda {type_guide.get(content_type, 'bilgilendirici')} bir blog yazısı yaz.
                
                Gereksinimler:
                - Yazı uzunluğu: {length_guide.get(content_length, '700-1000 kelime')}
                - Stil: {type_guide.get(content_type, 'bilgilendirici ve eğitici')}
                - Türkçe dilbilgisi kurallarına uygun
                - SEO dostu yapıda
                - Okuyucuyu meraklandıran giriş
                - Net alt başlıklar (H2, H3 HTML etiketleri ile)
                - Sonuç bölümü
                
                Lütfen yanıtını şu JSON formatında ver:
                {{
                    "title": "Çekici ve SEO dostu başlık",
                    "content": "HTML formatında tam blog içeriği",
                    "excerpt": "150-200 kelimelik özet",
                    "meta_description": "SEO için 150-160 karakterlik açıklama",
                    "tags": ["etiket1", "etiket2", "etiket3"]
                }}
                """
            
            response = self.model.generate_content(prompt)
            
            # Try to parse JSON response
            try:
                # Clean the response text
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                result = json.loads(response_text)
                
                # Validate required fields
                required_fields = ['title', 'content', 'excerpt', 'meta_description']
                for field in required_fields:
                    if field not in result:
                        result[field] = self._generate_fallback_content(topic, field)
                
                return {
                    "success": True,
                    "data": result
                }
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract content manually
                return self._parse_text_response(response.text, topic)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": self._generate_fallback_content(topic)
            }
    
    def generate_title_suggestions(self, topic: str, count: int = 5) -> list:
        """Generate multiple title suggestions for a topic"""
        try:
            prompt = f"""
            "{topic}" konusu için {count} adet çekici ve SEO dostu blog başlığı öner.
            Her başlık:
            - 50-60 karakter arası olsun
            - Tıklanma oranını artıracak şekilde merak uyandırsın
            - Türkçe dilbilgisi kurallarına uygun olsun
            
            Sadece başlıkları liste halinde ver, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(prompt)
            titles = [title.strip().strip('- ') for title in response.text.split('\n') if title.strip()]
            
            return titles[:count]
            
        except Exception as e:
            # Fallback titles
            return [
                f"{topic} Hakkında Bilmeniz Gerekenler",
                f"{topic} Rehberi: Başlangıçtan İleri Seviyeye",
                f"{topic} ile İlgili En Güncel Bilgiler",
                f"{topic}: Kapsamlı Analiz ve İncelemesi",
                f"{topic} Konusunda Uzman Görüşleri"
            ]
    
    def improve_content(self, content: str, instruction: str) -> str:
        """Improve existing content based on instruction"""
        try:
            prompt = f"""
            Aşağıdaki blog yazısını "{instruction}" talimatına göre geliştir:
            
            Mevcut İçerik:
            {content}
            
            Geliştirme Talimatı: {instruction}
            
            Lütfen sadece geliştirilmiş içeriği döndür, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return content  # Return original content if improvement fails
    
    def _parse_text_response(self, text: str, topic: str) -> Dict[str, Any]:
        """Parse non-JSON AI response and extract content"""
        lines = text.split('\n')
        
        # Try to find title, content, etc. in the response
        title = topic
        content = text
        excerpt = text[:200] + "..."
        meta_description = text[:150] + "..."
        
        # Simple parsing logic - you can make this more sophisticated
        for i, line in enumerate(lines):
            if 'başlık' in line.lower() or 'title' in line.lower():
                if i + 1 < len(lines):
                    title = lines[i + 1].strip()
                    break
        
        return {
            "success": True,
            "data": {
                "title": title,
                "content": f"<p>{content}</p>",
                "excerpt": excerpt,
                "meta_description": meta_description,
                "tags": []
            }
        }
    
    def _generate_fallback_content(self, topic: str, field: str = None) -> Any:
        """Generate fallback content when AI fails"""
        fallback_data = {
            "title": f"{topic} Hakkında",
            "content": f"<h2>{topic}</h2><p>Bu içerik AI tarafından oluşturulmuştur. Detaylar için lütfen manuel olarak düzenleyin.</p>",
            "excerpt": f"{topic} hakkında AI tarafından oluşturulan içerik.",
            "meta_description": f"{topic} hakkında detaylı bilgi.",
            "tags": [topic.lower()]
        }
        
        if field:
            return fallback_data.get(field, "")
        return fallback_data

# Singleton instance
ai_generator = AIContentGenerator()
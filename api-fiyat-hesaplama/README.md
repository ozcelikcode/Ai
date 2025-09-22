# 🧠 AI API Price Calculator

Modern ve kullanıcı dostu AI API fiyatlandırma hesaplayıcısı. Çeşitli yapay zeka modellerinin token kullanımına dayalı maliyet hesaplamasını yapabilirsiniz.

## ✨ Özellikler

### 🎯 Temel Özellikler
- **12+ AI Modeli**: OpenAI, Anthropic, Google, Meta'dan popüler modeller
- **Gerçek Zamanlı Hesaplama**: Anlık fiyat hesaplaması
- **Token Tahmini**: Metin girişi ile otomatik token tahmini
- **Hesaplama Geçmişi**: Önceki hesaplamaları kaydetme ve geri yükleme
- **Karşılaştırma**: Farklı modeller arasında fiyat karşılaştırması

### 🎨 UI/UX Özellikleri
- **Modern Tasarım**: Minimal, profesyonel ve ferah arayüz
- **Dark/Light Theme**: Sistem tercihini destekleyen tema sistemi
- **Responsive**: Mobil ve masaüstü uyumlu
- **Slider Kontrolü**: Kolay token seçimi için kaydırmalı kontroller
- **Detaylı Sonuçlar**: Kapsamlı maliyet analizi

### 🛠️ Teknik Özellikler
- **Modern Tech Stack**: React + Vite + Node.js + Express
- **Type Safety**: Güçlü tip kontrolü ve validasyon
- **Error Handling**: Kapsamlı hata yönetimi
- **API Documentation**: RESTful API endpoints

## 🚀 Hızlı Başlangıç

### Önkoşullar
- Node.js (v18 veya üzeri)
- npm veya yarn

### Kurulum

1. **Repository'yi klonlayın**
   ```bash
   git clone <repository-url>
   cd api-fiyat-hesaplama
   ```

2. **Bağımlılıkları yükleyin**
   ```bash
   npm install
   cd backend && npm install
   cd ..
   ```

3. **Tek komutla başlatın** 🎉
   ```bash
   npm start
   ```

Bu komut hem backend'i hem frontend'i aynı anda başlatır:
- **Backend**: http://localhost:3001
- **Frontend**: http://localhost:5174 (port otomatik seçilir)

### Alternatif Çalıştırma

Servisleri ayrı ayrı çalıştırmak için:

```bash
# Sadece frontend
npm run start:frontend

# Sadece backend  
npm run start:backend
```

## 🤖 Desteklenen Modeller

### OpenAI
- GPT-4o - $2.50 / $10.00 per 1M tokens
- GPT-4o Mini - $0.15 / $0.60 per 1M tokens
- GPT-4 Turbo - $10.00 / $30.00 per 1M tokens
- GPT-3.5 Turbo - $0.50 / $1.50 per 1M tokens

### Anthropic
- Claude 3.5 Sonnet - $3.00 / $15.00 per 1M tokens
- Claude 3 Haiku - $0.25 / $1.25 per 1M tokens
- Claude 3 Opus - $15.00 / $75.00 per 1M tokens

### Google
- Gemini 1.5 Pro - $1.25 / $5.00 per 1M tokens
- Gemini 1.5 Flash - $0.075 / $0.30 per 1M tokens

### Meta
- Llama 3.1 405B - $5.32 / $16.00 per 1M tokens
- Llama 3.1 70B - $0.59 / $0.79 per 1M tokens
- Llama 3.1 8B - $0.055 / $0.08 per 1M tokens

## 🎨 Kullanım

1. **Model Seçimi**: Dropdown'dan istediğiniz AI modelini seçin
2. **Token Girişi**: Input token ve output token sayılarını girin
   - Manual input ile direkt sayı girin
   - Slider ile kolay seçim yapın
   - Hızlı seçim butonlarını kullanın
3. **Metin Tahmini**: (Opsiyonel) Metin girişi ile otomatik token tahmini
4. **Hesaplama**: "Calculate Cost" butonuna tıklayın
5. **Sonuçları İnceleyin**: Detaylı maliyet analizi ve breakdown
6. **Geçmiş**: Hesaplama geçmişinden önceki hesaplamaları geri yükleyin

## 🔌 API Endpoints

### Modeller
- `GET /api/models` - Tüm modelleri listele
- `GET /api/models/:id` - Belirli model bilgisi
- `GET /api/models/provider/:provider` - Provider'a göre modeller

### Hesaplama
- `POST /api/calculator/calculate` - Fiyat hesaplama
- `POST /api/calculator/batch-calculate` - Toplu hesaplama
- `POST /api/calculator/estimate-tokens` - Token tahmini

### Sağlık Kontrolü
- `GET /health` - Servis durumu

## 📊 Hesaplama Mantığı

// 1M token başına fiyatlandırma için
const inputCost = (inputTokens / 1_000_000) * model.pricing.input
const outputCost = (outputTokens / 1_000_000) * model.pricing.output
const totalCost = inputCost + outputCost
```

## 🛠️ Geliştirme

### Komutlar
```bash
npm start          # Hem frontend hem backend'i çalıştır
npm run dev        # Sadece frontend (development)
npm run build      # Production build
npm run lint       # Linting
npm run preview    # Production preview
```

---

Built with ❤️ using React + Vite + Express
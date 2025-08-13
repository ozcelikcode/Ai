# AI Blog Platform - Geliştirme Kuralları

Bu dokümanda AI Blog platformunun geliştirilmesi sırasında uyulması gereken tüm kurallar ve standartlar yer almaktadır.

## 🎨 Tasarım Kuralları

### CSS ve Stil Yaklaşımı
- **Tailwind CSS** tüm stil işlemleri için kullanılacak
- **Vanilla JavaScript** kullanılacak, harici framework kullanılmayacak
- **Yumuşak geçişli tasarımlar** tercih edilecek
- **Krem rengi-kahverengi tonları** ana renk paleti olacak
  - Krem: `#fefdfb` - `#825726` arası tonlar
  - Kahverengi: `#f7f3f0` - `#522c26` arası tonlar
- **Hafif ve göz yormayan animasyonlar** kullanılacak
- Animasyonlar sadece hover ve focus olaylarında aktif olacak
- Site yüklenirken animasyon olmayacak
- **Lucide Icons** ikon seti kullanılacak (FontAwesome yerine)

### Responsive Tasarım
- Tüm cihazlara tam uyumlu tasarım
- Mobile-first yaklaşım
- Breakpoint'ler: sm (640px), md (768px), lg (1024px), xl (1280px)

## 🔧 Backend Kuralları

### Teknoloji Stack
- **Python 3.8+** kullanılacak
- **FastAPI** web framework olarak kullanılacak
- **SQLite** veritabanı (kullanıcı müdahalesiz)
- **SQLAlchemy** ORM olarak kullanılacak
- **Pydantic** veri validasyonu için

### Kod Yapısı ve Kalite
- **Dinamik, profesyonel, geleceğe yönelik** kod yapısı
- Değişmesi kolay modüler yapı
- Topluluk tarafından kabul gören standartlar
- **Temiz kod** prensipleri
- Yorum satırları sadece gerekli yerlerde
- **Type hints** kullanımı zorunlu
- **Docstring** kritik fonksiyonlarda

### Güvenlik Standartları
- **Güvenlik zaafiyeti riski olan kod asla kullanılmayacak**
- **JWT** tabanlı kimlik doğrulama
- **Bcrypt** ile şifre hashleme
- **SQL injection** koruması
- **XSS** koruması
- **CSRF** koruması
- **Rate limiting** uygulanacak
- Kullanıcı girişleri her zaman validate edilecek

## 🗂️ Proje Yapısı

### Dosya ve Klasör Organizasyonu
Yaygın olarak kullanılan GitHub projesi yapısı:

```
ai-blog/
├── app/
│   ├── core/           # Veritabanı, auth, config
│   ├── models/         # SQLAlchemy modelleri
│   ├── routers/        # FastAPI route'ları
│   ├── utils/          # Yardımcı fonksiyonlar
│   └── __init__.py
├── static/
│   ├── css/            # Custom CSS (minimal)
│   ├── js/             # Vanilla JavaScript
│   ├── images/         # Statik resimler
│   └── media/          # Kullanıcı yüklemeleri
├── templates/
│   ├── admin/          # Admin panel şablonları
│   ├── blog/           # Blog şablonları
│   └── base.html       # Ana şablon
├── uploads/            # Kullanıcı dosyaları
├── main.py            # Ana uygulama
├── requirements.txt   # Python bağımlılıkları
├── .env               # Ortam değişkenleri
├── .gitignore        # Git ignore kuralları
├── README.md         # Kullanıcı dokümantasyonu
└── RULES.md          # Bu dosya
```

## 📝 Blog Özellikleri ve Gereksinimler

### Ana Özellikler
- Blog sayfasında temel araç ve gereçler
- SEO optimizasyonu (meta etiketler, slug, sitemap)
- Arama fonksiyonu (admin panel dahil)
- Admin panel giriş sistemi
- İlk admin: username=`admin`, password=`12345678`

### Admin Panel Gereksinimleri
- Profesyonel araçlar ve arayüz
- Resim işlemleri: yükleme, sürükleme, URL ile ekleme
- AI destekli içerik üretimi (Gemini API)
- Kategoriler sayfası
- Sayfa yönetimi (özel sayfalar)
- Ayarlar sayfası:
  - Site başlığı, logo, favicon
  - Meta etiketleri
  - Profil resimleri yönetimi
  - AI prompt ve parametreler
- Yorum sistemi ve onay/ret
- İçerik yönetimi:
  - Taslak sistemi
  - Otomatik slug üretimi
  - Güncellenme tarihi (açılabilir/kapanabilir)
  - Medya galerisi
- Yazı okuma süresi hesaplayıcı
- Beğeni sistemi (giriş yapmış kullanıcılar)
- Kullanıcı profil sayfaları

### Gemini API Entegrasyonu
- API Key: `AIzaSyA7kpevybllWyvF-Vxjob2tjKW65mgEwqM`
- Manuel ve AI seçenekleri
- Prompt, uzunluk, tür ayarları
- Hata yönetimi ve fallback

## 🔄 Geliştirme Süreci

### Kod Kalitesi
- **Çok değil, akıllı ve öz kod** yazılacak
- Hatalı kod yapılarından uzak durulacak
- Test yapıları sadece istendiğinde
- Code review zorunlu
- **Hiçbir kod parçası sorulmadan silinmeyecek**

### Problem Çözme Yaklaşımı
- Zor problemlerde köküne inilecek
- Araştırma odaklı çözüm
- Topluluk kaynaklarından faydalanma
- Dokümantasyon takibi

### Bölümsel Geliştirme
- **Her şey bölüm bölüm yapılacak**
- Tek seferde tüm sistemi yapmaya kalkışılmayacak
- Her modül test edilecek
- Incremental development

## 📚 Dokümantasyon Standartları

### README.md
- GitHub standartlarında
- Sade ve anlaşılır dil
- Kurulum talimatları
- Detaylı ama özlü
- Kullanıcı odaklı bilgiler

### RULES.md (Bu Dosya)
- Geliştirici kuralları
- Teknik detaylar
- Kod standartları
- İç dokümantasyon

## 🚀 Deployment ve Production

### Üretim Ortamı Kuralları
- `DEBUG=False` ayarı
- Güçlü SECRET_KEY
- HTTPS zorunlu
- Güvenlik başlıkları
- Error handling
- Logging sistemi
- Backup stratejisi

### Performance
- Database query optimization
- Static file caching
- Image optimization
- Minification (gerektiğinde)

## ⚠️ Önemli Hatırlatmalar

1. **Kullanıcı bilgileri sadece README.md'de**
2. **Kurallar RULES.md'de**
3. **Kod temizliği ve güvenlik öncelik**
4. **Performans ve UX odaklı geliştirme**
5. **Bölüm bölüm geliştirme**
6. **Community best practices takibi**
7. **Sürekli öğrenme ve iyileştirme**

---

Bu kurallar projenin tutarlılığını ve kalitesini sağlamak için titizlikle uygulanmalıdır.
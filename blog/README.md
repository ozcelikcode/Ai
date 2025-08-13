# AI Blog Platform

Modern yapay zeka destekli blog platformu. FastAPI backend ve Vanilla JavaScript frontend ile geliştirilmiş, SQLite veritabanı kullanan profesyonel bir blog sistemi.

## 🚀 Özellikler

### 🎯 Ana Özellikler
- **AI Destekli İçerik Üretimi** - Gemini 2.5 Pro API ile otomatik blog yazısı oluşturma
- **Modern Responsive Tasarım** - Tailwind CSS ile krem-kahverengi tema
- **Dinamik Admin Panel** - Kapsamlı yönetim sistemi
- **Gelişmiş Arama Sistemi** - Frontend ve admin panelde güçlü arama

### 👤 Kullanıcı Deneyimi
- **Kullanıcı Kayıt/Giriş Sistemi** - Güvenli kimlik doğrulama
- **Profil Yönetimi** - Avatar seçimi ve şifre değiştirme
- **Yorum Sistemi** - Onay/ret mekanizması ile moderasyon
- **Beğenme Sistemi** - Giriş yapan kullanıcılar için

### 🔧 Yönetim Özellikleri
- **Kategoriler** - Blog yazıları için kategori yönetimi
- **Etiketler** - Otomatik tamamlama ile etiket sistemi
- **Medya Galerisi** - Resim yükleme (dosya/URL ile)
- **Sayfa Yönetimi** - Özel sayfa oluşturma
- **SEO Optimizasyonu** - Meta etiketleri ve slug sistemi
- **Taslak Sistemi** - Yazıları taslak olarak kaydetme

### 🛡️ Güvenlik
- **JWT Tabanlı Kimlik Doğrulama** - Güvenli session yönetimi
- **Admin Yetkilendirme** - Rol tabanlı erişim kontrolü
- **Input Validation** - Güvenli veri işleme

## 📋 Gereksinimler

- Python 3.8+
- SQLite (otomatik kurulum)

## 🛠️ Kurulum

### 1. Projeyi İndirin
```bash
git clone https://github.com/yourusername/ai-blog.git
cd ai-blog
```

### 2. Virtual Environment Oluşturun
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Ortam Değişkenlerini Ayarlayın
`.env.example` dosyasını `.env` olarak kopyalayın ve gerekli ayarları yapın:
```bash
cp .env.example .env
```

`.env` dosyasında SECRET_KEY'i değiştirin (üretim ortamı için).

### 5. Veritabanını Başlatın
```bash
python app/utils/init_db.py
```

### 6. Uygulamayı Çalıştırın
```bash
python main.py
```

Uygulama `http://localhost:8000` adresinde çalışacaktır.

## 👤 İlk Giriş

İlk admin kullanıcısı otomatik oluşturulur:
- **Kullanıcı Adı:** `admin`
- **Şifre:** `12345678`

Admin paneline `http://localhost:8000/admin` adresinden erişebilirsiniz.

## 📁 Proje Yapısı

```
ai-blog/
├── app/
│   ├── core/           # Temel sistem dosyaları
│   ├── models/         # Veritabanı modelleri
│   ├── routers/        # API endpoint'leri
│   └── utils/          # Yardımcı fonksiyonlar
├── static/             # CSS, JS, resim dosyaları
├── templates/          # HTML şablonları
├── uploads/            # Yüklenen dosyalar
├── main.py            # Ana uygulama
└── requirements.txt   # Python bağımlılıkları
```

## 🔧 Yapılandırma

### Gemini API
AI destekli içerik üretimi için Gemini API kullanılmaktadır. `.env` dosyasında API anahtarınızı ayarlayın.

### Veritabanı
Varsayılan olarak SQLite kullanılır. Farklı bir veritabanı için `DATABASE_URL` ayarını değiştirin.

## 🚀 Deployment

### Üretim Ortamı
1. `.env` dosyasında `DEBUG=False` ayarlayın
2. Güçlü bir `SECRET_KEY` oluşturun
3. HTTPS kullanın
4. Güvenlik başlıklarını yapılandırın

### Docker (Opsiyonel)
```bash
# Dockerfile oluşturulacak
docker build -t ai-blog .
docker run -p 8000:8000 ai-blog
```

## 🤝 Katkıda Bulunma

1. Fork'layın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit'leyin (`git commit -m 'Add amazing feature'`)
4. Push'layın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 Destek

Herhangi bir sorun için issue açabilir veya iletişime geçebilirsiniz.

---

**AI Blog Platform** - Modern blog deneyimi için tasarlandı.
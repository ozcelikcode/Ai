# Blog Projesi

Modern ve profesyonel bir blog uygulaması. Go backend ve Tailwind CSS ile responsive frontend tasarımı.

## Özellikler

✨ **Modern Tasarım**
- Tailwind CSS ile responsive tasarım
- Krem-kahve renk paleti
- Yumuşak geçişler ve animasyonlar
- Lucide Icons icon seti

🔐 **Güvenli Admin Paneli**
- JWT tabanlı kimlik doğrulama
- Güvenli şifre hashleme (bcrypt)
- Admin yetkilendirme sistemi

📝 **Blog Yönetimi**
- Yazı oluşturma, düzenleme ve silme
- Taslak/Yayın durumu yönetimi
- Otomatik slug oluşturma
- Özet (excerpt) desteği

🏗️ **Sağlam Mimari**
- Temiz kod yapısı
- Modüler Go backend
- SQLite veritabanı (kurulum gerektirmez)
- RESTful API

## Kurulum

### Gereksinimler
- Go 1.21 veya üzeri
- Git

### Adımlar

1. **Projeyi klonlayın**
   ```bash
   git clone <repository-url>
   cd blog
   ```

2. **Go modüllerini indirin**
   ```bash
   go mod tidy
   ```

3. **Uygulamayı başlatın**
   ```bash
   go run ./cmd/blog
   ```
   Alternatif (Node.js bulunanlar için):
   ```bash
   npm run dev
   ```

4. **Tarayıcınızda açın**
   ```
   http://localhost:8081
   ```

## Kullanım

### İlk Admin Girişi
Uygulama ilk çalıştırıldığında otomatik olarak admin kullanıcısı oluşturulur:
- **Kullanıcı Adı:** `admin`
- **Şifre:** `12345678`

### Admin Panel
- Admin paneline erişim: `http://localhost:8081/admin`
- Yeni yazı oluşturma, düzenleme ve silme
- Yazıları taslak olarak kaydetme veya yayınlama

### API Endpoints

#### Genel Kullanım
- `GET /api/posts?published=true` - Yayınlanan yazıları listele
- `GET /api/posts/:id` - Yazı detayını getir
- `GET /api/posts/slug/:slug` - Slug ile yazı getir

#### Kimlik Doğrulama
- `POST /api/auth/login` - Admin girişi

#### Admin İşlemleri (Token gerekli)
- `POST /api/posts` - Yeni yazı oluştur
- `PUT /api/posts/:id` - Yazı güncelle
- `DELETE /api/posts/:id` - Yazı sil

## Proje Yapısı

```
├── cmd/blog/           # Ana uygulama
├── internal/
│   ├── auth/          # JWT işlemleri
│   ├── database/      # Veritabanı bağlantısı
│   ├── handlers/      # HTTP handler'lar
│   ├── middleware/    # Middleware'ler
│   └── models/        # Veri modelleri
├── web/
│   ├── templates/     # HTML şablonları
│   └── static/        # CSS, JS, resim dosyaları
├── go.mod             # Go modül dosyası
└── README.md          # Bu dosya
```

## Geliştirme

### Veritabanı
Proje SQLite kullanır. Veritabanı dosyası (`blog.db`) otomatik olarak oluşturulur.

### Güvenlik
- Şifreler bcrypt ile hashlenir
- JWT token'lar kullanılır
- Admin yetkilendirme middleware'i

### Özelleştirme
- Renkler: `web/templates/base.html` içindeki Tailwind config
- Stil: Tailwind CSS sınıfları
- API: `internal/handlers/` klasöründeki handler'lar

## Lisans

Bu proje açık kaynak kodludur.

## Destek

Sorunlar ve öneriler için GitHub Issues kullanın.


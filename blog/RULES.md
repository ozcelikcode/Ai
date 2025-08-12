# Proje Geliştirme Kuralları

## Tasarım Kuralları

### CSS ve Stil
- **Tailwind CSS** her kısımda kullanılacak
- **Yumuşak geçişli tasarımlar** tercih edilecek
- **Krem rengi-kahverengi tarzlarında** (Claude'un yeni tasarımı gibi) çok açık ve göz yormayan renkler kullanılacak
- **Hafif ve göz yormayan animasyonlar** olacak
- Her kısımda animasyon kullanılmaz
- Site açılışında ya da yenilenmesinde animasyon yüklenmesi olmayacak
- Sadece hover ve focus gibi olaylarda animasyon olacak
- **Lucide Icons** (FontAwesome alternatifi en iyi ve ücretsiz ikon seti) kullanılacak

## Backend Kuralları

### Teknoloji ve Yapı
- **Go dili** ile yazılacak
- **Dinamik, profesyonel, geleceğe yönelik** kod yapısı olması gerek
- **Değişmesi kolay ve topluluk tercihi** bir yapı tercih edilmeli
- **Popüler veritabanı** tercihi (SQLite - ayar kullanıcı-yönetici tarafından müdahale gerektirmeyen)
- **Temiz kod yapısı** ve sadece gereken kısımlarda yorum satırları

### Güvenlik
- **Güvenlik zaafiyeti verecek herhangi bir kod yapısı asla kullanılmamalı**
- **Güvenli ve profesyonel kod yapıları** tercih edilmeli
- Şifreleme ve kimlik doğrulama en iyi uygulamalarla yapılacak

## Geliştirme Yaklaşımı

### Kod Kalitesi
- **Çok değil, akıllı ve öz kod** yazılacak
- **Hatalı olabilecek kod yapılarından** uzak durulacak
- Test yapıları sadece istendiğinde oluşturulacak

### Problem Çözme
- **Zor ve çözülemeyen sorunlarda sorunun köküne** inilmeli
- Yine olmazsa **kod yapısı hakkında daha çok araştırma** yapılacak
- **Herhangi bir kod yapısı ve fonksiyon sorulmadan asla silinmemeli**

## Proje Gereksinimleri

### Blog Özellikleri
- **Blog sayfasında olması gereken temel araç ve gereçler** içinde barındırılacak
- **Admin panel giriş sayfası** olacak
- İlk admin oluşturulduğunda:
  - Kullanıcı adı: `admin`
  - Şifre: `12345678`

### Dokümantasyon
- **README.md**: Github standartlarında, kullanıcılara sunacakmış gibi sade ve anlaşılır dilde
- Kurulum sayfası içerecek
- Abartıya kaçmadan detaylı ve özlü olacak

## Önemli Notlar

- Bu kurallar geliştirici için rehberdir
- README.md dosyasında bu kurallara değinilmez
- Kullanıcılar için sadece gerekli bilgiler README.md'de yer alır
- Kod temizliği ve güvenlik her zaman öncelik
- Performans ve kullanıcı deneyimi odaklı geliştirme
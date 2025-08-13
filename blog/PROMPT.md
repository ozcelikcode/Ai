# Proje Geliştirme Kuralları

## Tasarım Kuralları

### CSS ve Stil
- **Tailwind CSS** her kısımda kullanılacak
- **Vanilla JS** kullanılacak
- **Yumuşak geçişli tasarımlar** tercih edilecek
- **Krem rengi-kahverengi tarzlarında** Krem ve kahverengi gibi çok açık ve göz yormayan renkler kullanılacak
- **Hafif ve göz yormayan animasyonlar** olacak
- Her kısımda animasyon kullanılmaz
- Site açılışında ya da yenilenmesinde animasyon yüklenmesi olmayacak
- Sadece hover ve focus gibi olaylarda animasyon olacak
- **Lucide Icons** (FontAwesome alternatifi en iyi ve ücretsiz ikon seti) kullanılacak

## Backend Kuralları

### Teknoloji ve Yapı
- **Python dili** ile yazılacak, Framework olarak FastApi kullanılacak
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
- SEO optimizasyonu çok iyi olacak, kodlar seo dostu olmalı
- **Arama fonksiyonu** olacak (admin panelde : sayfa yönetimi ve içerik kısmında da dahildir)
- **Admin panel giriş sistemi** olacak
- İlk admin oluşturulduğunda:
  - Kullanıcı adı: `admin`
  - Şifre: `12345678`
- **Admin panel ve genel**
  - admin panel genelinde profesyonel araçlar barındırılmalı
    - resim (yükleme, sürükleme, url ile belirtme) işlemleri
    - başlık, etiket, kategori, yazı içeriği yapay zeka ile doldurulsun seçeneği ile yapay zekaya tam destekli içerik yazdırılabilecek (sayfalar yönetimi kısmı yapay zeka için dahildir). Manuel ve yapay zeka ile yap seçeneği olmalı. Gemini (2.5 Pro) API ile yapılacaktır: AIzaSyA7kpevybllWyvF-Vxjob2tjKW65mgEwqM
  - **kategoriler sayfası** olacak
  - **sayfa yönetimi** olacak. Özel sayfa oluşturmak mümkün olacak
  - **ayarlar sayfası** olacak
    - site başlık (yükleme ile logo, url ile seçim), favicon, site meta tagları gibi olması gereken kısımlar bulunacak ve tam fonksiyon çalışacak
    - profil resimleri seçimleri sonsuz eklenebilir olmalı. Resim yükleme ve url ile seçim seçenekleri ile ekleme seçenekleri olmalı (her biri için)
    - **yapay zeka** prompt'u, yazı uzunluğu, türü gibi kurallar değiştirilebilir olacak
  - **Yorum sistemi** olacak
    - **Yorum onay-ret** sayfası olacak
    - kullanıcılar için **login ve register sayfası** özel bir sayfada olacaktır (/login, /register şeklinde)
  - **İçerik yönetimi**
    - İçerik ekleme ve düzenleme, sayfa ekleme ve düzenleme gibi işlevler tek sayfada dinamik bir şekilde olacaktır
    - taslak sistemi olacak
    - slug sistemi olacaktır, başlık yazıldıkça slug otomatik olarak değişecektir ve önizlemesi gösterilecektir. Değiştirilebilir olmalıdır (sayfa yönetimi de dahildir)
    - Güncellenme tarihi gösterilecek fakat isteğe bağlı olarak açılıp kapanabilecek, varsayılan açık olacak (sayfa yönetimi kısmı dahildir)
    - **Medya galerisi** sayfası olacak
  - **Yazı okuma süresi hesaplayıcı** olacak
    - Tamamen bütün cihazlara uyumlu bir **responsive tasarım** olmalıdır
    - Beğenme sistemi olmalı (sadece siteye giriş yapanlar kullanabilir)
  - **Kullanıcı profil sayfası** olacak
    - şifre ve şifre tekrarı ile şifreler sıfırlanabilecek
    - profil resmi sadece sitede belirlenmiş resimler arasından seçim yapılarak değiştirilebilecek

### Dokümantasyon
- **README.md**: Github standartlarında, kullanıcılara sunulacak şekilde sade ve anlaşılır dilde
- Kurulum sayfası içerecek
- Abartıya kaçmadan detaylı ve özlü olacak

### Proje Yapısı
- Dünya üzerinde çokça kullanılan bir dosya ve klasör yapısı kullanılmalı (Github'daki projelerde en çok kullanılan türler)

## Her Şeyden Önce Önemli Notlar

- Kullanıcılar için sadece gerekli bilgiler README.md'de yer alır, kısa ve öz olmalı
- Kurallar RULES.md dosyasında yer alır
- Kod temizliği ve güvenlik her zaman öncelik
- Performans ve kullanıcı deneyimi odaklı geliştirme
- Her şeyi bölüm bölüm yap, tekte her şeyi yapmaya kalkışma
---
name: meeting-plan
description: >
  Çevirisi biten bir toplantı kaydından eylem planı çıkarır. Rusça transkripti
  (docs/ru) kaynak alır, Türkçe çeviriyi (docs/tr) terim/isim sözlüğü olarak
  kullanır; kayıtta neyin istendiğini/kararlaştırıldığını analiz eder (action
  items, kararlar, açık sorular, sorumlular), planın hangi dilde olacağını sorar
  (TR / RU) ve docs/plans/<ad>_PLAN_<DIL>.md dosyasına yazar. Tetikleyiciler —
  "plan çıkar", "aksiyon planı yap", "kayıttan ne isteniyor", "/meeting-plan <ad>",
  "toplantıdan görevleri çıkar", çeviri bittikten sonra kullanıcı plan istediğinde.
---

# Meeting Plan (Toplantı Planı)

Amaç: çevirisi tamamlanmış bir kayıttan **eyleme dönük bir plan** üretmek — kayıtta
ne istendi, ne karar alındı, kim neyden sorumlu, neler açık kaldı. Çeviri (TR) değil,
**Rusça transkript (RU) kaynak gerçektir**; çeviri yalnızca terim ve isim tutarlılığı
için ikincil referanstır.

Bu skill `translate-meeting` çalıştıktan sonra devreye girer. Kullanıcı kararı görmeden
plan istemez — bu yüzden öneri, özet ile **aynı anda** sunulur (bkz. translate-meeting
Step 3) ve onay gelirse bu skill koşar.

## Step 0 — Dosyaları bul (preflight)

Skill kökünü bul (bu dosyanın 3 üstü: `.../meeting-translator`). Girdi olarak toplantı
**adını** (input dosyasının uzantısız basename'i, ör. `meeting1`) ya da doğrudan
`_RU.md` yolunu al. Verilmemişse, en son işlenen kaydı varsay ya da kullanıcıya sor.

1. `docs/ru/<ad>_RU.md` var mı? **Yoksa dur** — kullanıcıya "önce `/translate-meeting`
   ile transkript üret" de, sessizce çökme. Bu skill transkript üretmez.
2. `docs/tr/<ad>_TR.md` varsa onu da oku — isimler, proje adları, teknik terimler ve
   kısaltmalar için sözlük olarak kullan (planda aynı yazımı koru).

## Step 1 — Plan dilini sor

Kullanıcıya sor: **Plan hangi dilde olsun — TR mi RU mu?** Varsayılan **TR** (kullanıcının
çalışma dili); Enter / cevapsız = TR. RU yalnızca açıkça istenirse. Dili bir kez sor,
analizi bir kez yap, sonucu seçilen dile render et — iki ayrı analiz koşturma.

## Step 2 — Analiz (Claude, kaynak = RU transkript)

`docs/ru/<ad>_RU.md` dosyasını oku ve şunları çıkar:

- **Action items (yapılacaklar):** her biri için görev + sorumlu (kayıtta geçiyorsa) +
  son tarih (geçiyorsa). Sorumlu/tarih söylenmemişse **"Belirtilmedi"** yaz.
- **Alınan kararlar:** net biçimde "şu yapılacak/şu seçildi" denmiş olanlar.
- **Açık sorular / bloke konular:** karara bağlanmamış, ertelenmiş ya da birine
  sorulacak konular.

Halüsinasyona karşı sıkı kurallar (kayıtta konuşmacı etiketi yok, "kim söyledi" belirsiz):

- **Uydurma yok.** Kayıtta açıkça geçmeyen görev/karar/tarih ekleme.
- **Tartışma ≠ karar.** "Yapsak mı?" diye konuşulup reddedilen veya sonuçsuz kalan şeyi
  action item yapma; emin değilsen Açık sorular'a koy.
- Belirsiz/şüpheli yerleri `[?]` ile işaretle.
- Kayıttan hiç eylem çıkmıyorsa (bilgilendirme toplantısı) planı boş bırakma —
  "Aksiyon yok — bilgilendirme toplantısı" satırını ekle ki plan yanlışlıkla boş
  görünmesin.

## Step 3 — Planı yaz

`docs/plans/<ad>_PLAN_<DIL>.md` dosyasına kaydet (`<DIL>` = TR veya RU). `docs/plans/`
klasörü yoksa oluştur. Aynı isimli dosya zaten varsa üstüne yazmadan önce kullanıcıya
sor (farklı klasörlerden aynı isimli iki kayıt çakışabilir).

Şablon (örnek TR; RU seçilirse başlıkları Rusçaya çevir):

```markdown
# <ad> — Toplantı Planı (TR)
Oluşturulma: <tarih>
Kaynak: docs/ru/<ad>_RU.md

## Aksiyon Maddeleri
| # | Ne yapılacak | Sorumlu | Son tarih |
|---|--------------|---------|-----------|
| 1 | ...          | ...     | Belirtilmedi |

## Alınan Kararlar
- ...

## Açık Sorular
- ...
```

İsim/terim yazımında Step 0'da okunan `_TR.md`'yi referans al — orada nasıl yazıldıysa
planda da aynı yaz.

## Step 4 — Rapor

Sohbete **yalnızca Aksiyon Maddeleri tablosunu** (kısa, 5-7 satır) göster — tüm planı
sohbete dökme, kullanıcı sonsuz scroll yapmasın. Dosya yolunu ver. Plan boşsa bunu
açıkça söyle.

## Kural

- Kök-neden mantığı: kötü bir kaynak transkriptten plan çıkmaz. Transkript bozuksa
  (isimler yanlış, çok `[?]`) bunu rapor et ve `self-improve` skill'ini öner — eksik
  planı sessizce teslim etme.
- Büyük/uzun kayıtlarda bölüm bölüm analiz et ama terim ve isim tutarlılığını koru.

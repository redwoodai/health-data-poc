# Health Data PoC

Yerelde çalışan, hasta tarafından yetkilendirilen Epic/MyChart verisini SMART on FHIR ile alan Python kanıt uygulaması. Bu proje bir tıbbi cihaz değildir; sonuçları klinik karar için tek başına kullanmayın. Ham FHIR kaynakları kalıcı olarak saklanmaz ve uygulama hiçbir kullanıcı adı, parola, token veya PHI’yi loglamaz.

> **Public repository notice:** Bu repo yalnızca yerel Epic sandbox geliştirme PoC’sidir; production-ready değildir ve gerçek hasta verisiyle kullanılmamalıdır. `.env`, OAuth tokenları, authorization code’ları, client secret’lar, test hasta kimlikleri, FHIR yanıtları veya sağlık verisi ekran görüntülerini commit etmeyin. Güvenlik bildirimi için [SECURITY.md](SECURITY.md) dosyasına bakın.

## Verified Access Methods

Araştırma 11 Ağustos 2026 tarihinde, yalnızca resmî/standart kaynaklardan doğrulandı.

| Sağlayıcı | Hasta odaklı erişim var mı? | Yöntem | Kayıt gerekli mi? | Sandbox var mı? | Başlıca sınırlamalar | Resmî kaynak |
|---|---|---|---|---|---|---|
| Epic / MyChart | Evet | Hasta, MyChart oturumunda uygulamayı OAuth 2.0 SMART on FHIR ile yetkilendirir; FHIR R4 uç noktası kullanılır. | Evet; Epic sandbox için istemci kaydı, üretimde desteklenen her sağlık sistemi/dağıtım yöntemi için kayıt ve yapılandırma gerekir. | Evet | Erişilebilir kaynaklar, kapsamlar ve onay her kuruluşun politikasıyla sınırlıdır. Tek bir genel üretim FHIR sunucusu yoktur; Epic kuruluş uç noktalarını yayınlar. Epic Nexus/TEFCA IAS, ayrı bir QHIN/IAS programıdır; normal PoC yolu değildir. | [Epic Developer Resources](https://open.epic.com/DeveloperResources), [Epic R4 endpoints](https://open.epic.com/MyApps/endpoints), [Epic interoperability guide](https://open.epic.com/Home/InteroperabilityGuide?whatIWant=sandbox&whoAmI=developer) |
| Quest Diagnostics / MyQuest | Normal tüketici üçüncü taraf uygulaması için doğrulanmış genel sonuç API’si yok | Bu PoC için yok. Quest’in görünen FHIR dokümanları Quanum EHR/kurumsal kullanım; MyQuest sonuçları için kamuya açık SMART/OAuth hasta yetkilendirme akışı doğrulanmadı. | Kurumsal/iş ortağı ürünler için muhtemelen sözleşme/onay gerekir; tüketici uygulaması için yayımlanmış kayıt akışı bulunamadı. | Hasta-sonuç API’si için doğrulanmadı | Quanum EHR FHIR/bulk export ile MyQuest hasta hesabı aynı ürün değildir. Randevu API’leri laboratuvar sonuç erişimi değildir. | [Quest HCIT / FHIR isteği](https://www.questdiagnostics.com/healthcare-professionals/lab-tools-it-systems), [Quanum EHR FHIR rehberi (PDF)](https://www.questdiagnostics.com/content/dam/corporate/restricted/documents/qps_qecs/Quanum_EHR_FHIR_API.pdf), [MyQuest randevu API belgeleri](https://myquest.questdiagnostics.com/myquest-faq1/Topics/Concept/spec_orders_json_fhir_message_segments_con.htm) |

### Kesin ayrım: Quest

* **Teknik olarak mevcut:** Quest, sağlık kuruluşları için Quanum EHR ile ilgili FHIR belgeleri ve bazı randevu entegrasyonları yayımlar.
* **Onaylı iş ortağı/kurum için olası:** Quest’in “Request a FHIR API” çağrısı sağlık profesyonelleri/HCIT sayfasındadır; bunun kapsamı, sözleşmesi ve yetkisi Quest ile doğrulanmalıdır.
* **Normal hasta odaklı uygulama için doğrulanan:** MyQuest sonuçlarını hastanın OAuth onayıyla üçüncü tarafa veren açık FHIR, SMART, OAuth veya developer API bulunamadı. Bu nedenle `quest/client.py` bilerek istek yapmaz.

En gerçekçi uyumlu Quest yolu, sonuçların hastanın Epic veya başka bir sağlayıcı EHR kaydına gelmesi hâlinde o EHR’nin hasta yetkili FHIR API’sini kullanmaktır. Aksi hâlde Quest’ten yazılı olarak tüketici uygulaması/iş ortağı erişimi sorulmalıdır. Quest, MyQuest içinden hasta tarafından **elle** sonuç PDF’si indirmeyi desteklediğini belgeliyor ([PDF indirme](https://myquest.questdiagnostics.com/myquest-faq1/MyQuest/3064.htm)); gelecekte kullanıcı tarafından açıkça seçilen bir PDF içe aktarma özelliği düşünülebilir, ancak bu PoC bunu uygulamaz ve PDF indirmeyi otomatikleştirmez. Bu proje portal kazıma, tarayıcı otomasyonu, parola aktarma veya gizli uç nokta kullanmaz.

## Epic sandbox PoC

### 1. Uygulamayı kaydedin

1. [Epic on FHIR](https://fhir.epic.com/) hesabı oluşturun ve FHIR sandbox için uygulama/client kaydını tamamlayın.
2. Uygulama tipinizi hasta odaklı, standalone SMART on FHIR olarak seçin ve `http://127.0.0.1:8000/callback` redirect URI’sini kaydedin. Kayıtta verilen sandbox `client_id` değerini alın.
3. `.env.example` dosyasını `.env` olarak kopyalayın ve `EPIC_CLIENT_ID` alanını doldurun. Gerçek sırları Git’e eklemeyin.

Epic, hasta uygulamaları için OAuth 2.0 üzerinde HL7 SMART on FHIR’i destekler. SMART sunucusunun `/.well-known/smart-configuration` belgesinden yetkilendirme/token uç noktaları dinamik keşfedilir. Bu uygulama Authorization Code + S256 PKCE kullanır ve SMART v2 `aud` parametresini FHIR R4 sunucusuna bağlar; kullanıcı yalnızca Epic/MyChart sayfasında oturum açar.

### 2. Çalıştırın

```bash
cd health-data-poc
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

Tarayıcıda `http://127.0.0.1:8000/authorize` açın. Epic sandbox test hastasıyla yetkilendirdikten sonra `/data`, aşağıdakine benzer sağlayıcıdan bağımsız bir çıktı döndürür:

```json
{
  "source": "epic",
  "patient": {"source_resource_id": "...", "name": "..."},
  "labs": [{"name": "LDL Cholesterol", "value": 120, "unit": "mg/dL", "date": "...", "reference_range": "...", "source_resource_id": "..."}],
  "diagnostic_report_count": 1
}
```

Uygulama `Patient`, laboratuvar kategorili `Observation` ve `DiagnosticReport` çağrıları yapar. Ham FHIR JSON’u normalleştirilmiş laboratuvar modelinden ayrıdır ve `/data` ile döndürülmez; bu PoC onu kalıcı olarak saklamaz. Access token yalnızca süreç belleğindedir; uygulama kapanınca kaybolur. Yerel geliştirme sunucusunu ağ arayüzüne açmayın.

## Mevcut PoC durumu ve sandbox kayıt notları

11–12 Ağustos 2026 itibarıyla aşağıdakiler başarıyla tamamlandı:

1. Epic on FHIR geliştirici hesabı ve uygulama kaydı oluşturuldu; production ve non-production client ID’leri üretildi. **Bu kimlikleri, tokenları, OAuth authorization code’larını veya test-hasta verisini bu depoya/README’ye koymayın.**
2. Epic FHIR R4 sandbox SMART metadata’sı canlı doğrulandı. Authorization Code, standalone launch, public client ve S256 PKCE yeteneklerini ilan ediyor.
3. Local callback üzerinden OAuth 2.0 Authorization Code + PKCE akışı tamamlandı ve sandbox test hastası için token alındı.
4. Epic sandbox’tan `Patient`, laboratuvar `Observation` ve laboratuvar `DiagnosticReport` başarıyla çekildi; bir laboratuvar sonucu normalleştirildi.
5. Epic’in Bundle içinde gönderebildiği `OperationOutcome` uyarıları, gerçek FHIR sonuçlarıyla karıştırılmayacak şekilde filtrelendi.
6. Ham FHIR JSON’u `/data` çıktısından çıkarıldı; normalleştirilmiş model yalnızca klinik veri özeti ve `diagnostic_report_count` içerir.

### Uygulama kaydında seçilen/değiştirilmemesi gereken PoC ayarları

Bu bölüm, mevcut kodla uyumlu sandbox kaydını belgelendirir. Epic panelindeki gerçek durum farklıysa, paneldeki doğru değer esas alınır.

| Alan | PoC için değer |
|---|---|
| Application Name | `My Personal Health Vault` |
| Application Audience | `Patients` |
| Automatic Client Distribution | `USCDI v3` |
| Public Documentation URL | Public ve gerçek bir README/dokümantasyon URL’si; örnek: `https://github.com/redwoodai/health-data-poc` |
| Incoming APIs | `Patient.Read (Demographics) (R4)`, `Observation.Search (Labs) (R4)`, `DiagnosticReport.Search (Results) (R4)` |
| Sandbox endpoint URI | `http://127.0.0.1:8000/callback` |
| Dynamic clients | Kapalı |
| Confidential client | Kapalı (bu yerel PKCE PoC için) |
| SMART on FHIR Version | `R4` |
| SMART Scope Version | `SMART v2` |
| FHIR ID Generation Scheme | `Use 64-Character-Limited FHIR IDs for USCDI FHIR Resources` |
| Üretimde gereken ek URI | Gerçek, size ait `https://.../callback`; localhost URI sandbox içindir |

### Data Use Questionnaire: bu yerel PoC için doğru beyanlar

Yanıtlar her zaman gerçek uygulama davranışına göre verilmelidir. Mevcut PoC için: veri kalıcı saklanmaz; tokenlar yalnızca işlem belleğindedir; veri satılmaz/paylaşılmaz/reklam veya araştırma için kullanılmaz; kullanıcı dışındaki hiç kimse veriye erişmez; BAA yoktur; kullanıcı verisi uygulama kapandığında tutulmaz; erişim denetim günlüğü sunulmaz. Uygulamayı sunan taraf gerçekten bir LLC ise şirket türü `For-profit organization`; şirket yoksa `An individual or independent developer` olmalıdır. Finansman gerçekten yatırım/borç değil, açık kaynak/hobi çalışması ise `This app is produced by volunteers or is available in the open source community` seçilir.

## Sonraki adımlar

### Hemen tamamlanan ilk basamak: PoC temizliği

* Uygulamanın çağırdığı üç R4 API ile kayıt kapsamı eşitlendi.
* Gereksiz geniş SMART scope’lar kaldırıldı.
* OAuth callback sorgu parametrelerinin (özellikle tek kullanımlık `code`) terminal erişim loglarında görünmesi engellendi.
* Eksik FHIR `id` alanı veya Bundle `OperationOutcome` uyarısı uygulamayı çökertmez.
* Ham FHIR JSON normalleştirilmiş `/data` çıktısında gösterilmez veya saklanmaz.
* Dashboard, Epic’in token yanıtında gerçekten verdiği scope’ları “Bağlantı ve izin durumu” altında gösterir. Token geçersizleşirse uygulama güvenle yeniden yetkilendirme akışına yönlenir.

### Sıradaki uygulanabilir işler

1. **Sandbox regresyon testi:** Epic’in farklı sandbox test hastalarıyla yetkilendirme ve `Patient`/`Observation`/`DiagnosticReport` çağrılarını deneyin. Bu işlem test hesabı gerektirdiği için kullanıcı tarafından yapılmalıdır. Her testte Dashboard > “Bağlantı ve izin durumu” altında temel scope’ları doğrulayın; genişletilmiş veriler etkinleştirildiyse `Condition`, `AllergyIntolerance` ve `MedicationRequest` scope’larını da doğrulayın.
2. **Yerel kullanıcı arayüzü:** Tamamlandı. `/dashboard`, JSON yerine laboratuvar adı, değer, birim, tarih ve referans aralığını gösterir; ham FHIR JSON veya token göstermez.
3. **Ek klinik kaynaklar:** Condition, alerji ve ilaç desteği kodda hazırdır ama varsayılan olarak kapalıdır. Etkinleştirmek için Epic panelinde yalnızca şu R4 Search API’lerini ekleyin: `Condition.Search (Problems) (R4)`, `AllergyIntolerance.Search (Patient Chart) (R4)`, `MedicationRequest.Search (Signed Medication Order) (R4)`. Sandbox senkronizasyonundan sonra `.env` içine `EPIC_ENABLE_EXTENDED_CLINICAL_DATA=true` yazın, sunucuyu yeniden başlatın ve yeniden yetkilendirin. Encounter, Procedure, Immunization ve DocumentReference ileride aynı yöntemle eklenebilir.
4. **Quest yolu:** Doğrudan hasta API’si doğrulanmadığından portal otomasyonu eklenmez. Epic’e iletilen Quest sonuçları Epic FHIR’den alınır; ileri aşamada kullanıcı tarafından elle indirilen resmî Quest PDF’si için açık rızalı yerel içe aktarma tasarlanabilir.
5. **Üretim hazırlığı:** HTTPS callback/domain, gizlilik politikası, doğru Data Use Questionnaire, token kasası, şifreli depolama, hesap/MFA, silme-rıza-iptal akışları ve denetim kayıtları olmadan production sağlık verisi işlenmez.

## Public repository automation

GitHub Actions, `main`e yapılan her push ve pull request'te Python 3.11, 3.12 ve 3.13 üzerinde testleri çalıştırır. Dependabot, Python bağımlılıkları ve GitHub Actions sürümleri için aylık güncelleme önerileri açar. Bu otomasyon yalnızca kaynak kodunu ve örnek yapılandırmayı kullanır; `.env` dosyası CI'a gönderilmez.

### İstenen FHIR kaynakları ve SMART kapsamları

SMART R4’in en az ayrıcalıklı okuma/arama söz dizimi `.rs`’dir. PoC'nin varsayılan kapsamları yalnızca çalıştırdığı üç kaynağı ister. Sunucu daha dar kapsam verebilir veya bazılarını reddedebilir.

| Kaynak | İstenen scope |
|---|---|
| Patient | `patient/Patient.r` |
| Observation (laboratuvar) | `patient/Observation.rs` |
| DiagnosticReport | `patient/DiagnosticReport.rs` |
| Condition | Gelecek sürüm: `patient/Condition.rs` |
| MedicationRequest | Gelecek sürüm: `patient/MedicationRequest.rs` |
| MedicationStatement | Gelecek sürüm: `patient/MedicationStatement.rs` |
| AllergyIntolerance | Gelecek sürüm: `patient/AllergyIntolerance.rs` |
| Encounter | Gelecek sürüm: `patient/Encounter.rs` |
| Procedure | Gelecek sürüm: `patient/Procedure.rs` |
| Immunization | Gelecek sürüm: `patient/Immunization.rs` |
| DocumentReference | Gelecek sürüm: `patient/DocumentReference.rs` |

Ek bağlam/kimlik kapsamları: `launch/patient openid fhirUser`. SMART standardı, standalone uygulamada `launch/patient` ile hasta bağlamı istemeyi ve token yanıtındaki `patient` kimliğini kullanmayı tanımlar. Eski SMART v1 sunucuları `.read` kabul edebilir; bu PoC R4/SMART’ın güncel `.rs` biçimini ister. Ayrıntılar için [HL7 SMART launch](https://hl7.org/fhir/smart-app-launch/app-launch.html) ve [scope tanımı](https://hl7.org/fhir/smart-app-launch/scopes-and-launch-context.html).

### Çoklu Epic/MyChart kuruluşları

Sandbox `client_id` yalnızca sandbox içindir. Üretimde uygulama, kullanıcının bakım aldığı her kuruluşun yayımlanmış FHIR R4 uç noktasına bağlanır. Epic, yalnızca USCDI v1 veya v3 API setlerini kullanan ve teknik koşulları karşılayan belirli hasta uygulamalarının client ID’lerini auto-download etkin kuruluşlara otomatik dağıtabilir. Bu koşulları karşılamayan veya ek API isteyen uygulamalarda ilgili sağlık kuruluşu client kaydını isteyip kendi ortamına indirir/etkinleştirir. Bu sebeple PoC, tek sandbox uç noktasıyla sınırlıdır ve üretim için “bir client id her yerde kesin çalışır” varsayımı yapmaz.

Epic Nexus üzerinden TEFCA Individual Access Services, QHIN ile çalışan daha farklı bir üretim yoludur. Epic’e göre IAS istemcisi Epic Nexus’a kaydolur; buradan sağlanan kimlik tüm destekleyen katılımcılara eşitlenebilir. Bu, sıradan bağımsız uygulama kaydının yerine geçmez ve QHIN, IAL2 ve sözleşmesel gereksinimler içerir. Bkz. [Epic Nexus IAS](https://open.epic.com/Home/Interoperate/TEFCA/IAS).

## Güvenlik sınırları

* Kullanıcı adı/parola istenmez, saklanmaz veya iletilmez.
* Token, state ve PKCE verifier sadece RAM’dedir; loglara yazılmaz.
* Loglarda hasta adı, kimliği, FHIR URL parametreleri ve token bulunmaz.
* `.env` gitignore’dadır. Herhangi bir gerçek test/üretim kimliği veya PHI commit etmeyin.
* Bu demo, production token kasası, kullanıcı oturumu, veri şifreleme veya erişim denetimi içermez.

## Test

```bash
cd health-data-poc
PYTHONPATH=. python -m unittest discover -s tests -v
```

## Path from PoC to Product

HIPAA düzeyinde hasta kontrollü ürün için en azından: her sağlık sistemiyle üretim uygulama kaydı ve güvenlik incelemesi; uygun olduğu yerde BAA ve iş ortağı sözleşmeleri; güçlü kullanıcı kimlik doğrulama/MFA; şifreli depolama ve anahtar yönetimi; token kasası/rotasyonu; en az ayrıcalık/RBAC; denetlenebilir erişim kayıtları; rıza, geri alma ve veri silme akışları; güvenli SDLC, bağımsız güvenlik testleri, olay müdahalesi ve yedekleme gerekir. HIPAA kapsamı iş modeline ve ilişkili kuruluşlara göre hukuk uzmanıyla değerlendirilmelidir; hasta uygulaması olmak tek başına HIPAA uyumluluğu sağlamaz.

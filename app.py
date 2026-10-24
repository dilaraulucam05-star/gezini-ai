import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from urllib.parse import quote
import html
import math
import requests
import ast
import unicodedata
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

st.set_page_config(page_title='Gezini AI | Seyahatini Keşfet', page_icon='🌍', layout='wide', initial_sidebar_state='expanded')
ROOT = Path(__file__).resolve().parent

MONTHS = {'Ocak':1,'Şubat':2,'Mart':3,'Nisan':4,'Mayıs':5,'Haziran':6,'Temmuz':7,'Ağustos':8,'Eylül':9,'Ekim':10,'Kasım':11,'Aralık':12}
TYPES = {'Deniz ve plaj':'sahil','Doğa ve yeşil alanlar':'doga','Müze ve tarih':'muze_tarih','Şehir keşfi':'sehir_gezisi','Sakin ve huzurlu tatil':'sakinlik'}
PROVINCES = ['Adana','Adıyaman','Afyonkarahisar','Ağrı','Aksaray','Amasya','Ankara','Antalya','Ardahan','Artvin','Aydın','Balıkesir','Bartın','Batman','Bayburt','Bilecik','Bingöl','Bitlis','Bolu','Burdur','Bursa','Çanakkale','Çankırı','Çorum','Denizli','Diyarbakır','Düzce','Edirne','Elazığ','Erzincan','Erzurum','Eskişehir','Gaziantep','Giresun','Gümüşhane','Hakkâri','Hatay','Iğdır','Isparta','İstanbul','İzmir','Kahramanmaraş','Karabük','Karaman','Kars','Kastamonu','Kayseri','Kırıkkale','Kırklareli','Kırşehir','Kilis','Kocaeli','Konya','Kütahya','Malatya','Manisa','Mardin','Mersin','Muğla','Muş','Nevşehir','Niğde','Ordu','Osmaniye','Rize','Sakarya','Samsun','Şanlıurfa','Siirt','Sinop','Sivas','Şırnak','Tekirdağ','Tokat','Trabzon','Tunceli','Uşak','Van','Yalova','Yozgat','Zonguldak']

@st.cache_data
def load_data():
    city_path=ROOT/'GEZINI_ML_KUMELI_DESTINASYONLAR.csv'
    if not city_path.exists(): city_path=ROOT/'GEZINI_ANA_VERI_30_DESTINASYON_SON.csv'
    cities=pd.read_csv(city_path,encoding='utf-8-sig')
    climate_path=ROOT/'GEZINI_30_DESTINASYON_AYLIK_IKLIM.csv'
    climate=pd.read_csv(climate_path,encoding='utf-8-sig') if climate_path.exists() else pd.DataFrame()
    pricepath=ROOT/'GEZINI_KAYNAKLI_FIYAT_GOZLEMLERI.csv'
    prices=pd.read_csv(pricepath,encoding='utf-8-sig') if pricepath.exists() else pd.DataFrame()
    museums_path=ROOT/'GEZINI_MUZELER_TEKIL_SON.csv'
    museums=pd.read_csv(museums_path,encoding='utf-8-sig') if museums_path.exists() else pd.DataFrame()
    places_path=ROOT/'GEZINI_GEZI_NOKTALARI_SON.csv'
    places=pd.read_csv(places_path,encoding='utf-8-sig',dtype={'nokta_id':'string'}) if places_path.exists() else pd.DataFrame()
    if not places.empty:
        places['destinasyon']=places['destinasyon'].astype(str).str.strip()
        places['enlem']=pd.to_numeric(places['enlem'],errors='coerce')
        places['boylam']=pd.to_numeric(places['boylam'],errors='coerce')
    transit_path=ROOT/'GEZINI_ULASIM_BALIKESIR.csv'
    transit=pd.read_csv(transit_path,encoding='utf-8-sig') if transit_path.exists() else pd.DataFrame()
    # Colab'da islenen veri dosyasi onceliklidir.
    guide_path=ROOT/'GEZINI_SEHIR_OZELLIKLERI_ISLENMIS.csv'
    if not guide_path.exists():
        guide_path=ROOT/'GEZINI_30_SEHIR_REHBERI.csv'
    guide=pd.read_csv(guide_path,encoding='utf-8-sig') if guide_path.exists() else pd.DataFrame()
    if not guide.empty and 'destinasyon' in guide.columns:
        guide['destinasyon']=guide['destinasyon'].astype(str).str.strip()
    # Yillik festival bilgileri yalnızca ayrı rehber dosyasında bulunabilir.
    annual_path=ROOT/'GEZINI_30_SEHIR_REHBERI.csv'
    annual=pd.read_csv(annual_path,encoding='utf-8-sig') if annual_path.exists() else pd.DataFrame()
    event_path=ROOT/'GEZINI_ETKINLIKLER.csv'
    events=pd.read_csv(event_path,encoding='utf-8-sig') if event_path.exists() else pd.DataFrame()
    return cities,climate,prices,museums,transit,guide,annual,events,places

try:
    cities,climate,prices,museums,transit,guide,annual,events,places=load_data()
except Exception as exc:
    st.error('Veri dosyaları okunamadı. app.py ile iki ana CSV aynı Gezini klasöründe olmalı.')
    st.exception(exc)
    st.stop()

st.markdown('''<style>
:root {color-scheme: dark;}
.stApp {background:#0c1625;color:#edf5ff}
.block-container {max-width:1280px;padding-top:1.2rem;padding-bottom:4rem}
[data-testid="stSidebar"] {background:#132338;border-right:1px solid #30435b}
[data-testid="stSidebar"] *,[data-testid="stWidgetLabel"] *,[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li {color:#e5f1fc!important;opacity:1!important}
[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,[data-testid="stMarkdownContainer"] h3 {color:#f4fbff!important}
[data-testid="stCaptionContainer"] * {color:#a9bed2!important;opacity:1!important}
[data-testid="stMetricValue"],[data-testid="stMetricLabel"] {color:#eff8ff!important}
[data-testid="stAlert"] {background:#1d3450!important;color:#f4faff!important;border:1px solid #48708f!important}
[data-testid="stAlert"] * {color:#f4faff!important}
[data-testid="stForm"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#35516c!important}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {background:#158c9e!important;color:white!important;border:none!important}
.stButton button {border:1px solid #5184a4!important}
.hero {background:linear-gradient(92deg,rgba(8,26,49,.96),rgba(12,78,101,.60)),url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1800');background-size:cover;background-position:center;padding:74px 38px;border-radius:24px;margin-bottom:25px;box-shadow:0 12px 34px #0005;border:1px solid #294660}
.hero h1 {color:#fff!important;font-size:3rem;margin:0 0 14px}.hero p {color:#e4f7ff!important;font-size:1.13rem;line-height:1.7;max-width:760px}
.feature {background:#192d44;border:1px solid #3d617b;border-radius:18px;padding:22px;min-height:145px;color:#e9f7ff;box-shadow:0 4px 14px #0002}
.feature strong {color:#65dce1;font-size:1.08rem}.feature p {color:#e5f2fe!important}
.banner {background:linear-gradient(105deg,#16354a,#123444);padding:25px;border:1px solid #326c78;border-radius:20px;margin-bottom:20px;color:#e5faff}.banner h2 {color:#f4feff!important;margin:0 0 8px}
.city-top {background:#192e45;padding:14px;border-radius:14px;border:1px solid #365775;margin:8px 0 14px;color:#e5f3fc}
.city-top strong {color:#7ce0e3}
</style>''',unsafe_allow_html=True)


def compatibility(month,temp,selected_types,rain_pref):
    if not selected_types:
        raise ValueError('En az bir gezi türü seçmelisiniz.')
    month_data=climate.loc[climate['ay'].eq(month),['destinasyon_id','ortalama_sicaklik_c','ortalama_yagisli_gun']]
    data=cities.merge(month_data,on='destinasyon_id',validate='one_to_one').copy()
    if len(data)!=30:
        raise ValueError('İklim verilerinde 30 destinasyonun tamamı bulunamadı.')
    flags=[TYPES[x] for x in selected_types]
    # Eski ana etiketleri korurken Colab'da islenen etiketlerden de yararlan.
    # Yeni bir etiket, ayni ozelligi ikinci kez puanlamaz (mantiksal VEYA).
    yeni_etiketler={'sahil': ['deniz'], 'doga': ['doğa'], 'muze_tarih': ['tarih', 'kültür'], 'sehir_gezisi': ['şehir gezisi'], 'sakinlik': ['sakinlik']}
    if not guide.empty and {'destinasyon','standart_etiketler'}.issubset(guide.columns):
        extra=guide[['destinasyon','standart_etiketler']].drop_duplicates('destinasyon')
        data=data.merge(extra,on='destinasyon',how='left',validate='many_to_one')
    else:
        data['standart_etiketler']=''
    def tercih_eslesiyor(row,col):
        ana=bool(pd.to_numeric(row.get(col,0),errors='coerce')==1)
        tags={t.strip().casefold() for t in str(row.get('standart_etiketler','')).split(',')}
        return ana or any(tag in tags for tag in yeni_etiketler.get(col,[]))
    matched=sum(data.apply(lambda row: int(tercih_eslesiyor(row,col)),axis=1) for col in flags)
    data['gezi_puani']=30*matched/len(flags)
    difference=(data['ortalama_sicaklik_c']-temp).abs()
    data['sicaklik_puani']=20*(1-difference/12).clip(lower=0)
    if rain_pref=='Az yağış istiyorum':
        data['yagis_puani']=10*(1-data['ortalama_yagisli_gun']/8).clip(lower=0)
    elif rain_pref=='Orta düzey yağış olabilir':
        data['yagis_puani']=10*(1-data['ortalama_yagisli_gun']/12).clip(lower=0)
    else:
        data['yagis_puani']=10.0
    data['uyum']=(100*(data['gezi_puani']+data['sicaklik_puani']+data['yagis_puani'])/60).round(1).clip(0,100)
    return data.sort_values('uyum',ascending=False).reset_index(drop=True)

# === GEZINI AI | CANLI DOVIZ, BUTCE, ML BENZERLIK VE HAVA ===
@st.cache_data(ttl=21600, show_spinner=False)
def guncel_usd_kuru():
    """Ucretsiz referans kur; gercek piyasa/banka satis kuru olmayabilir."""
    try:
        yanit = requests.get('https://api.frankfurter.dev/v1/latest',
                            params={'base':'USD','symbols':'TRY'}, timeout=5)
        yanit.raise_for_status()
        veri=yanit.json()
        kur=float(veri['rates']['TRY'])
        if not 1 < kur < 500:
            raise ValueError('Gecersiz kur')
        return kur, f"Frankfurter referans kuru, veri tarihi: {veri.get('date','bilinmiyor')}"
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None, 'Canlı döviz kuru alınamadı.'


def butce_hesapla(sehir, gun, gece, kisi, seviye, kur):
    """Kaynak CSV'deki SENARYO fiyatlarıyla, toplam grup için kısmi gider hesaplar.
    İki kişilik oda tabanlı satırlarda tek kişi de tam oda fiyatı öder;
    hostel yatak bazlı satırlarda kişi başı ücret uygulanır.
    """
    onek = 'ekonomik' if seviye=='Ekonomik' else 'orta'
    alanlar = [f'{onek}_konaklama_kisi_gece',f'{onek}_yemek_kisi_gun',
               f'{onek}_toplu_tasima_kisi_gun']
    degerler=[pd.to_numeric(sehir.get(s),errors='coerce') for s in alanlar]
    if any(pd.isna(v) or v < 0 for v in degerler):
        return None
    para_birimi=str(sehir.get('para_birimi','')).strip()
    if para_birimi=='TRY': carp=1.0
    elif para_birimi=='USD' and kur is not None and kur>0: carp=float(kur)
    else: return None
    konaklama_kisi_gece,yemek_kisi_gun,yerel_kisi_gun=map(float,degerler)
    tur=str(sehir.get(f'{onek}_konaklama_turu','')).casefold()
    if 'hostel' in tur and 'yatak' in tur:
        yatak_sayisi=kisi
        konaklama_birim='Kişi başı hostel yatağı'
    else:
        # Kaynak kişi-gece tutarını çift kişilik oda / 2 üzerinden veriyor.
        yatak_sayisi=2*math.ceil(kisi/2)
        konaklama_birim=f'{math.ceil(kisi/2)} çift kişilik oda varsayımı'
    konaklama=konaklama_kisi_gece*gece*yatak_sayisi*carp
    yemek=yemek_kisi_gun*gun*kisi*carp
    yerel=yerel_kisi_gun*gun*kisi*carp
    toplam=round(konaklama)+round(yemek)+round(yerel)
    return {'konaklama':round(konaklama), 'yemek':round(yemek),
            'sehir_ici_ulasim':round(yerel),'toplam':round(toplam),
            'konaklama_birim':konaklama_birim, 'para_birimi':para_birimi,
            'senaryo': 'Prototip tahmini; fiyat teklifi / rezervasyon fiyatı değil'}


def makine_ogrenmesi_benzerligi(data, temp, selected_types, rain_pref):
    """scikit-learn NearestNeighbors: eğitimli etiket değil, özellik yakınlığı.
    30 şehir veri seti üstünde gerçek sklearn fit/kneighbors çağrısı yapılır.
    """
    try:
        import numpy as np
        from sklearn.neighbors import NearestNeighbors
    except ImportError:
        data['ml_benzerlik'] = float('nan')
        return data, False
    etiketler=['sahil','doga','muze_tarih','sehir_gezisi','sakinlik']
    ilave={'sahil': ['deniz'], 'doga': ['doğa'], 'muze_tarih': ['tarih','kültür'],
           'sehir_gezisi':['şehir gezisi'],'sakinlik':['sakinlik']}
    ozellik=[]
    for _, satir in data.iterrows():
        tags={t.strip().casefold() for t in str(satir.get('standart_etiketler','')).split(',')}
        etiket=[float(pd.to_numeric(satir.get(k,0),errors='coerce')==1 or any(t in tags for t in ilave[k]))
                for k in etiketler]
        aylik_yagis=float(satir['ortalama_yagisli_gun'])
        ozellik.append([v*0.8 for v in etiket]+[float(satir['ortalama_sicaklik_c'])/12, aylik_yagis/10])
    X=np.asarray(ozellik,dtype=float)
    secilen={TYPES[s] for s in selected_types}
    hedef=[float(k in secilen)*0.8 for k in etiketler]
    yagis_hedef=3 if rain_pref=='Az yağış istiyorum' else 7 if rain_pref=='Orta düzey yağış olabilir' else 0
    if rain_pref=='Yağış fark etmez':
        X[:,-1]=0.0
    hedef=np.asarray([hedef+[float(temp)/12, yagis_hedef/10]],dtype=float)
    model=NearestNeighbors(n_neighbors=len(X),metric='euclidean')
    model.fit(X)
    uzaklik, indis=model.kneighbors(hedef)
    puanlar=np.zeros(len(X))
    puanlar[indis[0]]=100/(1+uzaklik[0])
    data['ml_benzerlik']=np.round(puanlar,1)
    return data, True


@st.cache_data(ttl=3600, show_spinner=False)
def open_meteo_hava(enlem, boylam):
    """Open-Meteo gerçek HTTP API çağrısı; saatlik cache."""
    params={'latitude':float(enlem),'longitude':float(boylam),
            'current':'temperature_2m,weather_code,wind_speed_10m',
            'daily':'temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum',
            'forecast_days':16,'timezone':'auto'}
    r=requests.get('https://api.open-meteo.com/v1/forecast',params=params,timeout=7)
    r.raise_for_status()
    return r.json()


def canli_hava_goster(satir, baslangic, gun):
    st.markdown('### 🌦️ Canlı hava durumu — Open-Meteo')
    try:
        veri=open_meteo_hava(satir['enlem'],satir['boylam'])
    except (requests.RequestException, ValueError, KeyError, TypeError) as hata:
        st.warning('Güncel hava durumu alınamadı. İklim ortalamaları hava tahmini değildir.')
        return
    suan=veri.get('current',{})
    st.write(f"**Şu an:** {suan.get('temperature_2m','?')} °C  ·  Rüzgâr: {suan.get('wind_speed_10m','?')} km/sa")
    st.caption(f"API ölçüm zamanı: {suan.get('time','bilinmiyor')} (şehrin yerel saati). Kaynak: Open-Meteo")
    gunluk=veri.get('daily',{})
    tarihler=gunluk.get('time',[])
    son=baslangic+timedelta(days=int(gun)-1)
    satirlar=[]
    for i, t in enumerate(tarihler):
        try: dt=date.fromisoformat(t)
        except ValueError: continue
        if baslangic<=dt<=son:
            def eleman(alan):
                v=gunluk.get(alan,[])
                return v[i] if i<len(v) else None
            satirlar.append({'Tarih':dt.strftime('%d.%m.%Y'),
                              'En düşük (°C)':eleman('temperature_2m_min'),
                              'En yüksek (°C)':eleman('temperature_2m_max'),
                              'Yağış olasılığı (%)':eleman('precipitation_probability_max'),
                              'Yağış (mm)':eleman('precipitation_sum')})
    if satirlar:
        st.dataframe(pd.DataFrame(satirlar),hide_index=True,width='stretch')
        if len(satirlar)<gun:
            st.info('Seyahatin yalnızca tahmin ufkundaki günleri gösterildi. Diğer günler için kesin hava tahmini mevcut değil.')
    else:
        st.info('Seyahat tarihiniz tahmin aralığının dışında. Mevsimsel iklim ortalamalarını yukarıdan inceleyebilirsiniz; bunlar canlı tahmin değildir.')


def tl_yaz(tutar):
    return f'{tutar:,.0f} TL'.replace(',','.')



# --- Resmî tatiller: Nager.Date Community API (ülke/bölge düzeyi) ---
COUNTRY_CODES = {
    'Türkiye':'TR', 'Fransa':'FR', 'İtalya':'IT', 'İspanya':'ES',
    'Hollanda':'NL', 'Birleşik Krallık':'GB', 'Almanya':'DE',
    'Yunanistan':'GR', 'Portekiz':'PT', 'Birleşik Arap Emirlikleri':'AE',
    'Japonya':'JP', 'Tayland':'TH', 'Endonezya':'ID', 'ABD':'US',
    'Mısır':'EG', 'Fas':'MA'
}
# Yalnızca güvenilir biçimde eşleştirebildiğimiz 1. seviye bölgeler.
CITY_SUBDIVISIONS = {'Berlin':'DE-BE', 'New York':'US-NY', 'Miami':'US-FL',
                     'Barselona':'ES-CT', 'Madrid':'ES-MD'}

@st.cache_data(ttl=86400, show_spinner=False)
def resmi_tatilleri_getir(country_code, year):
    """API başarısız olursa None döner. Boş liste: API veri döndürdü, tatil bulamadı.
    Önce güncel v4, API erişilemiyorsa eski v3 denenir.
    """
    endpoints = [
        f'https://nagerholidays.com/api/v4/Holidays/{country_code}/{year}',
        f'https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}'
    ]
    for endpoint in endpoints:
        try:
            response=requests.get(endpoint,timeout=8)
            response.raise_for_status()
            payload=response.json()
            if isinstance(payload,list):
                return payload
        except (requests.RequestException, ValueError, TypeError):
            pass
    return None


def seyahat_tatilleri(destinasyon, ulke, baslangic, gun_sayisi):
    """(uygulanabilir tatiller, durum). Resmî tatil -> müze kapanışı çıkarımı yapmaz."""
    kod=COUNTRY_CODES.get(str(ulke).strip())
    if not kod:
        return [], 'ülke eşleştirmesi bulunamadı'
    bitis=baslangic+timedelta(days=int(gun_sayisi)-1)
    bolge=CITY_SUBDIVISIONS.get(str(destinasyon).strip())
    sonuc=[]
    for yil in range(baslangic.year,bitis.year+1):
        yanit=resmi_tatilleri_getir(kod,yil)
        if yanit is None:
            return [], 'resmî tatil servisine erişilemedi'
        for kayit in yanit:
            try:
                gun=date.fromisoformat(str(kayit['date']))
            except (KeyError,ValueError,TypeError):
                continue
            if not baslangic <= gun <= bitis:
                continue
            turler=kayit.get('holidayTypes', kayit.get('types',[])) or []
            if turler and 'Public' not in turler:
                continue
            ulusal=kayit.get('nationalHoliday',kayit.get('global',False))
            bolgeler=kayit.get('subdivisionCodes',kayit.get('counties',[])) or []
            if not ulusal and (not bolge or bolge not in bolgeler):
                continue
            ad=str(kayit.get('localName') or kayit.get('name') or 'Resmî tatil')
            sonuc.append((gun,ad))
    return sorted(set(sonuc)), 'kontrol edildi'


@st.cache_data(show_spinner=False)
def festival_takvimi_oku():
    dosya=ROOT/'GEZINI_FESTIVAL_TAKVIMI.csv'
    if not dosya.exists():
        return pd.DataFrame()
    return pd.read_csv(dosya,encoding='utf-8-sig')


def tarihli_festivaller(destinasyon, baslangic, gun_sayisi):
    # Sadece kaynağı ve tarihi belirtilmiş, yerel/yıllık teyit statülü kayıtlar.
    tablo=festival_takvimi_oku()
    alanlar={'destinasyon','etkinlik_adi','baslangic','bitis','kaynak_url'}
    if tablo.empty or not alanlar.issubset(tablo.columns):
        return []
    son=baslangic+timedelta(days=int(gun_sayisi)-1)
    bulunan=[]
    for _,k in tablo[tablo['destinasyon'].eq(destinasyon)].iterrows():
        try:
            ilk=date.fromisoformat(str(k['baslangic']))
            son_gun=date.fromisoformat(str(k['bitis']))
        except ValueError:
            continue
        kaynak=str(k.get('kaynak_url',''))
        if ilk<=son and son_gun>=baslangic and kaynak.startswith('https://'):
            bulunan.append(k.to_dict())
    return bulunan


def festival_uyarisi_goster(destinasyon, baslangic, gun_sayisi, kompakt=False):
    eslesen=tarihli_festivaller(destinasyon,baslangic,gun_sayisi)
    if not eslesen:
        return
    if kompakt:
        adlar=', '.join(str(f['etkinlik_adi']) for f in eslesen[:2])
        st.info('🎉 Seçtiğin tarihlerde etkinlik / festival dönemi: '+adlar+'. Yoğunluk veya ulaşım değişikliği olabilir; kapanışlar otomatik doğrulanmış değildir.')
        return
    st.markdown('### 🎉 Tarihine denk gelen festival ve etkinlikler')
    for f in eslesen:
        ilk=date.fromisoformat(str(f['baslangic']))
        son=date.fromisoformat(str(f['bitis']))
        takvim=ilk.strftime('%d.%m.%Y') if ilk==son else f"{ilk.strftime('%d.%m.%Y')} – {son.strftime('%d.%m.%Y')}"
        st.write(f"**{f['etkinlik_adi']}** · {takvim}")
        st.caption(str(f.get('dogrulama_durumu','')))
        st.write(str(f.get('etki_notu','')))
        st.markdown(f"[Etkinliğin kaynak sayfası]({f['kaynak_url']})")
    st.caption('Festival tarihleri ve açılış saatleri değişebilir. Bir festivalin olması, bütün müzelerin kapalı olduğu anlamına gelmez.')


def tatil_uyarisi_goster(destinasyon, ulke, baslangic, gun_sayisi, kompakt=False):
    tatiller, durum=seyahat_tatilleri(destinasyon,ulke,baslangic,gun_sayisi)
    if durum!='kontrol edildi':
        if not kompakt:
            st.info('📅 Resmî tatil verisi doğrulanamadı ('+durum+'). Gideceğiniz yerin yerel tatil takvimine bakın.')
        return
    if not tatiller:
        if not kompakt:
            st.caption('📅 Ulusal düzeyde eşleşen resmî tatil bulunamadı. Şehre özel günler ve müzelerin açılış saatleri ayrıca kontrol edilmeli.')
        return
    if kompakt:
        st.warning('📅 Seyahat tarihlerinde resmî tatil: '+', '.join(g.strftime('%d.%m.%Y')+' '+ad for g,ad in tatiller[:3])+'. Müze ve dükkânların çalışma saatleri değişebilir; gezi tarihini değerlendirirken bunu göz önünde bulundur.')
    else:
        st.markdown(f'### 📅 {ulke} — seyahat tarihlerindeki resmî tatiller')
        for gun, ad in tatiller:
            st.write('**'+gun.strftime('%d.%m.%Y')+'** — '+ad)
        st.warning('⚠️ Bu tarihlerde bazı mağaza, restoran ve müzelerin saatleri değişebilir veya bazıları kapalı olabilir. Özellikle müze ağırlıklı gezi için bu günleri yeniden değerlendirmek iyi olabilir. Ancak **tüm müzeler kapalı** demek doğru değildir; her mekânın resmî sitesinden kontrol edin.')
        st.caption('Kaynak: Nager.Date tatil takvimi (ülke/bölge düzeyi); yerel tatiller ve müze kapanışları eksik olabilir.')



# --- Gezi planlayıcısı: mevcut müze verileri, tarih ve hava durumuna dayalı. ---
def sade_metin(deger):
    return ''.join(k for k in unicodedata.normalize('NFKD', str(deger).casefold()) if not unicodedata.combining(k)).replace('ı','i')


def kaynak_muze_ayrintisi(kayit):
    try:
        detay=ast.literal_eval(str(kayit.get('orijinal_bilgiler','{}')))
        if not isinstance(detay,dict): detay={}
    except (SyntaxError, ValueError, TypeError):
        detay={}
    koord={}
    for alan,deger in detay.items():
        temiz=sade_metin(alan)
        if 'enlem' in temiz and deger: koord['lat']=deger
        if 'boylam' in temiz and deger: koord['lon']=deger
    try:
        lat,lon=float(koord['lat']),float(koord['lon'])
        if not(-90<=lat<=90 and -180<=lon<=180): raise ValueError
    except (ValueError,TypeError,KeyError):
        lat=lon=None
    durumlar=[str(deger) for alan,deger in detay.items()
              if ('ziyaret_durumu' in sade_metin(alan) or 'ziyaret durumu' in sade_metin(alan)) and deger]
    kapalilik=any('kapali' in sade_metin(durum) for durum in durumlar)
    kapali_gunler=[]
    for alan,deger in detay.items():
        anahtar=sade_metin(alan)
        if ('kapali gun' in anahtar or 'haftalik kapali' in anahtar or 'kapali_gun' in anahtar):
            kapali_gunler.append(sade_metin(deger))
    return {'ad':str(kayit['muze_adi']), 'adres':str(kayit.get('adres','')) if pd.notna(kayit.get('adres')) else '',
            'kaynak':str(kayit.get('resmi_kaynak','')) if pd.notna(kayit.get('resmi_kaynak')) else '',
            'lat':lat,'lon':lon,'kapali':kapalilik,'kapali_gunler':kapali_gunler,
            'saatler':str(detay.get('ziyaret_saatleri_ayrintili') or detay.get('Açılış saati') or
                           detay.get('Açılış') or detay.get('acilis_saati') or '').strip()}


def muze_o_gun_uygun(mu, gun):
    if mu['kapali']: return False
    haftanin_gunu=['pazartesi','sali','carsamba','persembe','cuma','cumartesi','pazar'][gun.weekday()]
    for kapanis in mu['kapali_gunler']:
        if haftanin_gunu in kapanis and 'her gun acik' not in kapanis:
            return False
    return True


def iki_nokta_km(a,b):
    if any(x is None for x in (a['lat'],a['lon'],b['lat'],b['lon'])): return None
    from math import radians,sin,cos,asin,sqrt
    lat1,lon1,lat2,lon2=map(radians,[a['lat'],a['lon'],b['lat'],b['lon']])
    dlat=lat2-lat1; dlon=lon2-lon1
    h=sin(dlat/2)**2+cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371*2*asin(min(1,sqrt(h)))


def gunluk_hava_haritasi(sehir_satiri,baslangic,gun_sayisi):
    """Yalnızca API'nin gerçekten döndürdüğü günler; diğer tarihlere tahmin yok."""
    try:
        veri=open_meteo_hava(sehir_satiri['enlem'],sehir_satiri['boylam'])
        daily=veri.get('daily',{})
    except (requests.RequestException, ValueError, TypeError,KeyError):
        return {}
    result={}
    son=baslangic+timedelta(days=int(gun_sayisi)-1)
    for i,ds in enumerate(daily.get('time',[])):
        try: dt=date.fromisoformat(ds)
        except (ValueError,TypeError): continue
        if baslangic<=dt<=son:
            def at(alan):
                items=daily.get(alan,[])
                return items[i] if i<len(items) else None
            result[dt]={'rain_pct':at('precipitation_probability_max'),
                        'rain_mm':at('precipitation_sum'),
                        'max_temp':at('temperature_2m_max')}
    return result




def gezi_yerleri_kayitlari(destinasyon):
    """Kaynaklı gezi adayları. Konum doğruluğu ziyaret saatlerinin doğrulandığı anlamına gelmez."""
    if places.empty:
        return []
    alt=places[places['destinasyon'].eq(destinasyon)]
    sonuc=[]
    for _,p in alt.iterrows():
        name=str(p.get('nokta_adi') or '').strip()
        if (not name or name.casefold()=='nan' or
                sade_metin(name).strip(' ()') in {'sans titre','untitled','unknown','inconnu','no name'}):
            continue
        try:
            lat=float(p['enlem']); lon=float(p['boylam'])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError()
        except (ValueError,TypeError,KeyError):
            lat=lon=None
        k=str(p.get('kategori') or '')
        ty=str(p.get('veri_turu') or '')
        indoor=('Müze' in k or 'galeri' in k.lower() or 'sergi' in k.lower())
        outdoor=any(tag in sade_metin(k) for tag in ('park','doga','plaj','seyir','meydan','carsi','hayvanat','arkeolojik'))
        # Anıt ve tarihî yapıların iç/dış mekân durumu kaynaktan kesinleşmez.
        # Bunlar açık günler için tercih edilebilir; yağmurlu günlere zorla önerilmez.
        if not indoor and not outdoor:
            outdoor=any(tag in sade_metin(k) for tag in ('tarih','anit','turistik','kalinti','kale'))
        kaynak=str(p.get('kaynak_url') or '').strip()
        if kaynak.lower()=='nan': kaynak=''
        saat=str(p.get('ziyaret_saatleri') or '').strip()
        if saat.lower()=='nan': saat=''
        kapali=str(p.get('haftalik_kapali_gun') or '').strip()
        if kapali.lower()=='nan': kapali=''
        notlar=str(p.get('onemli_not') or '').strip()
        if notlar.lower()=='nan': notlar=''
        sonuc.append({'ad':name,'kategori':k,'veri_turu':ty,'kaynak':kaynak,
                      'lat':lat,'lon':lon,'saatler':saat,'kapali_gunler':[sade_metin(kapali)] if kapali else [],
                      'kapali':False,'adres':str(p.get('adres') or '').replace('nan','').strip(),
                      'indoor':indoor,'outdoor':outdoor,'onemli_not':notlar,
                      'resmi':ty=='MÜZE_KAYDI','dogrulama':'Ziyaret saatlerini ve erişimi resmî kaynaktan kontrol edin.'})
    return sonuc


def kategori_uyumu(p,turler,yagmur):
    """Tek bir şehrin aday sayısı sıralama avantajı oluşturmaz."""
    cat=sade_metin(p['kategori'])
    uyum=0
    if 'Müze ve tarih' in turler and any(x in cat for x in ('muze','tarih','arkeolojik','anit','galeri','kalinti')): uyum+=5
    if 'Deniz ve plaj' in turler and 'plaj' in cat: uyum+=6
    if 'Doğa ve yeşil alanlar' in turler and any(x in cat for x in ('park','doga','seyir')): uyum+=6
    if 'Şehir keşfi' in turler and any(x in cat for x in ('meydan','carsi','turistik','anit','tarih')): uyum+=3
    if 'Sakin ve huzurlu tatil' in turler and any(x in cat for x in ('park','doga','seyir','plaj')): uyum+=3
    if yagmur:
        uyum+=7 if p['indoor'] else -9
    elif p['outdoor']:
        uyum+=3
    if p['lat'] is not None: uyum+=2
    if p['veri_turu']=='MÜZE_KAYDI': uyum+=3
    elif p['veri_turu']=='WIKIPEDIA_ADAY': uyum-=1
    return uyum


def gezi_yerleri_goster(destinasyon,adet=8):
    """Şehirde müzeye ek park, plaj, açık alan ve tarihî yer adaylarını sun."""
    items=gezi_yerleri_kayitlari(destinasyon)
    if not items:
        st.caption('Bu şehir için ek gezilecek yer verisi bulunamadı.')
        return
    # Kalabalık bir kategorinin tüm örnekleri kaplamaması için kategori çeşitliliği.
    gruplar={}
    for p in items:
        gruplar.setdefault(p['kategori'],[]).append(p)
    for k in gruplar:
        gruplar[k].sort(key=lambda p:(p['veri_turu']=='WIKIPEDIA_ADAY',p['lat'] is None,p['ad']))
    sec=[]
    while len(sec)<adet and any(gruplar.values()):
        for k in sorted(gruplar):
            if gruplar[k] and len(sec)<adet: sec.append(gruplar[k].pop(0))
    st.markdown(f'**📍 {destinasyon} — gezilecek yer örnekleri**')
    st.caption(f'Kayıtlı {len(items)} yer arasından farklı türlerde {len(sec)} örnek gösteriliyor.')
    for p in sec:
        st.markdown('• **'+p['ad']+'** · '+p['kategori'])
        if p['kaynak'].startswith(('https://','http://')): st.markdown(f"[Yer ve kaynak bilgisi]({p['kaynak']})")
    st.caption('© OpenStreetMap katkıda bulunanlar (ODbL)')


def gunluk_program_olustur(destinasyon,ulke,baslangic,gun_sayisi,turler,hava):
    """Çeşitli gezi yerlerini ilgi ve yağışa göre sıralar; resmî açık olma iddiasında bulunmaz."""
    adaylar=gezi_yerleri_kayitlari(destinasyon)
    if not adaylar and not museums.empty:
        adaylar=[dict(kaynak_muze_ayrintisi(mu),kategori='Müze/kültür',veri_turu='MÜZE_KAYDI',indoor=True,outdoor=False)
                 for _,mu in museums[museums['destinasyon'].eq(destinasyon)].iterrows()]
    secilen=set()
    resmiler,_=seyahat_tatilleri(destinasyon,ulke,baslangic,gun_sayisi)
    tatil_gunleri={g:ad for g,ad in resmiler}
    plan=[]
    rehber=guide[guide['destinasyon'].eq(destinasyon)] if not guide.empty else pd.DataFrame()
    rehber_aktivite=''
    if not rehber.empty:
        a=rehber.iloc[0].get('ornek_aktivite')
        if pd.notna(a): rehber_aktivite=str(a).strip()
    for i in range(int(gun_sayisi)):
        gun=baslangic+timedelta(days=i)
        h=hava.get(gun,{})
        try: yagmur=float(h.get('rain_pct'))>=60 or float(h.get('rain_mm'))>=4
        except (ValueError,TypeError): yagmur=False
        uygun=[p for p in adaylar if (p['ad'].casefold() not in secilen and muze_o_gun_uygun(p,gun))]
        # Yağış durumunda mümkünse iç mekân adayları, açık havada kullanıcı tercihi önce gelir.
        uygun.sort(key=lambda p:(-kategori_uyumu(p,turler,yagmur),p['ad'].casefold()))
        yakin=[]
        kapasite=3
        for slot in range(kapasite):
            if not uygun: break
            if slot==0:
                yeni=uygun[0]
            else:
                yakin_mesafe=[(iki_nokta_km(yakin[-1],m), m) for m in uygun[:40]]
                yakin_mesafe=[(d,m) for d,m in yakin_mesafe if d is not None]
                # Öncelikle aynı uygunluk bandında yakın yer seç; uzak şehir uçlarına gitme.
                yakin_mesafe=[(d,m) for d,m in yakin_mesafe if d<=8 and
                              kategori_uyumu(m,turler,yagmur)>=kategori_uyumu(uygun[0],turler,yagmur)-3]
                yeni=min(yakin_mesafe,key=lambda pair:pair[0])[1] if yakin_mesafe else uygun[0]
            yakin.append(yeni)
            secilen.add(yeni['ad'].casefold())
            uygun.remove(yeni)
        notlar=[]
        if gun in tatil_gunleri:
            notlar.append(f'Resmî tatil: {tatil_gunleri[gun]}. Ziyaret noktalarının saatlerini resmî sitelerden doğrulayın.')
        festivaller=tarihli_festivaller(destinasyon,gun,1)
        if festivaller:
            notlar.append('Bu güne denk gelen etkinlik: '+', '.join(str(f['etkinlik_adi']) for f in festivaller))
        if yagmur:
            notlar.append('Yağış olasılığı yüksek: mümkün olduğunca iç mekân seçeneklerine öncelik verildi. Seçilen yerlerin kapalı alan sunduğunu ve açık olduğunu kontrol edin.')
        elif h:
            notlar.append('Hava tahmini mevcut: açık hava etkinlikleri için güncel koşulları kontrol edin.')
        else:
            notlar.append('Bu tarih için güncel hava tahmini yok; planın hava koşullarına uygunluğu doğrulanmadı.')
        if len(yakin)>1 and iki_nokta_km(yakin[0],yakin[1]) is not None:
            km=iki_nokta_km(yakin[0],yakin[1])
            if km<=8: notlar.append('İlk iki nokta kuş uçuşu birbirine yakın; gerçek ulaşım süresi hesaplanmadı.')
        if rehber_aktivite and i==0: notlar.append('Şehir rehberinden genel aktivite fikri: '+rehber_aktivite)
        if any(p['veri_turu']=='WIKIPEDIA_ADAY' for p in yakin):
            notlar.append('Wikipedia kaynaklı noktalar araştırma adayıdır; ziyaret edilebilirlikleri teyit edilmemiştir.')
        if not yakin: notlar.append('Bu güne uygun başka kayıt kalmadı; yeni yer uydurulmadı.')
        plan.append({'gun':gun,'no':i+1,'muzeler':yakin,'notlar':notlar,'hava':h})
    return plan


def seyahat_kontrol_listesi(ulke,gun_sayisi,turler,hava):
    secenekler=['Kimlik ve gerekli seyahat belgelerini kontrol et',
               'Konaklama rezervasyon bilgilerini kaydet',
               'Gidiş-dönüş ulaşım seçeneklerini ve saatlerini kontrol et',
               'Telefon, şarj aleti ve uygun priz adaptörünü hazırla',
               'Ziyaret edilecek müzelerin resmî saatlerini yeniden kontrol et',
               'Acil iletişim bilgilerini ve varsa düzenli ilaçlarını hazırla']
    if ulke!='Türkiye':
        secenekler+=['Pasaport geçerlilik süresini kontrol et',
                    'Vize/giriş koşullarını resmî konsolosluk kaynaklarından doğrula',
                    'Seyahat sağlık sigortası koşullarını kontrol et',
                    'Yurt dışı mobil hat, ödeme yöntemi ve döviz planını kontrol et']
    if 'Deniz ve plaj' in turler: secenekler.append('Mayo, güneş koruyucu ve plaj malzemelerini hazırla')
    if 'Doğa ve yeşil alanlar' in turler: secenekler.append('Yürüyüş ayakkabısı ve doğa etkinliği ekipmanını hazırla')
    if any((v.get('rain_pct') is not None and float(v['rain_pct'])>=60) for v in hava.values()):
        secenekler.append('Yağmurluk veya şemsiyeni hazırla')
    return secenekler


def plan_pdf_baytlari(sehir,ulke,baslangic,gun_sayisi,butce,plan,checklist,bitmis):
    """Türkçe karakter destekli, dış API gerektirmeyen indirilebilir PDF."""
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    import os
    font_candidates=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'arial.ttf',
                     Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font='Helvetica'
    for fontfile in font_candidates:
        if fontfile.exists():
            try:
                if 'GeziniFont' not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont('GeziniFont',str(fontfile)))
                font='GeziniFont'
                break
            except Exception:
                pass
    def p(t): return xml_escape(str(t))
    b=BytesIO()
    doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    style=getSampleStyleSheet()
    style.add(ParagraphStyle(name='GeziniTitle',fontName=font,fontSize=17,leading=24,textColor=colors.HexColor('#12465B'),spaceAfter=10,alignment=TA_CENTER))
    style.add(ParagraphStyle(name='GeziniHead',fontName=font,fontSize=12,leading=17,textColor=colors.HexColor('#12465B'),spaceBefore=15,spaceAfter=6))
    style.add(ParagraphStyle(name='GeziniText',fontName=font,fontSize=9.5,leading=14,spaceAfter=5))
    stt=[]
    stt.append(Paragraph('GEZİNİ – SEYAHAT PLANIM',style['GeziniTitle']))
    stt.append(Paragraph(p(f'{sehir} / {ulke}  ·  {baslangic:%d.%m.%Y}  ·  {gun_sayisi} gün'),style['GeziniText']))
    stt.append(Paragraph(p(f'Kullanıcının belirlediği bütçe: {tl_yaz(butce)}'),style['GeziniText']))
    stt.append(Paragraph('Plan öneri niteliğindedir. Açılış, ücret ve tatil günü kapanışları için resmî kaynakları kontrol edin. Bütçeye gidiş-dönüş biletleri, müze, etkinlik ve vize ücretleri dahil değildir.',style['GeziniText']))
    for d in plan:
        section=[Paragraph(p(f"{d['no']}. Gün – {d['gun']:%d.%m.%Y}"),style['GeziniHead'])]
        if d['muzeler']:
            for m in d['muzeler']:
                section.append(Paragraph(p('• '+m['ad']+' ('+m.get('kategori','Gezi noktası')+')'+((' — '+m['adres']) if m['adres'] else '')),style['GeziniText']))
        else:
            section.append(Paragraph('• Serbest zaman / yerel kaynaklardan ek gezi noktası araştırın.',style['GeziniText']))
        for n in d['notlar']:
            section.append(Paragraph(p('– '+n),style['GeziniText']))
        stt.append(KeepTogether(section))
    hazirlik=[Paragraph('SEYAHAT ÖNCESİ HAZIRLIK',style['GeziniHead'])]
    for i,item in enumerate(checklist):
        hazirlik.append(Paragraph(p(('✓ ' if i in bitmis else '☐ ')+item),style['GeziniText']))
    stt.append(KeepTogether(hazirlik))
    stt.append(Spacer(1,10))
    stt.append(Paragraph('Gezini AI · Planda müze ve gezi noktası veri setleri ile erişilebildiğinde güncel hava/tatil API verileri kullanılmıştır. © OpenStreetMap contributors (ODbL). Wikipedia kayıtları ziyaret adayıdır.',style['GeziniText']))
    doc.build(stt)
    return b.getvalue()


def akilli_plan_ve_pdf_goster(satir, secim):
    sehir=str(satir['destinasyon']); ulke=str(satir['ulke'])
    baslangic=date.fromisoformat(secim['start_date'])
    gun_sayisi=int(secim['days'])
    st.markdown('### 🗺️ Gezilebilecek yerler')
    st.caption('Seçtiğin şehir için önerilen gezilecek yerler aşağıda listelenmiştir.')
    hava=gunluk_hava_haritasi(satir,baslangic,gun_sayisi)
    turler=secim.get('types',[])
    plan=gunluk_program_olustur(sehir,ulke,baslangic,gun_sayisi,turler,hava)
    gorulen=set()
    gezi_listesi=[]
    for d in plan:
        for m in d['muzeler']:
            anahtar=m['ad'].casefold()
            if anahtar not in gorulen:
                gorulen.add(anahtar)
                gezi_listesi.append(m)
    if gezi_listesi:
        for m in gezi_listesi:
            st.write(('🏛️ ' if m.get('indoor') else '📍 ')+m['ad']+' · '+m.get('kategori','Gezi noktası'))
            if m['kaynak'].startswith(('https://','http://')):
                st.markdown(f"[Kaynak sayfası]({m['kaynak']})")
    else:
        st.info('Bu şehir için listelenecek uygun gezi noktası bulunamadı.')
    st.markdown('### 🎒 Seyahat öncesi hazırlık listen')
    st.caption('Tamamladıklarını işaretleyebilirsin. Liste vize veya giriş hakkını doğrulamaz.')
    checklist=seyahat_kontrol_listesi(ulke,gun_sayisi,turler,hava)
    bitmis=set()
    for i,metin in enumerate(checklist):
        k=f"gezini_prep_{sehir}_{baslangic.isoformat()}_{i}"
        if st.checkbox(metin,key=k): bitmis.add(i)
    st.markdown('### 📄 Planını PDF olarak kaydet')
    try:
        pdf=plan_pdf_baytlari(sehir,ulke,baslangic,gun_sayisi,secim['budget'],plan,checklist,bitmis)
        st.download_button('📥 Gezi planımı indir (PDF)',data=pdf,
                           file_name=f"Gezini_{baslangic.isoformat()}_Gezi_Plani.pdf",
                           mime='application/pdf',width='stretch')
    except (ImportError, OSError, ValueError) as hata:
        st.warning('PDF oluşturulamadı. GEZINI_KUTUPHANELERI_KUR.bat dosyasını çalıştırarak reportlab kütüphanesini kur.')


def konaklama_arama_baglantilari(destinasyon):
    st.markdown('### 🏨 Konaklama seçeneklerini karşılaştır')
    st.write('**'+str(destinasyon)+'** için otelleri, hostelleri ve fiyatları aşağıdaki sitelerde inceleyebilirsin.')
    a,b=st.columns(2)
    with a:
        st.link_button('🔎 Google Hotels’ta ara','https://www.google.com/travel/hotels',width='stretch')
    with b:
        st.link_button('🏨 Booking.com’da ara','https://www.booking.com/',width='stretch')
    st.caption('Bağlantılar genel otel arama sayfalarını açar. Şehir, tarihler ve kişi sayısını ilgili sitede seçin. Gezini bu sitelerin canlı fiyatlarını çekmez veya rezervasyon yapmaz; toplam tutarı ödeme öncesinde doğrulayın.')

def sehir_rehberi_goster(destinasyon):
    if guide.empty or 'destinasyon' not in guide:
        return
    matches=guide[guide['destinasyon'].eq(destinasyon)]
    if matches.empty:
        return
    g=matches.iloc[0]
    def alan(ad):
        value=g.get(ad, '')
        return str(value).strip() if pd.notna(value) and str(value).strip() else ''
    st.markdown('### 🌍 Şehri tanı')
    a,b=st.columns(2)
    with a:
        aylar=alan('genel_rehber_aylari') or alan('onerilen_aylar')
        if aylar:
            st.markdown('**🗓️ Genel gezi için önerilen aylar**')
            st.write(aylar)
        st.markdown('**✨ Şehir özellikleri**')
        st.write(alan('sehir_ozellikleri') or 'Bilgi eklenmemiş')
        st.markdown('**📍 Öne çıkan**')
        st.write(alan('one_cikan') or 'Bilgi eklenmemiş')
    with b:
        st.markdown('**🧳 Kimler için ideal?**')
        st.write(alan('onerilen_gezginler') or 'Bilgi eklenmemiş')
        st.markdown('**🚶 Yapılabilecek aktivite**')
        st.write(alan('ornek_aktivite') or 'Bilgi eklenmemiş')
        st.markdown('**🗓️ Önerilen kalış süresi**')
        st.write(f"{alan('onerilen_sure_gun')} gün" if alan('onerilen_sure_gun') else 'Bilgi eklenmemiş')
    st.caption('Önerilen aylar genel gezi rehberi bilgisidir; seçtiğin tarihin hava tahmini değildir.')


def muze_listesi(destinasyon, adet=5):
    """Mevcut 293 kayıttan şehir bazlı müze seçimi; giriş ve açılış bilgileri canlı değil."""
    if museums.empty:
        return pd.DataFrame()
    kayit=museums[museums['destinasyon'].eq(destinasyon)].copy()
    if kayit.empty:
        return kayit
    return kayit.drop_duplicates('muze_adi').sort_values('muze_adi').head(adet)


def muzelere_bak(destinasyon, adet=5):
    kayit=muze_listesi(destinasyon,adet)
    if kayit.empty:
        st.caption('Bu şehir için müze verisi yüklenmedi.')
        return
    st.markdown(f'**🏛️ {destinasyon} için müze önerileri** ({len(kayit)} örnek)')
    st.caption('Kaydedilmiş müzelerden şehir eşleşmesine göre listelenir. Açılış saatleri, giriş ücretleri ve açık olma durumu ziyaret öncesinde resmî kaynaktan kontrol edilmelidir.')
    for _,m in kayit.iterrows():
        st.markdown(f'**• {m["muze_adi"]}**')
        if pd.notna(m.get('adres')) and str(m['adres']).strip():
            st.caption(str(m['adres']))
        kaynak=m.get('resmi_kaynak')
        if pd.notna(kaynak) and str(kaynak).startswith(('https://','http://')):
            st.markdown(f'[Müzenin kaynak sayfası]({kaynak})')


def ulasim_onerisi(cikis, destinasyon, ulke, tercih):
    # Rota tarifesi veya dogrudan sefer iddiasinda bulunmaz.
    if cikis==destinasyon and ulke=='Türkiye':
        return 'Aynı şehirde: toplu taşıma / yürüyüş seçeneklerini değerlendirin.'
    if tercih!='Fark etmez':
        return f'Önceliğiniz: {tercih}. Bu rota için sefer, aktarma ve fiyat henüz doğrulanmadı.'
    if ulke!='Türkiye':
        return 'Ön inceleme: uçak ve gerekirse aktarmalı bağlantıları araştırın. Balıkesir çıkışlı doğrudan uçuş varsayılmıyor.'
    return 'Ön inceleme: otobüs ve uygun havaalanı varsa uçak seçeneklerini karşılaştırın. Rota/sefer henüz doğrulanmadı.'


def ulasim_kayitlari(destinasyon, cikis):
    if transit.empty or cikis!='Balıkesir':
        return pd.DataFrame()
    gerek={'destinasyon','ulasim_turu'}
    if not gerek.issubset(transit.columns):
        return pd.DataFrame()
    sonuc=transit[transit['destinasyon'].eq(destinasyon)].copy()
    if 'veri_durumu' in sonuc:
        sonuc=sonuc[sonuc['veri_durumu'].ne('DOGRULAMA_BEKLIYOR')]
    return sonuc


def route_guide(origin,dest,country,preference):
    """Practical route guidance, not claiming schedules, routes or fares are verified."""
    if origin==dest and country=='Türkiye':
        return ['Aynı şehir içindesiniz; yerel ulaşım veya yürüyüşü değerlendirin.']
    if country=='Türkiye':
        return [f'1. {origin} ilinden {dest} yönüne otobüs seçeneklerini ve aktarmaları araştırın.',
                '2. Uçak tercih ediyorsanız çıkış iline yakın havalimanını ve hedef şehre ulaşımı karşılaştırın.',
                '3. Ulaşım tercihinize ve tarihe göre gidiş/dönüş biletlerini ayrı kontrol edin.']
    if origin=='Balıkesir' and dest=='Amsterdam':
        return ['1. Balıkesir’den İstanbul’daki uygun havalimanına kara yoluyla ulaşımı planlayın (güzergâh ve saat kontrol edilmeli).',
                '2. İstanbul çıkışlı Amsterdam Schiphol (AMS) uçuşlarını ve varsa aktarmaları karşılaştırın.',
                '3. Schiphol’den Amsterdam şehir merkezine tren veya otobüs bağlantısını kontrol edin.',
                '4. Dönüşte de aynı üç yolculuk bölümünün masrafını hesaba katın.']
    return [f'1. {origin} ilinden dış hat uçuşu için uygun bir havalimanına ulaşımı planlayın.',
            f'2. {dest} için direkt veya aktarmalı uçak seçeneklerini karşılaştırın; direkt sefer olduğu varsayılmıyor.',
            '3. Varış havalimanından şehir merkezine ulaşımı ve dönüşü ayrıca bütçelendirin.']


CITY_PHOTOS = {
 'İstanbul':'photo-1524231757912-21f4fe3a7200', 'Antalya':'photo-1507525428034-b723cf961d3e',
 'Kapadokya':'photo-1570939274717-7eda259b50ed','İzmir':'photo-1500534623283-312aade485b7',
 'Fethiye':'photo-1501785888041-af3ef285b470','Bodrum':'photo-1507525428034-b723cf961d3e',
 'Trabzon':'photo-1470770841072-f978cf4d019e','Bursa':'photo-1467269204594-9661b134dd2b',
 'Çanakkale':'photo-1519681393784-d120267933ba','Pamukkale':'photo-1500530855697-b586d89ba3ee',
 'Paris':'photo-1502602898657-3e91760cbb34','Roma':'photo-1552832230-c0197dd311b5',
 'Barselona':'photo-1539037116277-4db20889f2d4','Madrid':'photo-1543783207-ec64e4d95325',
 'Amsterdam':'photo-1534351590666-13e3e0bf8d3b','Londra':'photo-1513635269975-59663e0ac1ad',
 'Berlin':'photo-1560969184-10fe8719e047','Venedik':'photo-1514890547357-a9ee288728e0',
 'Atina':'photo-1555993539-1732b0258235','Lizbon':'photo-1555881400-74d7acaacd8b',
 'Dubai':'photo-1512453979798-5ea266f8880c','Tokyo':'photo-1540959733332-eab4deabeeaf',
 'Kyoto':'photo-1493976040374-85c8e12f0c0e','Bangkok':'photo-1508004680771-708b02aabdc0',
 'Phuket':'photo-1507525428034-b723cf961d3e','Bali':'photo-1537996194471-e657df975ab4',
 'New York':'photo-1486325212027-8081e485255e','Miami':'photo-1533105079780-92b9be482077',
 'Kahire':'photo-1539768942893-daf53e448371','Marakeş':'photo-1489749798305-4fea3ae63d43'
}

def photo_for(dest):
    image_id=CITY_PHOTOS.get(dest,'photo-1467269204594-9661b134dd2b')
    return f'https://images.unsplash.com/{image_id}?w=1100&q=85'

def show_transport_links(origin,dest,country,preference):
    st.markdown('### 🧭 Ulaşım ve bilet arama')
    for step in route_guide(origin,dest,country,preference):
        st.write(step)
    if country != 'Türkiye':
        st.caption('Yurt dışı rotalarında pasaport, vize, havalimanı ve transfer koşullarını ayrıca kontrol edin.')
    # Sağlayıcının genel arama sayfası: tarihli sefer bulunduğu iddia edilmez.
    if preference in ('Otobüs','Fark etmez'):
        st.link_button('🚌 Obilet’te otobüs ara', 'https://www.obilet.com/otobus-bileti')
    if preference in ('Uçak','Fark etmez'):
        st.link_button('✈️ Google Flights’ta uçak ara','https://www.google.com/travel/flights?hl=tr')
    if dest=='Amsterdam':
        st.markdown('[🚆 Schiphol → şehir merkezi ulaşımı](https://www.schiphol.nl/en/page/transport/)')
    st.caption('Bağlantılar arama sayfalarını açar; doğrudan sefer, bilet fiyatı veya koltuk uygunluğu garanti edilmez.')

def show_festivals(dest,start_date,days):
    end_date=start_date+timedelta(days=int(days)-1)
    shown=False
    # Yalnızca gerçek tarih, kaynak ve şehir bilgisi içeren isteğe bağlı dosya.
    if not events.empty and {'destinasyon','etkinlik_adi','tarih','kaynak_url'}.issubset(events.columns):
        subset=events[events['destinasyon'].astype(str).str.strip().eq(dest)].copy()
        subset['tarih']=pd.to_datetime(subset['tarih'],errors='coerce').dt.date
        subset=subset[subset['tarih'].between(start_date,end_date) & subset['kaynak_url'].astype(str).str.startswith(('https://','http://'))]
        if not subset.empty:
            st.markdown('### 🎉 Seyahat tarihindeki etkinlikler')
            for _,e in subset.iterrows():
                st.markdown(f'**{html.escape(str(e["etkinlik_adi"]))}** · {e["tarih"].strftime("%d.%m.%Y")}')
                if pd.notna(e.get('mekan')): st.write('📍',str(e['mekan']))
                st.markdown(f'[Resmî/ilan edilen kaynak]({str(e["kaynak_url"])})')
            st.caption('Tarih ve saatler değişebilir; seyahatten önce kaynak sayfalarını yeniden kontrol edin.')
            shown=True
    if not annual.empty and {'destinasyon','yillik_etkinlik','etkinlik_donemi'}.issubset(annual.columns):
        hit=annual[annual['destinasyon'].astype(str).str.strip().eq(dest)]
        if not hit.empty:
            a=hit.iloc[0]
            title=a.get('yillik_etkinlik')
            period=a.get('etkinlik_donemi')
            if pd.notna(title) and str(title).strip() and pd.notna(period):
                period_text=str(period)
                normalized=period_text.casefold()
                month_names={1:'ocak',2:'şubat',3:'mart',4:'nisan',5:'mayıs',6:'haziran',7:'temmuz',8:'ağustos',9:'eylül',10:'ekim',11:'kasım',12:'aralık'}
                selected_months={((start_date.month-1+i)%12)+1 for i in range((end_date.year-start_date.year)*12+end_date.month-start_date.month+1)}
                matches=any(month_names[m] in normalized for m in selected_months)
                # 'Sonbahar' gibi genel ifadeyi kesin tarih gibi gösterme.
                tarihliler=tarihli_festivaller(dest,start_date,days)
                ayni_bilgi=any(str(title).casefold() in str(k['etkinlik_adi']).casefold() or str(k['etkinlik_adi']).casefold() in str(title).casefold() for k in tarihliler)
                if matches and not ayni_bilgi:
                    if not shown: st.markdown('### 🎊 Yıllık festival ve etkinlik bilgisi')
                    st.write(f'**{title}** · Genel dönem: {period_text}')
                    st.caption('Şehir rehberi taslağından alınmıştır. Bu yıl düzenleneceği veya seyahat gününe denk geldiği doğrulanmamıştır.')
                    shown=True
    return shown

with st.sidebar:
    st.title('🌍 GEZİNİ')
    st.write('Seyahatini keşfet, sana uygun rotayı bul.')
    page=st.radio('Menü',['🏠 Ana Sayfa','✨ Seyahat Planla','🧭 Destinasyonlar','🏛️ Müzeler','📍 Gezilecek Yerler','ℹ️ Hakkında'])
    st.divider()

if page=='🏠 Ana Sayfa':
    st.markdown('<div class="hero"><h1>🌍 Dünyayı Gezini ile Keşfet</h1><p>Ne kadar bütçen var? Kaç günün var? Nasıl bir hava istiyorsun? Birkaç soruya cevap ver; Gezini sana uygun rotaları karşılaştırsın.</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.metric('Destinasyon',int(cities['destinasyon_id'].nunique()))
    b.metric('Aylık iklim kaydı',len(climate))
    c.metric('Şehir rehberi',f'{len(guide)} destinasyon')
    st.subheader('Gezini ile neler yapabilirsin?')
    x,y,z=st.columns(3)
    with x: st.markdown('<div class="feature"><strong>🎯 Akıllı eşleşme</strong><p>İlgi alanı, sıcaklık ve yağış tercihlerini birlikte değerlendir.</p></div>',unsafe_allow_html=True)
    with y: st.markdown('<div class="feature"><strong>🌤️ İklim bilgisi</strong><p>2016–2025 döneminin aylık iklim ortalamalarını incele.</p></div>',unsafe_allow_html=True)
    with z: st.markdown('<div class="feature"><strong>💰 Bütçeni planla</strong><p>Konaklama, yemek ve şehir içi ulaşım için yaklaşık giderleri karşılaştır.</p></div>',unsafe_allow_html=True)
    st.caption(f'📍 Gezilecek yer kaydı: {len(places)} · Müze kaydı: {len(museums)}' if not places.empty else 'Gezilecek yer veri dosyası yüklenmedi.')
    st.caption('Gezilecek yer verileri açık kaynaklardan derlenmiştir. © OpenStreetMap katkıda bulunanlar (ODbL).')
    st.subheader('🌍 İlham Veren Rotalar')
    st.caption('Şehirler, tarihî sokaklar ve doğa manzaralarından seçmeler.')
    # Fotoğraflar yalnızca ana sayfada sergilenir; öneri ve seyahat planı ekranında gösterilmez.
    vitrin = [
        ('Paris', '🇫🇷 Paris · Eyfel Kulesi'),
        ('Amsterdam', '🇳🇱 Amsterdam · Kanallar'),
        ('Roma', '🇮🇹 Roma · Tarihî sokaklar'),
        ('Kapadokya', '🎈 Kapadokya · Vadiler'),
        ('Tokyo', '🇯🇵 Tokyo · Şehir ışıkları'),
        ('Venedik', '🇮🇹 Venedik · Kanallar'),
        ('Bali', '🌿 Bali · Tropikal doğa'),
        ('Dubai', '🇦🇪 Dubai · Şehir manzarası'),
        ('Barselona', '🇪🇸 Barselona · Mimari'),
    ]
    for baslangic in range(0, len(vitrin), 3):
        kolonlar = st.columns(3, gap='medium')
        for kolon, (sehir, aciklama) in zip(kolonlar, vitrin[baslangic:baslangic+3]):
            with kolon:
                st.image(photo_for(sehir), caption=aciklama, width='stretch')
    st.info('Başlamak için sol menüden “✨ Seyahat Planla” bölümünü seç.')

elif page=='✨ Seyahat Planla':
    st.markdown('<div class="banner"><h2>✨ Sana En Uygun Seyahati Bulalım</h2>Tercihlerini aşağıdaki sorularla belirle; destinasyonların sana hangi açıdan uyduğunu gösterelim.</div>',unsafe_allow_html=True)
    with st.form('travel_form'):
        st.subheader('💰 1. Bütçe ve süre')
        a,b,c=st.columns(3)
        with a: budget=st.number_input('Toplam seyahat bütçeniz kaç TL?',min_value=1000,value=20000,step=500)
        with b: days=st.number_input('Tatiliniz kaç gün sürecek?',min_value=1,max_value=60,value=5,step=1)
        with c: people=st.number_input('Kaç kişi seyahat edeceksiniz?',min_value=1,max_value=20,value=1,step=1)
        x,y=st.columns(2)
        with x: nights=st.number_input('Kaç gece konaklayacaksınız?',min_value=0,max_value=59,value=4,step=1)
        with y: level=st.selectbox('Maliyet planı',['Ekonomik','Orta'])
        st.caption('Otel hesaplaması: kişi/gece fiyatı, oda paylaşımı ve gece sayısına göre yapılır. Fiyatlar tarihli rezervasyon teklifi değildir.')
        st.divider()
        st.subheader('🚌 2. Çıkış noktası ve yolculuk')
        origin=st.selectbox('Hangi ilden yola çıkacaksınız?',PROVINCES,index=PROVINCES.index('Balıkesir'))
        transport=st.radio('Hangi ulaşım türünü tercih edersiniz?',['Otobüs','Uçak','Fark etmez'],horizontal=True)
        st.caption('💡 Bütçe hesabına şehirler arası gidiş-dönüş ulaşım, müze girişleri, etkinlikler ve vize ücretleri dahil değildir. Bu giderleri ayrıca planlamalısınız.')
        st.divider()
        st.subheader('🌤️ 3. Hava koşulları ve tarih')
        a,b=st.columns(2)
        with a:
            start_date=st.date_input('Seyahat başlangıç tarihiniz',value=date.today(),min_value=date.today())
            month_name=next(k for k,v in MONTHS.items() if v==start_date.month)
            st.caption(f'Seyahat ayı: {month_name} · Seyahat bitişi gün sayısına göre hesaplanır.')
            target_temp=st.slider('İdeal ortalama sıcaklık kaç °C olsun?',min_value=-10,max_value=45,value=24)
        with b:
            rain_preference=st.radio('Yağış tercihiniz nedir?',['Az yağış istiyorum','Orta düzey yağış olabilir','Yağış fark etmez'])
            st.caption('Not: Verimiz yağış olasılığı (%) değil, ayda ortalama yağışlı gün sayısıdır.')
        st.divider()
        st.subheader('🏖️ 4. Tatil türü')
        travel_types=st.multiselect('Hangi tür yerleri gezmek istersiniz?',list(TYPES),default=['Deniz ve plaj','Doğa ve yeşil alanlar'])
        submit=st.form_submit_button('🌍 Bana uygun destinasyonları göster',type='primary',width='stretch')
    if submit:
        if not travel_types:
            st.warning('Lütfen en az bir gezi türü seçin.')
        elif climate.empty:
            st.error('Aylık iklim veri dosyası eksik. Doğrulanmamış verilerle öneri yapılmaz.')
        elif nights>days:
            st.warning('Konaklama gecesi sayısı seyahat gününü aşamaz.')
        else:
            results=compatibility(MONTHS[month_name],target_temp,travel_types,rain_preference)
            # Gerçek scikit-learn komşuluk araması: yalnızca yüklenmişse aktiftir.
            results, ml_aktif=makine_ogrenmesi_benzerligi(results,target_temp,travel_types,rain_preference)
            if ml_aktif:
                results['siralama_puani']=(results['uyum']*0.65+results['ml_benzerlik']*0.35).round(1)
            else:
                results['siralama_puani']=results['uyum']
            kur,kur_notu=guncel_usd_kuru()
            # Kur alınamazsa USD fiyatlardan TL maliyet uydurulmaz.
            # 30 şehrin TAMAMINI bütçeyle karşılaştır; sadece üst 3'e sonradan filtre uygulama.
            hesaplardi=[]
            for _,r in results.iterrows():
                fiyat=butce_hesapla(r,int(days),int(nights),int(people),level,kur)
                hesaplardi.append(fiyat)
            results['butce_tutari']=[x['toplam'] if x else float('nan') for x in hesaplardi]
            results['butce_durumu']=['Hesaplanan kalemler bütçe altında (kesin değil)' if x and x['toplam']<=budget else
                                    'Tahmini temel giderler bütçeyi aşıyor' if x else
                                    'Maliyet hesaplanamadı' for x in hesaplardi]
            # Bütçeye sığanlar ilk grupta, sonra benzerlik puanına göre sıralanır.
            results['butce_sirasi']=results['butce_durumu'].map({'Hesaplanan kalemler bütçe altında (kesin değil)':0,
                'Tahmini temel giderler bütçeyi aşıyor':1, 'Maliyet hesaplanamadı':2})
            results=results.sort_values(['butce_sirasi','siralama_puani'],ascending=[True,False])
            st.session_state['gezini_results']=results.head(3).to_dict('records')
            st.session_state['gezini_asimlar']=results[results['butce_sirasi']==1].head(8).to_dict('records')
            st.session_state['gezini_query']={'budget':budget,'days':days,'nights':nights,
               'people':people,'origin':origin,'transport':transport,'month':month_name,
               'start_date':start_date.isoformat(),'types':list(travel_types),'level':level,
               'kur':kur,'kur_notu':kur_notu,'ml_aktif':ml_aktif}
            st.session_state['gezini_selected']=None
    if st.session_state.get('gezini_results'):
        q=st.session_state['gezini_query']
        st.subheader('🏆 Sana önerilen şehirler')
        st.caption('💰 Bütçe karşılaştırması yaklaşık konaklama, yemek ve şehir içi ulaşım giderlerine dayanır. Gidiş-dönüş biletleri, müze, etkinlik ve vize ücretleri dahil değildir. Fiyatlar güncel rezervasyon teklifi değildir.')
        if not q['ml_aktif']:
            st.warning('Gelişmiş öneri sistemi şu anda kullanılamıyor; şehirleri yine de tercihlerine göre karşılaştırabiliyoruz.')
        else:
            with st.expander('ℹ️ Neden bu şehirler önerildi?'):
                st.caption('Gezini; sevdiğin tatil türlerini, sıcaklık ve yağış tercihlerini şehirlerin özellikleriyle karşılaştırır. Gösterilen yüzde bir uyum göstergesidir; kesin memnuniyet garantisi değildir. Bütçe uygunluğu ayrıca değerlendirilir.')
        if q['kur'] is None:
            st.warning('Güncel USD/TL kuru alınamadığı için bazı yurt dışı şehirlerinin TL maliyetlerini hesaplayamıyoruz. Kur verisi tekrar erişilebilir olduğunda sistem otomatik hesaplayacaktır; tahmini kur uydurulmaz.')
        else:
            st.caption('Yurt dışı giderleri güncel referans kur kullanılarak TL’ye çevrilir. Ödeme sırasında kur değişebilir.')
        uygun_sayisi=sum(r['butce_durumu']=='Hesaplanan kalemler bütçe altında (kesin değil)' for r in st.session_state['gezini_results'])
        if not uygun_sayisi:
            st.warning('Önerilen şehirlerde temel giderler bile sınırı aşıyor olabilir. Hiçbir şehir için doğrulanmış, eksiksiz toplam maliyet mevcut değil.')
        for idx,r in enumerate(st.session_state['gezini_results'][:3]):
            with st.container(border=True):
                col1,col2=st.columns([4,1])
                with col1:
                    st.subheader(f'{idx+1}. {r["destinasyon"]} — {r["ulke"]}')
                    st.markdown(f'### %{r["siralama_puani"]:.0f}')
                    st.progress(float(r['siralama_puani'])/100)
                    if pd.notna(r.get('butce_tutari')):
                        st.write(f"**💰 Tahmini gider: {tl_yaz(r['butce_tutari'])}** · Bütçen: {tl_yaz(q['budget'])}")
                    else:
                        st.write('**💰 Maliyet:** güncel döviz kuru / fiyat bulunamadı')
                    # Bütçe durumu sıralama için arka planda kullanılır; ziyaretçiye uzun teknik etiket gösterilmez.
                    st.caption('Konaklama, yemek ve şehir içi ulaşım için yaklaşık hesaplamadır. Gidiş-dönüş biletleri, müzeler, etkinlikler ve vize dahil değildir.')
                    st.caption(f"Aylık iklim ortalaması: {r['ortalama_sicaklik_c']:.1f} °C · Yağışlı gün/ay: {r['ortalama_yagisli_gun']:.1f}")
                with col2:
                    if st.button('✅ Bu şehri seç',key=f'choose_{idx}',width='stretch'):
                        st.session_state['gezini_selected']=r['destinasyon']
                with st.expander('🔎 Gider ayrıntıları'):
                    fiyat=butce_hesapla(r,q['days'],q['nights'],q['people'],q['level'],q['kur'])
                    if fiyat:
                        st.write(f"🏨 Konaklama: **{tl_yaz(fiyat['konaklama'])}** · {fiyat['konaklama_birim']}")
                        st.write(f"🍽️ Yemek: **{tl_yaz(fiyat['yemek'])}**")
                        st.write(f"🚇 Şehir içi: **{tl_yaz(fiyat['sehir_ici_ulasim'])}**")
                        st.caption('Gidiş-dönüş ulaşım, müze/etkinlik, vize ve diğer ek masraflar toplama dahil değildir.')
                        st.write(f"**Yalnızca hesaplanan giderler toplamı: {tl_yaz(fiyat['toplam'])}**")
                        st.caption(f"{q['days']} gün · {q['nights']} gece · {q['people']} kişi · {q['level']} bütçe planı. Rakamlar yaklaşık olup güncel otel teklifi değildir.")
                    else: st.warning('Maliyet hesaplamak için veri veya kur eksik.')
                tatil_uyarisi_goster(r['destinasyon'],r['ulke'],date.fromisoformat(q['start_date']),q['days'],kompakt=True)
                festival_uyarisi_goster(r['destinasyon'],date.fromisoformat(q['start_date']),q['days'],kompakt=True)
                with st.expander('🏛️ Burada gezebileceğin müzeler'):
                    muzelere_bak(r['destinasyon'],5)
                    gezi_yerleri_goster(r['destinasyon'],6)
        if st.session_state.get('gezini_asimlar'):
            with st.expander('🔍 Bütçeyi aşan diğer şehirleri incele'):
                for r in st.session_state['gezini_asimlar']:
                    if r['destinasyon'] not in [s['destinasyon'] for s in st.session_state['gezini_results']]:
                        st.write(f"{r['destinasyon']} — {tl_yaz(r['butce_tutari'])} temel gider · bütçe dışı")
        selected=st.session_state.get('gezini_selected')
        if selected:
            row=next((r for r in st.session_state['gezini_results'] if r['destinasyon']==selected),None)
            if row is not None:
                st.divider()
                st.title(f'🧳 {selected} Seyahat Planın')
                st.markdown(f'<div class="city-top">✅ <strong>{html.escape(selected)}</strong> seçildi. {html.escape(q["origin"])} çıkışlı seyahatine ait şehir rehberi ve ulaşım bağlantıları aşağıda.</div>',unsafe_allow_html=True)
                canli_hava_goster(row,date.fromisoformat(q['start_date']),q['days'])
                tatil_uyarisi_goster(selected,row['ulke'],date.fromisoformat(q['start_date']),q['days'])
                festival_uyarisi_goster(selected,date.fromisoformat(q['start_date']),q['days'])
                sehir_rehberi_goster(selected)
                muzelere_bak(selected,6)
                gezi_yerleri_goster(selected,8)
                show_festivals(selected,date.fromisoformat(q['start_date']),q['days'])
                show_transport_links(q['origin'],selected,row['ulke'],q['transport'])
                konaklama_arama_baglantilari(selected)
                st.divider()
                akilli_plan_ve_pdf_goster(row,q)

elif page=='🧭 Destinasyonlar':
    st.title('🧭 Destinasyonları Keşfet')
    countries=sorted(cities['ulke'].dropna().unique().tolist())
    country=st.selectbox('Hangi ülkeye bakmak istersiniz?',['Tümü']+countries)
    selected=cities if country=='Tümü' else cities[cities['ulke'].eq(country)]
    st.caption(f'{len(selected)} destinasyon')
    for _,row in selected.iterrows():
        with st.expander(f'📍 {row["destinasyon"]} — {row["ulke"]}'):
            st.image(photo_for(row['destinasyon']),width='stretch')
            tags=[label for label,column in TYPES.items() if row[column]==1]
            st.write('Gezi türleri:',', '.join(tags) if tags else 'Etiket yok')
            sehir_rehberi_goster(row['destinasyon'])
            muzelere_bak(row['destinasyon'],4)
            gezi_yerleri_goster(row['destinasyon'],5)

elif page=='📍 Gezilecek Yerler':
    st.title('📍 Gezilecek Yerleri Keşfet')
    st.caption('30 destinasyondaki müze, tarihî yapı, park, plaj ve diğer noktaları keşfedebilirsin.')
    if places.empty:
        st.warning('Gezilecek yer dosyası bulunamadı.')
    else:
        c1,c2=st.columns(2)
        with c1:
            city=st.selectbox('Şehir',sorted(places['destinasyon'].dropna().unique()),key='gezini_all_places_city')
        sub=places[places['destinasyon'].eq(city)].copy()
        with c2:
            cat=st.selectbox('Yer türü',['Tümü']+sorted(sub['kategori'].dropna().unique().tolist()),key='gezini_all_places_cat')
        if cat!='Tümü': sub=sub[sub['kategori'].eq(cat)]
        keyword=st.text_input('Yer adı ara (isteğe bağlı)',key='gezini_all_places_search')
        if keyword.strip():
            sub=sub[sub['nokta_adi'].fillna('').astype(str).str.contains(keyword.strip(),case=False,regex=False)]
        sub=sub.sort_values(['veri_turu','nokta_adi'],kind='stable')
        st.write(f'**{len(sub)} kayıt bulundu.** İlk 25 kayıt gösteriliyor.')
        for _,loc in sub.head(25).iterrows():
            st.markdown('**📍 '+str(loc['nokta_adi'])+'** · '+str(loc['kategori']))
            if str(loc['veri_turu'])=='WIKIPEDIA_ADAY':
                st.caption('Kaynak türü: Wikipedia')
            else:
                st.caption('Kaynak türü: Konum / müze kaydı')
            url=loc.get('kaynak_url')
            if pd.notna(url) and str(url).startswith(('https://','http://')):
                st.markdown(f'[Kaynağı görüntüle]({url})')
        st.caption('© OpenStreetMap katkıda bulunanlar (ODbL).')

elif page=='🏛️ Müzeler':
    st.title('🏛️ Gezini Müze Rehberi')
    if museums.empty:
        st.warning('GEZINI_MUZELER_TEKIL_SON.csv dosyasını Gezini klasörüne kopyalayın.')
    else:
        st.write(f'Kayıtlı {len(museums)} tekil müze için şehir bazlı arama. Ayrıca {len(places)} gezilecek yer kaydı bulunuyor.')
        yer=st.selectbox('Hangi destinasyonun müzelerini görmek istersiniz?', sorted(museums['destinasyon'].dropna().unique().tolist()))
        arama=st.text_input('Müze adında ara (isteğe bağlı)')
        secilen=museums[museums['destinasyon'].eq(yer)].copy()
        if arama.strip():
            secilen=secilen[secilen['muze_adi'].astype(str).str.contains(arama,case=False,regex=False,na=False)]
        st.caption(f'{len(secilen)} müze bulundu. Ziyaret saatleri ve ücretleri güncel olmayabilir.')
        for _,m in secilen.iterrows():
            with st.container(border=True):
                st.markdown(f'**🏛️ {m["muze_adi"]}**')
                if pd.notna(m.get('adres')) and str(m['adres']).strip():
                    st.write('📍',m['adres'])
                kaynak=m.get('resmi_kaynak')
                if pd.notna(kaynak) and str(kaynak).startswith(('https://','http://')):
                    st.markdown(f'[Kaynak / müze bilgileri]({kaynak})')


else:
    st.title('ℹ️ Gezini Hakkında')
    st.write('Gezini, seyahat tercihlerini karşılaştırarak destinasyon öneren üniversite projesidir.')
    st.write('Şehir rehberimiz, iklim bilgileri, müzeler ve gezi noktalarıyla gezini planlamana yardımcı olur. Tarihi doğrulanmış etkinlikler seyahat dönemine göre gösterilir; genel festival dönemleri kesin tarih anlamına gelmez.')
    st.write('Gezini; tatil tercihlerin, şehirlerin özellikleri ve iklim koşullarına göre sana uygun rotaları karşılaştırır. Konaklama, yemek ve şehir içi ulaşım için yaklaşık bütçe hesabı sunar. Gidiş-dönüş ulaşım, müze, etkinlik ve vize giderleri bu hesaba dahil değildir. Güncel hava durumu, resmî tatil uyarıları, festival takvimi, müze rehberi ve konaklama arama bağlantılarıyla seyahatini planlamana yardımcı olur. Fiyatları ve ziyaret saatlerini rezervasyon veya ziyaret öncesinde ilgili kaynaktan kontrol etmelisin.')

st.divider()
st.caption('Gezini AI · Bütçeler yaklaşık hesaplamadır · İklim ortalamaları güncel hava tahmini değildir · Tatil günlerinde mekân saatlerini kontrol et.')

# ARCHATIA

ARCHATIA je desktop aplikacija za prepoznavanje arhitektonskih stilova na temelju fotografije građevine. Aplikacija koristi lokalni AI model CLIP za usporedbu slike s opisima arhitektonskih stilova te korisniku prikazuje najvjerojatnije rezultate, postotak pouzdanosti i osnovne informacije o prepoznatim stilovima.

Projekt je izrađen kao praktična aplikacija s grafičkim sučeljem, lokalnom obradom slike i jednostavnom povijesti prethodnih analiza.

## Glavne mogućnosti

- odabir fotografije građevine putem gumba ili drag-and-drop funkcije
- analiza arhitektonskog stila pomoću lokalnog CLIP modela
- prikaz više mogućih stilova s postotkom pouzdanosti
- detaljan prikaz razdoblja, regija, materijala i značajki pojedinog stila
- povijest prethodnih analiza
- brisanje pojedinačnih stavki iz povijesti ili čišćenje cijele povijesti
- uvećani prikaz odabrane slike
- početni loading ekran tijekom učitavanja AI modela
- automatsko preuzimanje modela pri prvom pokretanju ako model nije lokalno dostupan

## Tehnologije

Aplikacija je izrađena u Pythonu i koristi:

- `tkinter` za grafičko korisničko sučelje
- `Pillow` za prikaz i pripremu slika
- `torch` za rad s AI modelom
- `transformers` za učitavanje CLIP modela
- `tkinterdnd2` i `windnd` za drag-and-drop podršku na Windowsu

## AI model

ARCHATIA koristi model `openai/clip-vit-base-patch32`. Model se sprema lokalno u folder `models/clip-vit-base-patch32`.

Model nije nužno potrebno ručno preuzimati. Ako ga aplikacija ne pronađe pri prvom pokretanju, pokušat će ga automatski preuzeti i spremiti lokalno. Nakon toga se model učitava s računala i ne mora se ponovno preuzimati.

Napomena: za prvo automatsko preuzimanje modela potrebna je internetska veza.

## Struktura projekta

```text
ARCHATIA_FRAN_MATAGIĆ/
  assets/              ikone i vizualni resursi aplikacije
  core/                logika analize, učitavanje modela i podaci o stilovima
  data/                lokalni podaci aplikacije, povijest i obrađene slike
  gui/                 grafičko sučelje aplikacije
  models/              lokalno spremljeni AI modeli
  utils/               pomoćne funkcije
  main.py              ulazna datoteka za pokretanje aplikacije
  requirements.txt     popis potrebnih Python biblioteka
```

## Instalacija

Preporučuje se korištenje virtualnog okruženja.

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Ako se Python na računalu pokreće naredbom `py`, može se koristiti:

```powershell
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Pokretanje

Aplikacija se pokreće iz glavnog foldera projekta:

```powershell
python main.py
```

ili:

```powershell
py main.py
```

## Korištenje aplikacije

1. Pokrenuti aplikaciju.
2. Odabrati fotografiju građevine pomoću gumba `Odaberi sliku` ili povući sliku na radnu površinu aplikacije.
3. Pokrenuti analizu pritiskom na `Analiziraj stil`.
4. Pregledati rezultate analize i moguće stilove.
5. Klikom na rezultat moguće je otvoriti detalje o stilu.
6. Prethodne analize dostupne su u panelu `Povijest analiza`.
7. Za novu analizu potrebno je pritisnuti `Nova analiza`.

## Podržani formati slika

Aplikacija podržava najčešće formate slika:

- JPG / JPEG
- PNG
- BMP
- WEBP

## Napomena o točnosti

Rezultat analize predstavlja procjenu AI modela, a ne konačnu stručnu potvrdu arhitektonskog stila. Točnost ovisi o kvaliteti fotografije, kutu snimanja, vidljivosti fasade i sličnosti između pojedinih stilova.

Za stabilnije rezultate aplikacija koristi više tekstualnih opisa po arhitektonskom stilu te ih uspoređuje sa slikom. Time se smanjuje mogućnost zamjene sličnih stilova, primjerice secesije i paladijanizma, gotike i neogotike ili modernizma i internacionalnog stila.

## Autor

Fran Matagić

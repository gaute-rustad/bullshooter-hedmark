# 🎯 Hedmark C E-Dart Hub

En moderne, mobilvennlig oversikt for **Hedmark C E-dartliga**, med automatisk oppdatering fra [Bullshooter.no](https://bullshooter.no/index.php/liga/ligaspill-hedmark/hedmark-c), push-varsler via **ntfy** og ferdig sammendrag for Messenger/Spond.

---

## 🌟 Funksjoner

- 🏆 **Ligatabell & Terminliste**: Full tabell med form, målforskjell (legs) og poeng, samt rundevelger for å se resultater, spillesteder og utsatte kamper.
- ⚡ **Siste runde (Runde 12)**: Ukens klatrere i 501 og Cricket, ukens beste runder og rundens kampresultater.
- 🎯 **Totalsnitt**:
  - Velg mellom **501 (PPR)** og **Cricket (MPR)**.
  - Søk etter spillere.
  - Filtrer etter lag.
  - Sortering på High Out, 180s, Hats og Tons.
- 👥 **Mitt Lag (f.eks. Darty Nellie)**:
  - Egen lagfane som husker favorittlaget ditt (kan byttes til hvilket som helst lag).
  - Viser lagets plassering, poeng, spillerstall og alle sesongens kamper med seier/tap-status.
- 📋 **Ett-klikks kopiering for Messenger / Spond**:
  - Ferdigformatert ukentlig kamprapport klar til å deles med laget.
- 🔔 **Push-varsel på mobilen via ntfy**:
  - Få varsel på telefonen i samme sekund som ukens runde publiseres på nett!

---

## 🚀 Komme i gang

### Teste lokalt på din PC
Åpne ganske enkelt `index.html` direkte i en nettleser. Datafilen `data.js` er forhåndslastet med data fra runde 12, så den fungerer umiddelbart uten behov for lokal webserver!

For å kjøre skraperen manuelt lokalt:
```bash
pip install -r requirements.txt
python scraper.py
```

---

## 🌐 Publisere på GitHub Pages (med automatisk oppdatering)

### 1. Opprett et GitHub-repository
I denne mappen (`hedmark-c-dart`):
```bash
git init
git add .
git commit -m "Første versjon av Hedmark C Hub"
git branch -M main
git remote add origin https://github.com/<ditt-brukernavn>/<ditt-repo-navn>.git
git push -u origin main
```

### 2. Aktiver GitHub Pages
1. Gå til repositoriet ditt på GitHub.
2. Klikk **Settings** ➔ **Pages**.
3. Under **Build and deployment** / **Source**: Velg **Deploy from a branch**.
4. Velg **Branch**: `main` og mappe `/ (root)`.
5. Klikk **Save**. Nettsiden din er nå live etter ca. 1 minutt!

### 3. Aktiver ntfy-varsel på mobilen
1. Last ned gratis-appen **ntfy** på mobilen din (iOS eller Android), eller åpne [ntfy.sh](https://ntfy.sh) i nettleseren.
2. Velg et unikt topic-navn (f.eks. `hedmark-c-dart-varsel-987`).
3. Abonner på topicet i appen.
4. I GitHub-repoet ditt, gå til **Settings** ➔ **Secrets and variables** ➔ **Actions**.
5. Legg til to hemmeligheter (**Repository secrets**):
   - `NTFY_TOPIC`: Ditt valgte topic-navn (f.eks. `hedmark-c-dart-varsel-987`)
   - `GH_PAGES_URL`: URL-en til din GitHub Pages-side (f.eks. `https://dittbrukernavn.github.io/hedmark-c-dart/`)

Når GitHub Actions kjører (automatisk hver onsdag kveld og torsdag morgen, eller når du trykker "Run workflow"), sjekker den om det er kommet ny runde. Er det nye resultater, pushes de til nettsiden din, og du får øyeblikkelig et push-varsel på telefonen!

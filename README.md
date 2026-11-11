# ETERNITYEON-
LAST EON is an open-source, modular immersive digital framework and interactive art installation. * Technology # ETERNITYEON-

### LAST EON · Generative Immersive Digital Experience

**Wildland Revolution**  
by **Ivan Nicola Lojodice**

> **Free Knowledge · One Race · One Face**  
> *Qui giace il Tempo. Qui comincia Noi.*

ETERNITYEON- è la repository del progetto **LAST EON**, una ricerca artistica e tecnologica sulle relazioni tra dati, ambiente, percezione e trasformazione. Il progetto esplora come segnali e contenuti digitali possano diventare materiale per esperienze visive, sonore e interattive.

## Visione

LAST EON considera il dato non solo come informazione, ma come materiale da osservare, interpretare e trasformare.

La ricerca si sviluppa attorno a tre concetti:

- **Segnale** — ciò che viene rilevato o ricevuto.
- **Relazione** — i legami tra ambiente, persone e sistemi digitali.
- **Trasformazione** — il passaggio dal dato a una forma visiva, sonora o narrativa.

Il progetto è in evoluzione e unisce sperimentazione artistica, sviluppo digitale e ricerca.

## Stack tecnologico

Il progetto può includere:

- **TouchDesigner** per la rete visuale interattiva.
- **Arduino** per acquisire dati da sensori analogici.
- **Python** per leggere la seriale e inoltrare i dati.
- **OSC** per trasmettere i valori a TouchDesigner.
- **GLSL** per eventuali shader personalizzati.

## Flusso dati Arduino–TouchDesigner

Il flusso previsto per l’input da Arduino è:

```text
Sensori → Arduino → USB/seriale → bridge Python → OSC → TouchDesigner Generative Immersive Digital Experience
**Wildland Revolution**  
by **Ivan Nicola Lojodice**

> **Free Knowledge · One Race · One Face**  
> *Qui giace il Tempo. Qui comincia Noi.*

ETERNITYEON- è la repository del progetto **LAST EON**, una ricerca artistica e tecnologica sulle relazioni tra dati, ambiente, percezione e trasformazione. Il progetto esplora come segnali e contenuti digitali possano diventare esperienze visive, sonore e immersive.

## Visione

LAST EON considera il dato non solo come informazione, ma come materiale da osservare, interpretare e trasformare.

La ricerca si sviluppa attorno a tre concetti:

- **Segnale** — ciò che viene rilevato o ricevuto.
- **Relazione** — i legami tra ambiente, persone e sistemi digitali.
- **Trasformazione** — il passaggio dal dato a una forma visiva, sonora o narrativa.

Il progetto è in evoluzione e unisce sperimentazione artistica, sviluppo digitale e ricerca.

## Il ruolo di `project.json`

Il file `project.json` contiene i testi e i dati utilizzati dalla pagina. Il file `index.html` è progettato per caricarli tramite JavaScript, usando `fetch()`.

Perché il caricamento funzioni, entrambi i file devono trovarsi nella cartella principale della repository e avere questi nomi esatti:

```text
ETERNITYEON-/
├── README.md
├── index.html
└── project.json
```


## Documentazione ed esempi

- [Ottimizzazione memoria e integrazione WebSocket](docs/OTTIMIZZAZIONE_MEMORIA_WEBSOCKET.md)
- [Esempio DataCore](examples/datacore_memory_aware.py)
- [Client WebSocket](examples/websocket_client.py)





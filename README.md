# ETERNITYEON-

### LAST EON · Generative Immersive Digital Experience

**Wildland Revolution**  
by **Ivan Nicola Lojodice**

> **Free Knowledge · One Race · One Face**  
> *Qui giace il Tempo. Qui comincia Noi.*

ETERNITYEON- è la repository di **LAST EON**, un progetto artistico e tecnologico che esplora la trasformazione di segnali e dati in esperienze visive, sonore e interattive.

## Project status

**Stato: prototipo in evoluzione.**

La repository contiene una pagina web, documentazione, esempi Python e un percorso prototipale per inviare dati da Arduino a TouchDesigner tramite seriale, Python e OSC.

Il bridge e lo sketch Arduino richiedono test con la scheda, i sensori e la versione di TouchDesigner effettivamente utilizzati. La presenza dei file non significa che l’intera installazione sia stata collaudata.

Lo script `scripts/create_eternityeon_network.py` è sperimentale. Revisiona il codice e fai una copia del progetto TouchDesigner prima di eseguirlo: può eliminare una rete `ETERNITYEON` già esistente.

Il client WebSocket è un esempio separato dal percorso Arduino/OSC. Non costituisce da solo un trading bot né un collegamento a un exchange.

## Architettura Arduino–TouchDesigner

```text
Sensori → Arduino → USB/seriale → bridge Python → OSC/UDP → TouchDesigner
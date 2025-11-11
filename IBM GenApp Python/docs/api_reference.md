# API Reference (Kurz)

Basis-URL (lokal): `http://127.0.0.1:8000`
- Authentifizierung: keine
- Content-Type: `application/json`

## Kunden
- Liste (Filter + Paging, Standardlimit 100)
```
curl "http://127.0.0.1:8000/api/customers?name=ann&postcode=10&limit=20&offset=0"
```
- Anlegen
```
curl -X POST http://127.0.0.1:8000/api/customers \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"ANN","last_name":"SMITH","date_of_birth":"1975-01-31","postcode":"W1A4WW"}'
```
- Detail
```
curl http://127.0.0.1:8000/api/customers/1
```
- Aktualisieren
```
curl -X PUT http://127.0.0.1:8000/api/customers/1 \
  -H 'Content-Type: application/json' \
  -d '{"postcode":"E15WW"}'
```
- Security lesen/rotieren (`?rotate=true` generiert neues Passwort)
```
curl "http://127.0.0.1:8000/api/customers/1/security"
curl "http://127.0.0.1:8000/api/customers/1/security?rotate=true"
```
- Security setzen (Teil-Updates via JSON möglich)
```
curl -X PUT http://127.0.0.1:8000/api/customers/1/security \
  -H 'Content-Type: application/json' \
  -d '{"customer_pass":"abcd1234","state_indicator":"N"}'
```

## Policen (generisch)
- Liste (Filter + Paging, inkl. `postcode`-Filter für Commercial)
```
curl "http://127.0.0.1:8000/api/policies?policy_type=M&customer_id=1&active_only=true&postcode=SO2&limit=20&offset=0"
```
- Liste (detailliert, liefert Basis- und Detaildaten, Paging via `page`)
```
curl "http://127.0.0.1:8000/api/policies/detailed?page=1&limit=20"
```
- Anlegen (optional `details`, Policy-Nummer wird generiert, falls nicht gesetzt)
```
curl -X POST http://127.0.0.1:8000/api/policies \
  -H 'Content-Type: application/json' \
  -d '{"policy_type":"M","customer_id":1,"issue_date":"2025-01-01","details":{"make":"DENNIS","reg_number":"A567WWR"}}'
```
- Update Basisfelder
```
curl -X PUT http://127.0.0.1:8000/api/policies/1 \
  -H 'Content-Type: application/json' \
  -d '{"payment":500,"commission":25}'
```
Hinweis: Löschen aktuell nur via UI (`POST /policies/{id}/delete`).

## Policen (typspezifisch)
- Motor anlegen (Pflicht: `customer_id`,`make`,`model`,`reg_number`)
```
curl -X POST http://127.0.0.1:8000/api/policies/motor \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"make":"VW","model":"BEETLE","reg_number":"A567WWR","premium":700}'
```
- Motor aktualisieren
```
curl -X PUT "http://127.0.0.1:8000/api/policies/motor/1?premium=700&accidents=1"
```
- House anlegen (Pflicht: `customer_id`,`property_type`,`bedrooms`,`value`,`postcode`)
```
curl -X POST http://127.0.0.1:8000/api/policies/house \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"property_type":"HOUSE","bedrooms":3,"value":150000,"postcode":"SO211UP"}'
```
- House aktualisieren
```
curl -X PUT "http://127.0.0.1:8000/api/policies/house/1?bedrooms=4&value=175000"
```
- Endowment anlegen (Pflicht: `customer_id`,`fund_name`,`term`,`sum_assured`)
```
curl -X POST http://127.0.0.1:8000/api/policies/endowment \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"fund_name":"SHEPPA","term":25,"sum_assured":100000}'
```
- Endowment aktualisieren
```
curl -X PUT "http://127.0.0.1:8000/api/policies/endowment/1?term=30&sum_assured=120000"
```
- Commercial anlegen (Pflicht: `customer_id`,`address`,`postcode`)
```
curl -X POST http://127.0.0.1:8000/api/policies/commercial \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"address":"5 MAIN ST","postcode":"SO212JN"}'
```
- Commercial aktualisieren
```
curl -X PUT "http://127.0.0.1:8000/api/policies/commercial/1?fire_peril=50&fire_premium=400"
```
Antwort der Typ-spezifischen `PUT`-Routen: `{"ok": true}` bei Erfolg.

## Schäden (Claims)
- Liste (optional `policy_id`, Paging via `page`/`limit`)
```
curl "http://127.0.0.1:8000/api/claims?policy_id=1&page=1&limit=20"
```
- Detail
```
curl http://127.0.0.1:8000/api/claims/1
```
- Anlegen
```
curl -X POST http://127.0.0.1:8000/api/claims \
  -H 'Content-Type: application/json' \
  -d '{"policy_id":1,"number":10,"date":"2025-02-01","value":5000,"cause":"FIRE"}'
```
- Aktualisieren
```
curl -X PUT http://127.0.0.1:8000/api/claims/1 \
  -H 'Content-Type: application/json' \
  -d '{"paid":1000,"observations":"Teilregulierung abgeschlossen"}'
```
Hinweis: Löschen ist nur über das UI möglich (`POST /claims/{id}/delete`).

## Events / Audit-Log
- Liste (Filter nach Quelle/Level + Paging)
```
curl "http://127.0.0.1:8000/api/events?source=policies&level=INFO&limit=50&offset=0"
```

## Statuscodes
- 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 422 Validation Error

## Using the flask shell

Example for using the flask shell to update the DB (convert invalid dates to XSD dateTime)
```
~/git/ltpoe_api$ FLASK_APP=ltpapi FLASK_ENV=development pipenv run flask shell
>>>
from ltpapi.store import get_connection 
from pprint import pprint
from rdflib import XSD, Literal
import time
from datetime import datetime
conn = get_connection(app) 
ns = conn.namespace

p=ns['created']
triples=list(conn._graph[:ns['created']:])
for (s,o) in triples:
    if type(o) == Literal and o.datatype != XSD.dateTime:
        if len(str(o.value)) == 19:
            t=datetime.fromtimestamp(o.value / 1000000000.0).isoformat(' ')
            newTriple=(s, p, Literal(t, datatype=XSD.dateTime))
            conn._graph.set(newTriple)
            print('Updating len 19: ', newTriple)
        elif len(o) == 10:
            t=datetime.fromtimestamp(int(o)).isoformat(' ')
            newTriple=(s, p, Literal(t, datatype=XSD.dateTime))
            conn._graph.set(newTriple)
            print('Updating len 10: ', newTriple)
        else:
            print("Invalid: ", o, len(o))

conn._graph.commit()

```


Acquire:
- JPEG
- MP3
- Doc
- HTML
- Text


Extract metadata


- Observation
    - Required:
        - date
        - software agent
    - blob
    - metadata


# Starting from new photo of manhattan bridge
# observation
```
{   date: 2019-05-24,
    agent: time-stitch/0.1,
    items:
        [
            {
                type: Landmark,
                name: "Manhattan Bridge",
                properties: {
                    sameAs: wd:Q125050
                }
            }, {
                type: Photo,
                name: 20190524_0100.jpg,
                properties: {
                    url: http://s3.amazonaws.com/ltp.shawnlower.net/b/20190524_0100.jpg,
                    capture_timestamp: "2019-05-24 20:51 EDT"
                }
            }
        ]
```
Serialized to RDF as:

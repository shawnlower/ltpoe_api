New Type / Ontology Mapping

First step is to enter the name of the new type. This should be mapped against a list of other public ontologies, such as:

- WordNet
- Wikidata
- Schema.org

A result would contain:
    Query:
        { 'phrase': 'webpage' }

    Response:
        [
            { 'ontology': 'wn', 'term': 'http://wordnet-rdf.princeton.edu/id/06370307-n', 'attrs' [ ... ] },
            { 'ontology': 'wn', 'term': 'http://wordnet-rdf.princeton.edu/id/06370307-n' },
        ]

Wordnet:
    http://localhost:8888/notebooks/wordnet.ipynb
    http://wordnetweb.princeton.edu/perl/webwn?o2=1&o0=1&o8=1&o1=1&o7=1&o5=1&o9=&o6=1&o3=1&o4=1&s=webpage
```
from nltk.corpus import wordnet
webpage = wordnet.synsets('webpage')[0]
names = webpage.lemma_names() # [str,]
description = webpage.definition() # str
```

# Mapping Types

owl:sameAs
rdfs:subClassOf

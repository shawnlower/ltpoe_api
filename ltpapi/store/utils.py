import string

def normalize_iri(iri: str):
    if iri.startswith('http:') or iri.startswith('https:'):
        return f'<{iri}>'
    else:
        return iri

def normalize_type_id(name: str):
    """
    Rules enforced for a normalized name:
    - Consists only of the letters a-z, plus a period.
    - Each word begins with a capital letter
    - Does not begin or end with a period
    """
    name = ''.join([word.title() for word in name.split()])
    name = ''.join([c for c in name if c in ['.'] + list(string.ascii_letters)])
    name=name.lstrip('.').rstrip('.')
    return name

def normalize_item_id(name: str):
    name = name.lower().replace(' ', '-')
    name = ''.join([c for c in name if c in ['.', '-'] + list(string.ascii_letters)])
    name=name.lstrip('.').rstrip('.')
    return name

def unprefix_config(config, prefix):
   """
   Convert PREFIX_KEY=VAL to key=val
   e.g.:
      [('STORE_ENDPOINT', 'http://localhost:3030/ltp'), ('STORE_TYPE', 'SparqlDatastore')]
         becomes
      {'endpoint': 'http://localhost:3030/ltp', 'type': 'SparqlDatastore'}
   """
   prefix = prefix.rstrip('_')
   return dict((k.split('_')[1].lower(), v) for (k,v) in config.items() if \
           k.startswith(f'{prefix}_'))


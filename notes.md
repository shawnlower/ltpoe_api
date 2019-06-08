Acquire:
- JPEG
- MP3
- Doc
- HTML
- Text


- Extract metadata


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
                name: Manhattan Bridge,
                properties: {
                    sameAs: wd:Q125050
                }
            }, {
                type: Photo,
                name: 20190524_0100.jpg,
                properties: {
                    url: http://s3.amazonaws.com/ltp.shawnlower.net/b/20190524_0100.jpg,
                    capture_timestamp: 2019-05-24 20:51 EDT
                }
            }
        ]
```
Serialized to RDF as:

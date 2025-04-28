# Flow Metrics

# Why are some Hip-Hop artists more successful than others?

## Some data sources we are looking into:

### 1. Artist Information and Popularity Metrics:

- Spotify API

### 2. Discography & Song Data:

- MusicBrainz API
- Spotify API

### 3. Lyrics for Vocabulary Analysis:

- Genius API

## Some Information we want to display:

### 1. Artist Profile:

- Basic Info
  - Name
  - Image
  - Years Active
- Career Metrics
  - Total Albums
  - Total EPs
  - Total Singles
  - Total Features
- Popularity Trends over Time

### 2. Vocabulary Analysis Metrics:

- Unique Word Count [UWC]
- Type-Token Ratio [TTR] (ratio of unique words to total words)
- Average Word Length [AVL]
- Lexical Density [LD] (ratio of content words to total words)
- Comparison to average hip-hope vocabulary baseline [VBL]

### 3. Correlation Analysis:

- Scatter plots showing relationship between vocabulary metrics and career metrics
- Word complexity vs. Commercial Success
- Vocabulary change over artists' career

## Technical Implementation Considerations

### 1. Data Collection Pipeline

1. Extract data from multiple APIs (Spotify, Chartmetric, MusicBrainz, Genius)
2. Process lyrics for vocabulary analysis
3. Store data in a Database (NoSQL Document Database)

### 2. Natural Language Processing (NLP) for Lyrics:

1. Clean lyrics by removing section headers, punctuation, etc.
2. Tokenize text into words
3. Filter out common words/stopwords for more meaningful analysis
4. Use stemmming/lemmatization to count word roots instead of variations

### 3. Key Metrics to Track

1. **Token-Type Ratio [TTR]:** The ratio of unique words to total words. Higher values indicate more diverse vocabulary.
2. **Unique Word Count [UWC]:** Total number of unique words in lyrics.
3. **Advance Metrics:**
  - Frequency of rare words (appearing in < 1% of hip-hop lyrics)
  - Average syllables per word (Complexity Measure)
  - Use of slang/vernacular vs. Standard English

## Challenges to Address

### 1. Data Completeness

Not all lyrics may be available through APIs and might require web scraping to acquire. In the event that web scraping is used for lyrics collection, we will attempt to pull from multiple sources and compile an average.

### 2. Legal Considerations

We will need to be careful how we store and display lyrics to avoid copyright infringment.

> Ideally, we shouldn't have any reason to display lyrics, but we should look into any implications of storing lyrics.

### 3. Attribution of Features

For songs with multiple artists, deciding whose vocabulary to attribute the lyrics to.

### 4. Genre Classification

Determining which artists are truly hip-hop/rap vs. adjacent genres. Unfortunately due to a lack of a formal evaluation method for this, we will be using the following priority:
1. More than 1 source lists artist/song as `hip-hop`, `rap`, or both.
2. At least 1 source lists artist/song as `hip-hop`, `rap`, or both.
3. Personal opinion from author. In this scenario, the artist or song will be noted as added by personal opinion for addition to genre, and grouping categories will include data with and without these artists.